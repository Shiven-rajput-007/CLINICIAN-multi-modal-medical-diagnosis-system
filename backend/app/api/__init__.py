from app.api.auth import router as auth_router
from app.api.diagnosis import router as diagnosis_router
from app.api.files import router as files_router
from app.api.health import router as health_router
from app.api.users import router as users_router

__all__ = ["auth_router", "diagnosis_router", "files_router", "health_router", "users_router"]
