from pydantic import BaseModel, EmailStr, Field
from backend.app.schemas.user import UserResponse

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Full name of clinician")
    email: EmailStr = Field(..., description="Valid work/hospital email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    role: str = Field(default="doctor", description="Role: doctor or hospital_staff")
    hospital_name: str = Field(default="University Medical Center", min_length=2, max_length=200)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Clinician email address")
    password: str = Field(..., min_length=1, description="Account password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
