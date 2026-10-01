import sys
import io
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User

client = TestClient(app)

def generate_sample_image_bytes(color=(150, 150, 170), size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_api():
    print("\n=======================================================")
    print("STARTING FASTAPI ENDPOINTS VERIFICATION")
    print("=======================================================\n")

    # 1. Test Root and Health Check
    print("[1/6] Testing GET / and GET /health...")
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    assert r.json()["status"] == "operational"

    r = client.get("/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    assert r.json()["models_ready"] is True
    print("[PASS] Root and health endpoints operational.")

    # 2. Test Registration
    print("[2/6] Testing POST /register...")
    test_email = "alex.carey@saintjudes.org"
    # Ensure clean slate
    db = SessionLocal()
    db.query(User).filter(User.email == test_email).delete()
    db.commit()
    db.close()

    reg_payload = {
        "name": "Dr. Alex Carey",
        "email": test_email,
        "password": "ClinicalPassword2026!",
        "hospital_name": "St. Jude Hospital",
        "role": "Chief Radiologist"
    }
    r = client.post("/register", json=reg_payload)
    assert r.status_code == 201, f"Registration failed: {r.text}"
    reg_data = r.json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] Clinician registration successful.")

    # 3. Test Duplicate Registration Block
    r = client.post("/register", json=reg_payload)
    assert r.status_code == 400, "Duplicate registration should return 400"
    print("[PASS] Duplicate registration successfully prevented.")

    # 4. Test Login and /me
    print("[3/6] Testing POST /login and GET /me...")
    login_payload = {"email": test_email, "password": "ClinicalPassword2026!"}
    r = client.post("/login", json=login_payload)
    assert r.status_code == 200, f"Login failed: {r.text}"
    assert "access_token" in r.json()

    r = client.get("/me", headers=headers)
    assert r.status_code == 200, f"/me failed: {r.text}"
    assert r.json()["email"] == test_email
    assert r.json()["hospital_name"] == "St. Jude Hospital"
    print("[PASS] Login and /me profile retrieval passed.")

    # 5. Test Multipart Diagnosis Inference
    print("[4/6] Testing POST /diagnose (Chest X-ray)...")
    img_bytes = generate_sample_image_bytes()
    files = {
        "file": ("patient_scan_042.png", img_bytes, "image/png")
    }
    data = {
        "modality": "chest_xray",
        "symptoms": json.dumps({"cough": True, "dyspnea": True, "fever": False})
    }
    r = client.post("/diagnose", headers=headers, files=files, data=data)
    assert r.status_code == 200, f"Diagnosis failed: {r.text}"
    diag_res = r.json()
    assert diag_res["modality"] == "chest_xray"
    assert "image_prediction" in diag_res
    assert "fusion_prediction" in diag_res
    assert diag_res["gradcam_image"].startswith("data:image/png;base64,")
    print(f"[PASS] Diagnosis inference API succeeded: Image Class='{diag_res['image_prediction']['class']}', Fusion Class='{diag_res['fusion_prediction']['class']}'.")

    # 6. Test Save and Retrieve Diagnosis History
    print("[5/6] Testing POST & GET /diagnosis-history...")
    history_payload = {
        "modality": "chest_xray",
        "image_filename": "patient_scan_042.png",
        "image_prediction": diag_res["image_prediction"]["class"],
        "image_confidence": diag_res["image_prediction"]["confidence"],
        "fusion_prediction": diag_res["fusion_prediction"]["class"],
        "fusion_confidence": diag_res["fusion_prediction"]["confidence"],
        "symptoms": {"cough": True, "dyspnea": True, "fever": False},
        "class_probabilities": diag_res["image_prediction"]["probabilities"]
    }
    r = client.post("/diagnosis-history", headers=headers, json=history_payload)
    assert r.status_code == 201, f"Save history failed: {r.text}"
    saved_id = r.json()["id"]

    r = client.get("/diagnosis-history", headers=headers)
    assert r.status_code == 200, f"Get history failed: {r.text}"
    hist_list = r.json()
    assert len(hist_list) >= 1
    assert hist_list[0]["id"] == saved_id
    print(f"[PASS] Saved and retrieved audit history record #{saved_id}.")

    # 6. Test Error Cases
    print("[6/6] Testing edge and error cases...")
    # Invalid token
    r = client.get("/me", headers={"Authorization": "Bearer invalid_token_123"})
    assert r.status_code == 401
    # Invalid modality
    r = client.post("/diagnose", headers=headers, files=files, data={"modality": "invalid_modality", "symptoms": "{}"})
    assert r.status_code == 400
    # Invalid file type
    bad_files = {"file": ("document.pdf", b"pdf content", "application/pdf")}
    r = client.post("/diagnose", headers=headers, files=bad_files, data={"modality": "chest_xray", "symptoms": "{}"})
    assert r.status_code == 400
    print("[PASS] All edge cases (invalid token, bad modality, invalid file format) handled correctly.")

    print("\n=======================================================")
    print("ALL FASTAPI ENDPOINT TESTS PASSED SUCCESSFULLY! (6/6)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_api()
