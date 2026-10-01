import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import UserRegister, UserLogin, TokenResponse
from backend.app.schemas.user import UserResponse

logger = logging.getLogger("medical_assistant.api.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new clinician account.
    Validates email uniqueness and hashes password with bcrypt.
    """
    email_clean = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    user = User(
        name=payload.name.strip(),
        email=email_clean,
        password_hash=get_password_hash(payload.password),
        hospital_name=payload.hospital_name.strip(),
        role=payload.role.strip()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered successfully: id={user.id}, email={user.email}")
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a clinician and issues a signed JWT access token.
    """
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"Failed login attempt for: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email and password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    logger.info(f"User logged in: id={user.id}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the currently authenticated clinician profile.
    """
    return current_user
