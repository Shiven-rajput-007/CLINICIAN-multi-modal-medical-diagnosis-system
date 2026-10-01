import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.config import MODEL_METADATA, settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.diagnosis import (
    DiagnosisInferResponse,
    DiagnosisRecordResponse,
    PaginatedHistoryResponse,
    DashboardStatsResponse
)
from app.services.diagnosis_service import DiagnosisService

logger = logging.getLogger("medical_assistant.api.diagnosis")
router = APIRouter(prefix="/diagnosis", tags=["Diagnosis & Multimodal Inference"])

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.get("/metadata")
def get_clinical_metadata():
    """
    Returns available clinical imaging modalities, symptom checklists, and labels.
    """
    return MODEL_METADATA

@router.post("/infer", response_model=DiagnosisInferResponse, status_code=status.HTTP_201_CREATED)
async def infer_diagnosis(
    file: UploadFile = File(..., description="Medical imaging scan file (.png, .jpg, .jpeg)"),
    modality: str = Form(..., description="Target modality: 'chest_xray' or 'brain_mri'"),
    symptoms: str = Form("{}", description="JSON string mapping symptom keys to boolean flags"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Runs end-to-end multimodal diagnosis:
    - Validates file format and size
    - Preprocesses image
    - Runs PyTorch DenseNet-121 image model
    - Runs PyTorch Late-Fusion model with symptom vector
    - Generates Grad-CAM visual heatmap overlay
    - Persists audit record in database strictly isolated to current user
    - Returns structured predictions and visualizations
    """
    filename = file.filename or "scan.png"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PNG, JPG, and JPEG medical scans are accepted."
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty."
        )

    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"The uploaded scan exceeds the maximum allowable size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if modality not in MODEL_METADATA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid modality '{modality}'. Supported modalities: {list(MODEL_METADATA.keys())}"
        )

    try:
        symptoms_dict = json.loads(symptoms) if isinstance(symptoms, str) else symptoms
        if not isinstance(symptoms_dict, dict):
            symptoms_dict = {}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid symptoms JSON: {str(e)}"
        )

    try:
        result = DiagnosisService.process_and_save_diagnosis(
            image_bytes=image_bytes,
            original_filename=filename,
            modality=modality,
            symptoms_dict=symptoms_dict,
            user_id=current_user.id,
            db=db
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Inference failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Medical diagnosis inference failed: {str(e)}"
        )

# Also expose /diagnose as an alias to /infer for convenience
@router.post("/diagnose", response_model=DiagnosisInferResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def diagnose_alias(
    file: UploadFile = File(...),
    modality: str = Form(...),
    symptoms: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await infer_diagnosis(file=file, modality=modality, symptoms=symptoms, db=db, current_user=current_user)

@router.get("/history", response_model=PaginatedHistoryResponse)
def get_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page"),
    modality: Optional[str] = Query(None, description="Optional modality filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves paginated diagnosis history strictly isolated to the authenticated user.
    """
    return DiagnosisService.get_user_history(
        user_id=current_user.id,
        db=db,
        page=page,
        page_size=page_size,
        modality=modality
    )

@router.get("/history/{diagnosis_id}", response_model=DiagnosisRecordResponse)
def get_diagnosis_record(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single diagnosis record strictly verifying user ownership.
    """
    return DiagnosisService.get_record_by_id(
        record_id=diagnosis_id,
        user_id=current_user.id,
        db=db
    )

@router.delete("/history/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagnosis_record(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific diagnosis record and its physical files after verifying ownership.
    """
    DiagnosisService.delete_diagnosis_record(
        record_id=diagnosis_id,
        user_id=current_user.id,
        db=db
    )
    return None

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns real statistics computed strictly from the authenticated user's records.
    Returns genuine zeros for fresh accounts.
    """
    return DiagnosisService.get_user_dashboard_stats(
        user_id=current_user.id,
        db=db
    )
