import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.services.file_service import FileService
from backend.app.ml.model_loader import get_model_manager
from backend.app.api import (
    auth_router,
    diagnosis_router,
    files_router,
    health_router,
    users_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medical_assistant")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager:
    1. Prepares local secure file storage
    2. Pre-warms resident PyTorch DenseNet-121 and Late-Fusion models
    """
    logger.info("Initializing Multi-Modal Medical Diagnosis Assistant backend...")
    FileService.initialize_storage()

    try:
        manager = get_model_manager()
        logger.info(f"PyTorch diagnostic models successfully pre-warmed on device: {manager.device}")
    except Exception as e:
        logger.error(f"Error pre-loading PyTorch models: {e}", exc_info=True)

    yield

    logger.info("Shutting down Multi-Modal Medical Diagnosis Assistant backend.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade clinical decision support API using PyTorch DenseNet-121 and late-fusion multimodal neural networks with Grad-CAM visual explainability.",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Global exception handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."}
    )

# Register API routes under /api
app.include_router(auth_router, prefix="/api")
app.include_router(diagnosis_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(health_router, prefix="/api")

# Also register health check at root /health for docker/load balancer probes
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": "/api"
    }
