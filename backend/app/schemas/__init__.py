from app.schemas.auth import UserRegister, UserLogin, TokenResponse
from app.schemas.user import UserResponse, UserBase
from app.schemas.diagnosis import (
    PredictionDetail,
    DiagnosisInferResponse,
    DiagnosisRecordResponse,
    PaginatedHistoryResponse,
    DashboardStatsResponse,
    RecentDiagnosisSummary
)
from app.schemas.common import HealthResponse, MessageResponse, ErrorResponse

__all__ = [
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    "UserBase",
    "PredictionDetail",
    "DiagnosisInferResponse",
    "DiagnosisRecordResponse",
    "PaginatedHistoryResponse",
    "DashboardStatsResponse",
    "RecentDiagnosisSummary",
    "HealthResponse",
    "MessageResponse",
    "ErrorResponse"
]
