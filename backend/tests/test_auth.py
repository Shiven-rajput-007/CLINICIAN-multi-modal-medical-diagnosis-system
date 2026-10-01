import pytest

def test_register_success(client):
    payload = {
        "name": "Dr. Allison Cameron",
        "email": "cameron@hospital.org",
        "password": "SecurePassword123!",
        "hospital_name": "General Hospital",
        "role": "doctor"
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "password" not in data
    assert "password_hash" not in data
    assert "id" in data

def test_register_duplicate_email(client, registered_doctor):
    resp = client.post("/api/auth/register", json=registered_doctor)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]

def test_login_invalid_password(client, registered_doctor):
    payload = {
        "email": registered_doctor["email"],
        "password": "WrongPassword123!"
    }
    resp = client.post("/api/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]

def test_login_success(client, registered_doctor):
    payload = {
        "email": registered_doctor["email"],
        "password": registered_doctor["password"]
    }
    resp = client.post("/api/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == registered_doctor["email"]
    assert "password_hash" not in data["user"]

def test_protected_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

def test_protected_me_with_token(client, auth_headers, registered_doctor):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == registered_doctor["email"]
    assert data["name"] == registered_doctor["name"]
