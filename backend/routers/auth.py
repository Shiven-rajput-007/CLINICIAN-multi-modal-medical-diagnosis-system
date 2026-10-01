from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from backend.auth import get_password_hash, verify_password, create_access_token
from backend.dependencies import get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A clinician with this email address is already registered."
        )

    # Hash password using bcrypt
    hashed_pwd = get_password_hash(payload.password)

    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hashed_pwd,
        hospital_name=payload.hospital_name.strip(),
        role=payload.role.strip()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    access_token = create_access_token(data={"sub": new_user.email, "id": new_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Authenticates a clinician using email/username and password.
    Supports both JSON payloads (frontend / API) and Form-urlencoded data (Swagger UI OAuth2 Authorize).
    """
    content_type = request.headers.get("content-type", "")
    identifier = None
    password = None

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        identifier = form.get("username") or form.get("email")
        password = form.get("password")
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                identifier = body.get("email") or body.get("username")
                password = body.get("password")
        except Exception:
            try:
                form = await request.form()
                identifier = form.get("username") or form.get("email")
                password = form.get("password")
            except Exception:
                pass

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both email/username and password are required."
        )

    identifier_str = str(identifier).strip()
    # Match email (case-insensitive) or clinician name
    user = db.query(User).filter(
        (User.email == identifier_str.lower()) | (User.name.ilike(identifier_str))
    ).first()

    if not user or not verify_password(str(password), user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password. Please verify your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/token", response_model=TokenResponse, include_in_schema=True)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Standard OAuth2 token endpoint for Swagger UI and OAuth2 clients."""
    identifier_str = form_data.username.strip()
    user = db.query(User).filter(
        (User.email == identifier_str.lower()) | (User.name.ilike(identifier_str))
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
