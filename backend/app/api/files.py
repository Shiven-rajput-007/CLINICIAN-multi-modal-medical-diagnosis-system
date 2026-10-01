from fastapi import APIRouter
from fastapi.responses import FileResponse
from backend.app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["File Storage"])

@router.get("/{category}/{filename}")
def get_stored_file(category: str, filename: str):
    """
    Safely retrieves a stored medical scan or Grad-CAM overlay image.
    Strictly verifies directory containment to prevent path traversal.
    """
    file_path = FileService.resolve_safe_file_path(category, filename)
    ext = file_path.suffix.lower()
    media_type = "image/png"
    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"

    return FileResponse(file_path, media_type=media_type)
