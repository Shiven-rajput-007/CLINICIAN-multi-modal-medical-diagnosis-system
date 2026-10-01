import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Medical Diagnosis Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT
    JWT_SECRET_KEY: str = "medical_assistant_secure_production_secret_key_change_me_987654321"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Database
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"

    # Server Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000"

    # ML Model Checkpoint Paths (can be overridden via environment variables)
    CHEST_IMAGE_MODEL_PATH: Optional[str] = str(BASE_DIR / "backend" / "models_ml" / "chest_xray" / "densenet121_chest.pth")
    CHEST_FUSION_MODEL_PATH: Optional[str] = str(BASE_DIR / "backend" / "models_ml" / "chest_xray" / "fusion_chest.pth")
    BRAIN_IMAGE_MODEL_PATH: Optional[str] = str(BASE_DIR / "backend" / "models_ml" / "brain_mri" / "densenet121_brain.pth")
    BRAIN_FUSION_MODEL_PATH: Optional[str] = str(BASE_DIR / "backend" / "models_ml" / "brain_mri" / "fusion_brain.pth")

    # Compute Device ('auto', 'cuda', 'cpu')
    DEVICE: str = "auto"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Class definitions
CHEST_XRAY_CLASSES = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion"
]

BRAIN_MRI_CLASSES = [
    "Glioma",
    "Meningioma",
    "No Tumor",
    "Pituitary"
]

# Deterministic symptom feature vector order
CHEST_SYMPTOMS = [
    "cough",
    "fever",
    "dyspnea",
    "chest_pain",
    "fatigue",
    "hemoptysis",
    "wheezing",
    "tachypnea"
]

CHEST_SYMPTOM_LABELS = {
    "cough": "Persistent Cough",
    "fever": "Fever / Chills",
    "dyspnea": "Shortness of Breath (Dyspnea)",
    "chest_pain": "Pleuritic Chest Pain",
    "fatigue": "Severe Fatigue / Malaise",
    "hemoptysis": "Hemoptysis (Coughing Blood)",
    "wheezing": "Wheezing / Stridor",
    "tachypnea": "Rapid Shallow Breathing"
}

BRAIN_SYMPTOMS = [
    "headache",
    "seizures",
    "vision_changes",
    "nausea_vomiting",
    "cognitive_decline",
    "balance_issues",
    "motor_weakness",
    "speech_difficulty"
]

BRAIN_SYMPTOM_LABELS = {
    "headache": "Persistent Morning Headache",
    "seizures": "Seizures / Focal Convulsions",
    "vision_changes": "Vision Loss / Diplopia (Double Vision)",
    "nausea_vomiting": "Unexplained Nausea or Vomiting",
    "cognitive_decline": "Memory Loss / Cognitive Decline",
    "balance_issues": "Ataxia / Loss of Balance / Vertigo",
    "motor_weakness": "Focal Muscle Weakness / Numbness",
    "speech_difficulty": "Speech / Language Difficulties"
}

MODEL_METADATA = {
    "chest_xray": {
        "modality_name": "Chest X-ray",
        "num_classes": 5,
        "classes": CHEST_XRAY_CLASSES,
        "symptoms": CHEST_SYMPTOMS,
        "symptom_labels": CHEST_SYMPTOM_LABELS,
        "image_size": (224, 224),
        "target_layer": "features.denseblock4.denselayer16.conv2"
    },
    "brain_mri": {
        "modality_name": "Brain MRI",
        "num_classes": 4,
        "classes": BRAIN_MRI_CLASSES,
        "symptoms": BRAIN_SYMPTOMS,
        "symptom_labels": BRAIN_SYMPTOM_LABELS,
        "image_size": (224, 224),
        "target_layer": "features.denseblock4.denselayer16.conv2"
    }
}
