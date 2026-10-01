import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, DiagnosisHistory
from backend.schemas import (
    DiagnosisResponse,
    DiagnosisHistoryCreate,
    DiagnosisHistoryResponse,
    HealthStatusResponse
)
from backend.dependencies import get_current_user
from backend.config import MODEL_METADATA, settings
from backend.ml.prediction import run_diagnosis
from backend.ml.loader import get_model_manager

logger = logging.getLogger("medical_assistant.api.diagnosis")

router = APIRouter(tags=["Diagnosis & Clinical History"])

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

@router.get("/health", response_model=HealthStatusResponse)
def health_check():
    manager = get_model_manager()
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "models_ready": manager.is_ready(),
        "device": str(manager.device),
        "modalities": MODEL_METADATA
    }

@router.get("/metadata")
def get_metadata():
    """Returns clinical modalities, supported classes, and symptom checklists."""
    return MODEL_METADATA

@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_image(
    file: UploadFile = File(..., description="Uploaded clinical scan (X-ray or MRI)"),
    modality: str = Form(..., description="Diagnostic modality ('chest_xray' or 'brain_mri')"),
    symptoms: str = Form("{}", description="JSON string mapping symptom keys to booleans"),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate file extension
    filename = file.filename or "uploaded_scan.png"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image file extension '{ext}'. Accepted formats: PNG, JPG, JPEG."
        )

    # 2. Read image content and check size
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty. Please provide a valid scan."
        )
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded image exceeds the 15MB file size limit."
        )

    # 3. Validate modality
    if modality not in MODEL_METADATA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid modality '{modality}'. Allowed: {list(MODEL_METADATA.keys())}"
        )

    # 4. Parse symptom flags
    try:
        symptoms_dict = json.loads(symptoms) if isinstance(symptoms, str) else symptoms
        if not isinstance(symptoms_dict, dict):
            symptoms_dict = {}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed symptom vector JSON: {str(e)}"
        )

    # 5. Run end-to-end inference and Grad-CAM
    try:
        result = run_diagnosis(
            image_bytes=image_bytes,
            modality=modality,
            symptoms_dict=symptoms_dict,
            image_filename=filename
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnostic analysis encountered an unexpected error: {str(e)}"
        )

@router.post("/diagnosis-history", response_model=DiagnosisHistoryResponse, status_code=status.HTTP_201_CREATED)
def save_diagnosis_history(
    payload: DiagnosisHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Persists a verified diagnosis record into the SQLite database.
    Strictly associates the record with the authenticated clinician.
    """
    record = DiagnosisHistory(
        user_id=current_user.id,
        modality=payload.modality,
        image_filename=payload.image_filename,
        image_prediction=payload.image_prediction,
        image_confidence=payload.image_confidence,
        fusion_prediction=payload.fusion_prediction,
        fusion_confidence=payload.fusion_confidence,
        symptoms=payload.symptoms,
        class_probabilities=payload.class_probabilities
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/diagnosis-history", response_model=List[DiagnosisHistoryResponse])
def get_user_diagnosis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    modality: Optional[str] = None
):
    """
    Retrieves the clinical audit history strictly isolated to the authenticated user.
    Records are returned chronologically (newest first).
    """
    query = db.query(DiagnosisHistory).filter(DiagnosisHistory.user_id == current_user.id)
    if modality:
        query = query.filter(DiagnosisHistory.modality == modality)

    records = query.order_by(DiagnosisHistory.created_at.desc()).all()
    return records
