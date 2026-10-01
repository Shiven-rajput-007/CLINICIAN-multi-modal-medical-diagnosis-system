import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import init_db
from backend.ml.loader import get_model_manager
from backend.routers import auth, diagnosis

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medical_assistant.app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and pre-load PyTorch models
    logger.info("Initializing SQLite database tables...")
    init_db()
    logger.info("Database initialized successfully.")

    logger.info("Pre-warming PyTorch diagnostic models into resident memory...")
    try:
        manager = get_model_manager()
        logger.info(f"Models ready on device: {manager.device}")
    except Exception as e:
        logger.error(f"Error during model pre-warming: {e}", exc_info=True)

    yield

    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready clinical decision-support API utilizing DenseNet-121 computer vision, "
        "multimodal late-fusion neural networks, and Grad-CAM attention maps for chest X-ray and brain MRI analysis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],  # Permits Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
# Direct endpoints matching specifications
app.include_router(auth.router)
# Also include with /auth prefix for API convention compatibility
app.include_router(auth.router, prefix="/auth")
# Diagnosis endpoints
app.include_router(diagnosis.router)

@app.get("/", tags=["General"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "operational",
        "disclaimer": (
            "This application is an educational and clinical decision-support prototype. "
            "All findings must be independently verified by a qualified medical professional."
        )
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system administration."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
