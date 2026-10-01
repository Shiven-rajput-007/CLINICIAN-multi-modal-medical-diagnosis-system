from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ================= AUTH SCHEMAS =================
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Clinician's full name")
    email: EmailStr = Field(..., description="Valid work email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    hospital_name: str = Field(..., min_length=2, max_length=200, description="Hospital or Institution name")
    role: str = Field(default="Clinician", min_length=2, max_length=100, description="Medical role or specialty")

class UserLogin(BaseModel):
    email: Optional[str] = Field(None, description="Clinician's email address")
    username: Optional[str] = Field(None, description="Clinician's username or email")
    password: str = Field(..., description="Clinician's password")

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    hospital_name: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ================= DIAGNOSIS SCHEMAS =================
class PredictionDetail(BaseModel):
    prediction_class: str = Field(..., serialization_alias="class")
    confidence: float
    probabilities: Dict[str, float]

    model_config = ConfigDict(populate_by_name=True)

class DiagnosisResponse(BaseModel):
    modality: str
    image_prediction: PredictionDetail
    fusion_prediction: PredictionDetail
    gradcam_image: str  # Base64 data URI
    image_filename: str
    symptoms: Dict[str, bool]

# ================= HISTORY SCHEMAS =================
class DiagnosisHistoryCreate(BaseModel):
    modality: str
    image_filename: str
    image_prediction: str
    image_confidence: float
    fusion_prediction: str
    fusion_confidence: float
    symptoms: Dict[str, Any]
    class_probabilities: Dict[str, float]

class DiagnosisHistoryResponse(BaseModel):
    id: int
    user_id: int
    modality: str
    image_filename: str
    image_prediction: str
    image_confidence: float
    fusion_prediction: str
    fusion_confidence: float
    symptoms: Dict[str, Any]
    class_probabilities: Dict[str, float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthStatusResponse(BaseModel):
    status: str
    app_name: str
    models_ready: bool
    device: str
    modalities: Dict[str, Any]
