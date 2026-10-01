import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings, BASE_DIR

# Ensure data directory exists
data_dir = BASE_DIR / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# Ensure SQLite database directory is resolved safely on Windows
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    raw_path = db_url[len("sqlite:///"):]
    p = Path(raw_path)
    if not p.is_absolute():
        p = BASE_DIR / p
    p.parent.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{p.as_posix()}"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
