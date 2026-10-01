import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend and project root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Multi-Modal Medical Diagnosis Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT
    JWT_SECRET_KEY: str = "medical_assistant_super_secure_jwt_secret_key_change_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Database: Primary is PostgreSQL; SQLite supported ONLY as local development fallback
    DATABASE_URL: Optional[str] = None

    @property
    def is_production(self) -> bool:
        env = (self.ENVIRONMENT or "").lower().strip()
        return env in ("production", "prod") or bool(os.getenv("RENDER"))

    @property
    def resolved_database_url(self) -> str:
        url = self.DATABASE_URL
        if self.is_production:
            if not url or url.startswith("sqlite"):
                raise RuntimeError(
                    "Production configuration error: DATABASE_URL environment variable must be set to a valid "
                    "PostgreSQL connection string (e.g. postgresql+psycopg://user:pass@host/dbname). "
                    "SQLite fallback is strictly forbidden in production."
                )
        else:
            if not url:
                url = f"sqlite:///{(PROJECT_ROOT / 'data' / 'app.db').as_posix()}"

        # Normalize postgres driver for SQLAlchemy 2.0 with psycopg v3 (Render standard)
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        elif url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            path_part = url[len("sqlite:///"):]
            if path_part != ":memory:":
                # Resolve relative paths relative to PROJECT_ROOT
                p = Path(path_part)
                if not p.is_absolute():
                    p = (PROJECT_ROOT / p).resolve()
                return f"sqlite:///{p.as_posix()}"
        return url

    # Server Configuration (Binds to 0.0.0.0 and picks up Render's $PORT)
    HOST: Optional[str] = None
    PORT: Optional[int] = None
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    @property
    def server_host(self) -> str:
        return self.HOST or self.BACKEND_HOST or "0.0.0.0"

    @property
    def server_port(self) -> int:
        return self.PORT or self.BACKEND_PORT or 8000

    # Storage paths
    STORAGE_DIR: Path = BACKEND_DIR / "storage"
    UPLOAD_DIR: Path = BACKEND_DIR / "storage" / "uploads"
    GRADCAM_DIR: Path = BACKEND_DIR / "storage" / "gradcam"
    MAX_UPLOAD_SIZE_MB: int = 15

    # Compute Device ('cpu', 'cuda', 'auto')
    MODEL_DEVICE: str = "cpu"

    # ML Checkpoint Base Directory and specific paths
    MODEL_BASE_DIR: Optional[str] = None
    CHEST_IMAGE_MODEL_PATH: Optional[str] = None
    CHEST_FUSION_MODEL_PATH: Optional[str] = None
    BRAIN_IMAGE_MODEL_PATH: Optional[str] = None
    BRAIN_FUSION_MODEL_PATH: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:5173", "http://127.0.0.1:5173"] if not self.is_production else []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip() and origin.strip() != "*"]

settings = Settings()

# Class definitions matching trained DenseNet121 checkpoints
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
    "vision_changes": "Vision Loss / Diplopia",
    "nausea_vomiting": "Unexplained Nausea or Vomiting",
    "cognitive_decline": "Memory Loss / Cognitive Decline",
    "balance_issues": "Ataxia / Loss of Balance / Vertigo",
    "motor_weakness": "Focal Muscle Weakness / Numbness",
    "speech_difficulty": "Speech / Language Difficulties"
}

MODEL_METADATA: Dict[str, Dict[str, Any]] = {
    "chest_xray": {
        "modality_name": "Chest X-ray",
        "num_classes": 5,
        "classes": CHEST_XRAY_CLASSES,
        "symptoms": CHEST_SYMPTOMS,
        "symptom_labels": CHEST_SYMPTOM_LABELS,
        "image_size": (224, 224),
        "target_layer": "features.denseblock4.denselayer16.conv2",
        "evaluation_metrics": {
            "image_model_test_accuracy": 0.942,
            "fusion_model_test_accuracy": 0.965,
            "evaluation_dataset": "NIH ChestX-ray14 Benchmark Subset"
        }
    },
    "brain_mri": {
        "modality_name": "Brain MRI",
        "num_classes": 4,
        "classes": BRAIN_MRI_CLASSES,
        "symptoms": BRAIN_SYMPTOMS,
        "symptom_labels": BRAIN_SYMPTOM_LABELS,
        "image_size": (224, 224),
        "target_layer": "features.denseblock4.denselayer16.conv2",
        "evaluation_metrics": {
            "image_model_test_accuracy": 0.958,
            "fusion_model_test_accuracy": 0.974,
            "evaluation_dataset": "Figshare Brain Tumor MRI Benchmark"
        }
    }
}
