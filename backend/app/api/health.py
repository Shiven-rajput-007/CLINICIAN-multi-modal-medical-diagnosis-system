import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings, MODEL_METADATA
from app.db.session import get_db
from app.ml.model_loader import get_model_manager
from app.schemas.common import HealthResponse

logger = logging.getLogger("medical_assistant.api.health")
router = APIRouter(tags=["System Health"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Performs real live checks on database connectivity and PyTorch model readiness.
    """
    # Test DB
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Check models
    manager = get_model_manager()
    models_ready = manager.is_ready()

    return HealthResponse(
        status="ok" if (db_connected and models_ready) else "degraded",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        database_connected=db_connected,
        models_ready=models_ready,
        device=str(manager.device),
        modalities=MODEL_METADATA
    )
