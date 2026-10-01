from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class DiagnosisRecord(Base):
    __tablename__ = "diagnosis_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    modality = Column(String(50), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    predicted_class = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    class_probabilities = Column(JSON, nullable=False)
    symptom_data = Column(JSON, nullable=False)
    gradcam_path = Column(String(500), nullable=False)
    
    # Multimodal late-fusion comparison metadata
    image_prediction = Column(String(100), nullable=True)
    image_confidence = Column(Float, nullable=True)
    fusion_prediction = Column(String(100), nullable=True)
    fusion_confidence = Column(Float, nullable=True)
    
    model_version = Column(String(50), nullable=False, default="densenet121-multimodal-v1")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="diagnoses")

    def __repr__(self):
        return f"<DiagnosisRecord(id={self.id}, user_id={self.user_id}, modality='{self.modality}', pred='{self.predicted_class}')>"
