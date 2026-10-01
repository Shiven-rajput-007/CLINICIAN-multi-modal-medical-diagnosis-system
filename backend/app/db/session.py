import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("medical_assistant.db")

# Parse connection arguments based on driver
connect_args = {}
db_url = settings.resolved_database_url
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # Ensure parent directory exists for sqlite DB file
    if "///" in db_url:
        db_path_str = db_url.split("///")[-1]
        try:
            Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create DB parent directory: {e}")

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency yielding an isolated SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
