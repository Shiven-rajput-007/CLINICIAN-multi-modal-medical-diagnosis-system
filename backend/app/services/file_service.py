import uuid
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from fastapi import HTTPException, status
from backend.app.core.config import settings

class FileService:
    @staticmethod
    def initialize_storage():
        """Ensures storage directories exist."""
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        settings.GRADCAM_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_upload_image(image_bytes: bytes, original_filename: str) -> Tuple[str, Path]:
        """
        Saves raw uploaded image bytes to storage/uploads with a secure unique UUID filename.
        Returns (relative_storage_path, full_file_path).
        """
        FileService.initialize_storage()
        ext = Path(original_filename).suffix.lower()
        if not ext or ext not in [".png", ".jpg", ".jpeg"]:
            ext = ".png"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = settings.UPLOAD_DIR / unique_name
        target_path.write_bytes(image_bytes)
        relative_path = f"uploads/{unique_name}"
        return relative_path, target_path

    @staticmethod
    def save_gradcam_image(gradcam_pil: Image.Image) -> Tuple[str, Path]:
        """
        Saves Grad-CAM PIL image to storage/gradcam with a secure unique UUID filename.
        Returns (relative_storage_path, full_file_path).
        """
        FileService.initialize_storage()
        unique_name = f"gradcam_{uuid.uuid4().hex}.png"
        target_path = settings.GRADCAM_DIR / unique_name
        gradcam_pil.save(target_path, format="PNG", optimize=True)
        relative_path = f"gradcam/{unique_name}"
        return relative_path, target_path

    @staticmethod
    def resolve_safe_file_path(category: str, filename: str) -> Path:
        """
        Validates category and filename to strictly prevent path traversal attacks.
        Returns the resolved Path if it exists and is within the storage directory.
        """
        if category not in ["uploads", "gradcam"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file category '{category}'. Must be 'uploads' or 'gradcam'."
            )

        # Disallow directory traversal characters
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file identifier."
            )

        base_dir = settings.UPLOAD_DIR if category == "uploads" else settings.GRADCAM_DIR
        full_path = (base_dir / filename).resolve()

        # Strict containment check
        try:
            full_path.relative_to(base_dir.resolve())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to specified file path is forbidden."
            )

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requested clinical image file not found."
            )

        return full_path

    @staticmethod
    def delete_file_safely(relative_path: Optional[str]):
        """Safely deletes a file from disk if it exists."""
        if not relative_path:
            return
        try:
            full_path = settings.STORAGE_DIR / relative_path
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
        except Exception:
            pass
