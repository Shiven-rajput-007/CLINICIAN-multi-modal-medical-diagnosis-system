import logging
import math
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.models.diagnosis import DiagnosisRecord
from backend.app.schemas.diagnosis import (
    DiagnosisInferResponse,
    DiagnosisRecordResponse,
    PaginatedHistoryResponse,
    DashboardStatsResponse,
    RecentDiagnosisSummary,
    PredictionDetail
)
from backend.app.services.file_service import FileService
from backend.app.ml.inference import run_diagnosis
from backend.app.core.config import MODEL_METADATA

logger = logging.getLogger("medical_assistant.services.diagnosis")

class DiagnosisService:
    @staticmethod
    def process_and_save_diagnosis(
        image_bytes: bytes,
        original_filename: str,
        modality: str,
        symptoms_dict: Dict[str, bool],
        user_id: int,
        db: Session
    ) -> DiagnosisInferResponse:
        """
        Runs ML inference + Grad-CAM, saves images to disk, and records diagnosis in DB.
        """
        # 1. Execute ML pipeline
        ml_res = run_diagnosis(
            image_bytes=image_bytes,
            modality=modality,
            symptoms_dict=symptoms_dict,
            image_filename=original_filename
        )

        # 2. Persist image and Grad-CAM overlay to disk
        upload_rel_path, _ = FileService.save_upload_image(image_bytes, original_filename)
        gradcam_rel_path, _ = FileService.save_gradcam_image(ml_res["gradcam_pil"])

        # 3. Create persistent database record strictly associated with user
        record = DiagnosisRecord(
            user_id=user_id,
            modality=modality,
            original_filename=original_filename,
            image_path=upload_rel_path,
            predicted_class=ml_res["predicted_class"],
            confidence=ml_res["confidence"],
            class_probabilities=ml_res["class_probabilities"],
            symptom_data=symptoms_dict,
            gradcam_path=gradcam_rel_path,
            image_prediction=ml_res["image_prediction"]["prediction_class"],
            image_confidence=ml_res["image_prediction"]["confidence"],
            fusion_prediction=ml_res["fusion_prediction"]["prediction_class"],
            fusion_confidence=ml_res["fusion_prediction"]["confidence"],
            model_version="densenet121-multimodal-v1"
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # 4. Construct response
        image_url = f"/api/files/{upload_rel_path}"
        gradcam_url = f"/api/files/{gradcam_rel_path}"

        return DiagnosisInferResponse(
            id=record.id,
            user_id=record.user_id,
            modality=record.modality,
            original_filename=record.original_filename,
            predicted_class=record.predicted_class,
            confidence=record.confidence,
            class_probabilities=record.class_probabilities,
            image_prediction=PredictionDetail(
                prediction_class=ml_res["image_prediction"]["prediction_class"],
                confidence=ml_res["image_prediction"]["confidence"],
                probabilities=ml_res["image_prediction"]["probabilities"]
            ),
            fusion_prediction=PredictionDetail(
                prediction_class=ml_res["fusion_prediction"]["prediction_class"],
                confidence=ml_res["fusion_prediction"]["confidence"],
                probabilities=ml_res["fusion_prediction"]["probabilities"]
            ),
            image_url=image_url,
            gradcam_url=gradcam_url,
            gradcam_base64=ml_res["gradcam_base64"],
            symptom_data=record.symptom_data,
            model_version=record.model_version,
            created_at=record.created_at
        )

    @staticmethod
    def get_user_history(
        user_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        modality: Optional[str] = None
    ) -> PaginatedHistoryResponse:
        """
        Retrieves paginated diagnosis history strictly isolated to the authenticated user.
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        query = db.query(DiagnosisRecord).filter(DiagnosisRecord.user_id == user_id)
        if modality and modality.strip():
            query = query.filter(DiagnosisRecord.modality == modality.strip())

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 0

        offset = (page - 1) * page_size
        records = query.order_by(DiagnosisRecord.created_at.desc()).offset(offset).limit(page_size).all()

        record_responses = []
        for r in records:
            image_url = f"/api/files/{r.image_path}"
            gradcam_url = f"/api/files/{r.gradcam_path}"
            record_responses.append(
                DiagnosisRecordResponse(
                    id=r.id,
                    user_id=r.user_id,
                    modality=r.modality,
                    original_filename=r.original_filename,
                    predicted_class=r.predicted_class,
                    confidence=r.confidence,
                    class_probabilities=r.class_probabilities,
                    image_prediction=r.image_prediction,
                    image_confidence=r.image_confidence,
                    fusion_prediction=r.fusion_prediction,
                    fusion_confidence=r.fusion_confidence,
                    symptom_data=r.symptom_data,
                    image_url=image_url,
                    gradcam_url=gradcam_url,
                    model_version=r.model_version,
                    created_at=r.created_at
                )
            )

        return PaginatedHistoryResponse(
            records=record_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_record_by_id(record_id: int, user_id: int, db: Session) -> DiagnosisRecordResponse:
        """
        Retrieves a single record strictly verifying user ownership.
        """
        record = db.query(DiagnosisRecord).filter(
            DiagnosisRecord.id == record_id,
            DiagnosisRecord.user_id == user_id
        ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis record not found or access denied."
            )

        return DiagnosisRecordResponse(
            id=record.id,
            user_id=record.user_id,
            modality=record.modality,
            original_filename=record.original_filename,
            predicted_class=record.predicted_class,
            confidence=record.confidence,
            class_probabilities=record.class_probabilities,
            image_prediction=record.image_prediction,
            image_confidence=record.image_confidence,
            fusion_prediction=record.fusion_prediction,
            fusion_confidence=record.fusion_confidence,
            symptom_data=record.symptom_data,
            image_url=f"/api/files/{record.image_path}",
            gradcam_url=f"/api/files/{record.gradcam_path}",
            model_version=record.model_version,
            created_at=record.created_at
        )

    @staticmethod
    def delete_diagnosis_record(record_id: int, user_id: int, db: Session) -> None:
        """
        Deletes a diagnosis record after verifying ownership.
        """
        record = db.query(DiagnosisRecord).filter(
            DiagnosisRecord.id == record_id,
            DiagnosisRecord.user_id == user_id
        ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis record not found or access denied."
            )

        # Safely remove associated files from disk
        FileService.delete_file_safely(record.image_path)
        FileService.delete_file_safely(record.gradcam_path)

        db.delete(record)
        db.commit()

    @staticmethod
    def get_user_dashboard_stats(user_id: int, db: Session) -> DashboardStatsResponse:
        """
        Calculates all dashboard metrics strictly from the authenticated user's records.
        For a newly registered user with zero records, returns genuine zero statistics.
        """
        user_records = db.query(DiagnosisRecord).filter(DiagnosisRecord.user_id == user_id).all()
        total_diagnoses = len(user_records)

        if total_diagnoses == 0:
            return DashboardStatsResponse(
                total_diagnoses=0,
                chest_xray_count=0,
                brain_mri_count=0,
                average_confidence=0.0,
                most_recent_diagnosis=None,
                class_distribution={},
                modality_breakdown={"chest_xray": 0, "brain_mri": 0},
                model_evaluation_metrics={
                    "chest_xray": MODEL_METADATA["chest_xray"]["evaluation_metrics"],
                    "brain_mri": MODEL_METADATA["brain_mri"]["evaluation_metrics"],
                    "note": "These are benchmark model test evaluation metrics, not user-generated clinical statistics."
                }
            )

        chest_count = sum(1 for r in user_records if r.modality == "chest_xray")
        brain_count = sum(1 for r in user_records if r.modality == "brain_mri")
        avg_confidence = sum(r.confidence for r in user_records) / total_diagnoses

        # Most recent
        sorted_records = sorted(user_records, key=lambda r: r.created_at, reverse=True)
        recent = sorted_records[0]
        recent_summary = RecentDiagnosisSummary(
            id=recent.id,
            modality=recent.modality,
            predicted_class=recent.predicted_class,
            confidence=round(recent.confidence, 4),
            created_at=recent.created_at
        )

        # Class distribution
        class_dist: Dict[str, int] = {}
        for r in user_records:
            c = r.predicted_class
            class_dist[c] = class_dist.get(c, 0) + 1

        return DashboardStatsResponse(
            total_diagnoses=total_diagnoses,
            chest_xray_count=chest_count,
            brain_mri_count=brain_count,
            average_confidence=round(avg_confidence, 4),
            most_recent_diagnosis=recent_summary,
            class_distribution=class_dist,
            modality_breakdown={"chest_xray": chest_count, "brain_mri": brain_count},
            model_evaluation_metrics={
                "chest_xray": MODEL_METADATA["chest_xray"]["evaluation_metrics"],
                "brain_mri": MODEL_METADATA["brain_mri"]["evaluation_metrics"],
                "note": "These are benchmark model test evaluation metrics, not user-generated clinical statistics."
            }
        )
