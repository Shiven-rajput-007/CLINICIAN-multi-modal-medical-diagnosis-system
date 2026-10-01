import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup paths
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# In-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def registered_doctor(client):
    reg_data = {
        "name": "Dr. Gregory House",
        "email": "house@princeton.org",
        "password": "DiagnosticMaster123!",
        "hospital_name": "Princeton-Plainsboro",
        "role": "doctor"
    }
    resp = client.post("/api/auth/register", json=reg_data)
    assert resp.status_code == 201
    return reg_data

@pytest.fixture
def auth_headers(client, registered_doctor):
    login_data = {
        "email": registered_doctor["email"],
        "password": registered_doctor["password"]
    }
    resp = client.post("/api/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def doctor_two(client):
    reg_data = {
        "name": "Dr. James Wilson",
        "email": "wilson@princeton.org",
        "password": "OncologyChief123!",
        "hospital_name": "Princeton-Plainsboro",
        "role": "doctor"
    }
    resp = client.post("/api/auth/register", json=reg_data)
    assert resp.status_code == 201
    return reg_data

@pytest.fixture
def auth_headers_two(client, doctor_two):
    login_data = {
        "email": doctor_two["email"],
        "password": doctor_two["password"]
    }
    resp = client.post("/api/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
