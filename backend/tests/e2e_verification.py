import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.models.diagnosis import DiagnosisRecord

def run_e2e_verification():
    print("==================================================================")
    print("STARTING FULL END-TO-END VERIFICATION OF CLINICAL ASSISTANT")
    print("==================================================================")

    client = TestClient(app)

    # 1. Clean test DB
    db = SessionLocal()
    db.query(DiagnosisRecord).delete()
    db.query(User).delete()
    db.commit()

    users_count = db.query(User).count()
    diag_count = db.query(DiagnosisRecord).count()
    assert users_count == 0, "Users table must start completely empty!"
    assert diag_count == 0, "Diagnosis table must start completely empty!"
    print(f"[VERIFIED] Database starts completely EMPTY: {users_count} users, {diag_count} diagnoses.")

    # 2. Register Dr. Robert Chase
    reg_payload = {
        "name": "Dr. Robert Chase",
        "email": "chase@princeton.org",
        "password": "IntensiveCare2026!",
        "hospital_name": "Princeton-Plainsboro",
        "role": "doctor"
    }
    resp = client.post("/api/auth/register", json=reg_payload)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    user_data = resp.json()
    assert user_data["email"] == "chase@princeton.org"
    assert "password_hash" not in user_data
    print(f"[VERIFIED] User registration successful: ID #{user_data['id']}, Name: {user_data['name']}")

    # 3. Login
    login_resp = client.post("/api/auth/login", json={
        "email": "chase@princeton.org",
        "password": "IntensiveCare2026!"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[VERIFIED] Authentication successful; signed JWT access token issued.")

    # 4. Verify Brand New User Stats (Rule 1: NO DEMO DATA)
    stats_resp = client.get("/api/diagnosis/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_diagnoses"] == 0, "Must be 0 for new user"
    assert stats["chest_xray_count"] == 0, "Must be 0 for new user"
    assert stats["brain_mri_count"] == 0, "Must be 0 for new user"
    assert stats["average_confidence"] == 0.0, "Must be 0.0 for new user"
    assert stats["most_recent_diagnosis"] is None, "Must be None for new user"
    assert stats["class_distribution"] == {}, "Must be empty for new user"
    print("[VERIFIED] Brand new user sees genuine ZERO stats and empty distribution:")
    print("           Total Diagnoses: 0 | Chest: 0 | Brain: 0 | Avg Confidence: 0.0%")

    # 5. Verify Brand New User History
    hist_resp = client.get("/api/diagnosis/history", headers=headers)
    assert hist_resp.status_code == 200
    hist = hist_resp.json()
    assert hist["total"] == 0
    assert len(hist["records"]) == 0
    print("[VERIFIED] Brand new user history is genuine EMPTY: 0 records.")

    # 6. Real Chest X-Ray Diagnosis Inference
    chest_scan_path = PROJECT_ROOT / "data" / "test_scans" / "chest_xray_test.png"
    assert chest_scan_path.exists(), f"Test scan missing at {chest_scan_path}"
    with open(chest_scan_path, "rb") as f:
        chest_bytes = f.read()

    files = {"file": ("chest_xray_test.png", chest_bytes, "image/png")}
    data = {
        "modality": "chest_xray",
        "symptoms": '{"cough": true, "fever": true, "dyspnea": true}'
    }
    infer1_resp = client.post("/api/diagnosis/infer", headers=headers, files=files, data=data)
    assert infer1_resp.status_code == 201, f"Inference failed: {infer1_resp.text}"
    rec1 = infer1_resp.json()
    assert rec1["modality"] == "chest_xray"
    assert rec1["predicted_class"] in ["Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Pleural Effusion"]
    assert len(rec1["class_probabilities"]) == 5
    assert rec1["gradcam_base64"].startswith("data:image/png;base64,")
    assert rec1["image_url"].startswith("/api/files/uploads/")
    assert rec1["gradcam_url"].startswith("/api/files/gradcam/")
    print(f"[VERIFIED] Real Chest X-Ray inference succeeded:")
    print(f"           Predicted Class: '{rec1['predicted_class']}' ({rec1['confidence']*100:.1f}%)")
    print(f"           Grad-CAM Generated: {len(rec1['gradcam_base64'])} base64 chars | DB Record ID: #{rec1['id']}")

    # 7. Real Brain MRI Diagnosis Inference
    brain_scan_path = PROJECT_ROOT / "data" / "test_scans" / "brain_mri_test.png"
    assert brain_scan_path.exists(), f"Test scan missing at {brain_scan_path}"
    with open(brain_scan_path, "rb") as f:
        brain_bytes = f.read()

    files = {"file": ("brain_mri_test.png", brain_bytes, "image/png")}
    data = {
        "modality": "brain_mri",
        "symptoms": '{"headache": true, "vision_changes": true}'
    }
    infer2_resp = client.post("/api/diagnosis/infer", headers=headers, files=files, data=data)
    assert infer2_resp.status_code == 201, f"Brain inference failed: {infer2_resp.text}"
    rec2 = infer2_resp.json()
    assert rec2["modality"] == "brain_mri"
    assert rec2["predicted_class"] in ["Glioma", "Meningioma", "No Tumor", "Pituitary"]
    assert len(rec2["class_probabilities"]) == 4
    assert rec2["gradcam_base64"].startswith("data:image/png;base64,")
    print(f"[VERIFIED] Real Brain MRI inference succeeded:")
    print(f"           Predicted Class: '{rec2['predicted_class']}' ({rec2['confidence']*100:.1f}%)")
    print(f"           Grad-CAM Generated: {len(rec2['gradcam_base64'])} base64 chars | DB Record ID: #{rec2['id']}")

    # 8. Check Dashboard Stats Updated
    stats_updated_resp = client.get("/api/diagnosis/stats", headers=headers)
    assert stats_updated_resp.status_code == 200
    u_stats = stats_updated_resp.json()
    assert u_stats["total_diagnoses"] == 2
    assert u_stats["chest_xray_count"] == 1
    assert u_stats["brain_mri_count"] == 1
    assert u_stats["average_confidence"] > 0
    assert u_stats["most_recent_diagnosis"]["id"] == rec2["id"]
    print(f"[VERIFIED] Dashboard statistics updated from real DB records:")
    print(f"           Total: {u_stats['total_diagnoses']} | Chest: {u_stats['chest_xray_count']} | Brain: {u_stats['brain_mri_count']} | Avg Conf: {u_stats['average_confidence']*100:.1f}%")

    # 9. Verify History with Pagination
    hist_updated = client.get("/api/diagnosis/history?page=1&page_size=10", headers=headers).json()
    assert hist_updated["total"] == 2
    assert len(hist_updated["records"]) == 2
    print(f"[VERIFIED] History returns {hist_updated['total']} records with full pagination metadata.")

    # 10. Test Deletion of Record 1
    del_resp = client.delete(f"/api/diagnosis/history/{rec1['id']}", headers=headers)
    assert del_resp.status_code == 204
    hist_after_del = client.get("/api/diagnosis/history", headers=headers).json()
    assert hist_after_del["total"] == 1
    assert hist_after_del["records"][0]["id"] == rec2["id"]
    print(f"[VERIFIED] Deletion succeeded: Record #{rec1['id']} removed from database.")

    # 11. Test User Isolation (Doctor 2)
    reg_doc2 = client.post("/api/auth/register", json={
        "name": "Dr. Allison Cameron",
        "email": "cameron@princeton.org",
        "password": "ImmunologyChief123!",
        "hospital_name": "Princeton-Plainsboro",
        "role": "doctor"
    }).json()

    login_doc2 = client.post("/api/auth/login", json={
        "email": "cameron@princeton.org",
        "password": "ImmunologyChief123!"
    }).json()
    headers_doc2 = {"Authorization": f"Bearer {login_doc2['access_token']}"}

    # Doctor 2 must see 0 diagnoses
    doc2_stats = client.get("/api/diagnosis/stats", headers=headers_doc2).json()
    assert doc2_stats["total_diagnoses"] == 0, "Doctor 2 must NOT see Doctor 1's records!"

    # Doctor 2 cannot delete Doctor 1's remaining record
    unauth_del = client.delete(f"/api/diagnosis/history/{rec2['id']}", headers=headers_doc2)
    assert unauth_del.status_code == 404, "Cross-user deletion must be rejected with 404!"
    print("[VERIFIED] Strict User Isolation verified: Doctor 2 cannot see or delete Doctor 1's records.")

    # 12. Reset to clean empty database for production
    db.query(DiagnosisRecord).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    print("[VERIFIED] Database cleanly reset to EMPTY state for initial user start.")

    print("\n==================================================================")
    print("ALL END-TO-END VERIFICATION CHECKS PASSED (12/12)!")
    print("==================================================================")

if __name__ == "__main__":
    run_e2e_verification()
