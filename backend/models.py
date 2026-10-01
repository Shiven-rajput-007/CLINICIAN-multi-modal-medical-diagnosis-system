from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    hospital_name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False, default="Clinician")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    diagnoses = relationship(
        "DiagnosisHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(DiagnosisHistory.created_at)"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', hospital='{self.hospital_name}')>"


class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    modality = Column(String(50), nullable=False)
    image_filename = Column(String(255), nullable=False)
    image_prediction = Column(String(100), nullable=False)
    image_confidence = Column(Float, nullable=False)
    fusion_prediction = Column(String(100), nullable=False)
    fusion_confidence = Column(Float, nullable=False)
    symptoms = Column(JSON, nullable=False)
    class_probabilities = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="diagnoses")

    def __repr__(self):
        return f"<DiagnosisHistory(id={self.id}, user_id={self.user_id}, modality='{self.modality}', pred='{self.image_prediction}')>"
