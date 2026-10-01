import sys
from pathlib import Path

# Ensure backend directory and project root are discoverable in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent      # backend/app
_BACKEND_DIR = _CURRENT_DIR.parent                  # backend
_PROJECT_ROOT = _BACKEND_DIR.parent                 # root

for _p in [str(_BACKEND_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.file_service import FileService
from app.ml.model_loader import get_model_manager
from app.api import (
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

if __name__ == "__main__":
    import uvicorn
    host = settings.server_host
    port = settings.server_port
    logger.info(f"Starting server on {host}:{port}...")
    uvicorn.run("app.main:app", host=host, port=port, reload=settings.DEBUG)
