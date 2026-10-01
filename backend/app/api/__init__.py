from backend.app.api.auth import router as auth_router
from backend.app.api.diagnosis import router as diagnosis_router
from backend.app.api.files import router as files_router
from backend.app.api.health import router as health_router
from backend.app.api.users import router as users_router

__all__ = ["auth_router", "diagnosis_router", "files_router", "health_router", "users_router"]
