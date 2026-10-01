from typing import Optional, Dict, Any
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    database_connected: bool
    models_ready: bool
    device: str
    modalities: Dict[str, Any]

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
