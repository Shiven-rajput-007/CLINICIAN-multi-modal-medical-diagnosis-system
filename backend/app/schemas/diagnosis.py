from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class PredictionDetail(BaseModel):
    prediction_class: str
    confidence: float
    probabilities: Dict[str, float]

class DiagnosisInferResponse(BaseModel):
    id: int
    user_id: int
    modality: str
    original_filename: str
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    image_prediction: PredictionDetail
    fusion_prediction: PredictionDetail
    image_url: str
    gradcam_url: str
    gradcam_base64: str
    symptom_data: Dict[str, Any]
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DiagnosisRecordResponse(BaseModel):
    id: int
    user_id: int
    modality: str
    original_filename: str
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    image_prediction: Optional[str] = None
    image_confidence: Optional[float] = None
    fusion_prediction: Optional[str] = None
    fusion_confidence: Optional[float] = None
    symptom_data: Dict[str, Any]
    image_url: str
    gradcam_url: str
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedHistoryResponse(BaseModel):
    records: List[DiagnosisRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class RecentDiagnosisSummary(BaseModel):
    id: int
    modality: str
    predicted_class: str
    confidence: float
    created_at: datetime

class DashboardStatsResponse(BaseModel):
    total_diagnoses: int
    chest_xray_count: int
    brain_mri_count: int
    average_confidence: float
    most_recent_diagnosis: Optional[RecentDiagnosisSummary] = None
    class_distribution: Dict[str, int]
    modality_breakdown: Dict[str, int]
    model_evaluation_metrics: Dict[str, Any]
