import io
import json
import pytest
from PIL import Image

def generate_test_image_bytes(color=(180, 180, 190), size=(224, 224)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_empty_dashboard_stats(client, auth_headers):
    """Verifies that a new user sees true zeros and empty distributions."""
    resp = client.get("/api/diagnosis/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_diagnoses"] == 0
    assert data["chest_xray_count"] == 0
    assert data["brain_mri_count"] == 0
    assert data["average_confidence"] == 0.0
    assert data["most_recent_diagnosis"] is None
    assert data["class_distribution"] == {}
    assert "model_evaluation_metrics" in data

def test_infer_validation_errors(client, auth_headers):
    # Missing file
    resp = client.post(
        "/api/diagnosis/infer",
        headers=auth_headers,
        data={"modality": "chest_xray", "symptoms": "{}"}
    )
    assert resp.status_code == 422

    # Unsupported format
    txt_bytes = b"Hello not an image"
    files = {"file": ("test.txt", io.BytesIO(txt_bytes), "text/plain")}
    resp = client.post(
        "/api/diagnosis/infer",
        headers=auth_headers,
        files=files,
        data={"modality": "chest_xray", "symptoms": "{}"}
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]

    # Unsupported modality
    img_bytes = generate_test_image_bytes()
    files = {"file": ("scan.png", io.BytesIO(img_bytes), "image/png")}
    resp = client.post(
        "/api/diagnosis/infer",
        headers=auth_headers,
        files=files,
        data={"modality": "unsupported_echo", "symptoms": "{}"}
    )
    assert resp.status_code == 400
    assert "Invalid modality" in resp.json()["detail"]

def test_infer_and_history_flow(client, auth_headers, auth_headers_two):
    img_bytes = generate_test_image_bytes(color=(150, 160, 170))
    symptoms = json.dumps({"cough": True, "fever": True, "dyspnea": False})
    files = {"file": ("patient_scan_01.png", io.BytesIO(img_bytes), "image/png")}

    # 1. Run inference for Doctor 1
    resp = client.post(
        "/api/diagnosis/infer",
        headers=auth_headers,
        files=files,
        data={"modality": "chest_xray", "symptoms": symptoms}
    )
    assert resp.status_code == 201
    infer_data = resp.json()
    record_id = infer_data["id"]
    assert infer_data["modality"] == "chest_xray"
    assert infer_data["original_filename"] == "patient_scan_01.png"
    assert "predicted_class" in infer_data
    assert infer_data["confidence"] > 0
    assert len(infer_data["class_probabilities"]) == 5
    assert infer_data["image_url"].startswith("/api/files/uploads/")
    assert infer_data["gradcam_url"].startswith("/api/files/gradcam/")
    assert infer_data["gradcam_base64"].startswith("data:image/png;base64,")

    # 2. Check Doctor 1 stats updated to 1
    stats_resp = client.get("/api/diagnosis/stats", headers=auth_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_diagnoses"] == 1
    assert stats["chest_xray_count"] == 1
    assert stats["brain_mri_count"] == 0
    assert stats["average_confidence"] > 0
    assert stats["most_recent_diagnosis"]["id"] == record_id

    # 3. Check Doctor 2 (Isolation Check) still has 0 records!
    doc2_stats_resp = client.get("/api/diagnosis/stats", headers=auth_headers_two)
    assert doc2_stats_resp.status_code == 200
    doc2_stats = doc2_stats_resp.json()
    assert doc2_stats["total_diagnoses"] == 0
    assert doc2_stats["class_distribution"] == {}

    # 4. Check History pagination for Doctor 1
    hist_resp = client.get("/api/diagnosis/history?page=1&page_size=10", headers=auth_headers)
    assert hist_resp.status_code == 200
    hist = hist_resp.json()
    assert hist["total"] == 1
    assert hist["page"] == 1
    assert len(hist["records"]) == 1
    assert hist["records"][0]["id"] == record_id

    # Doctor 2 history must be empty
    doc2_hist_resp = client.get("/api/diagnosis/history?page=1&page_size=10", headers=auth_headers_two)
    assert doc2_hist_resp.status_code == 200
    assert doc2_hist_resp.json()["total"] == 0
    assert len(doc2_hist_resp.json()["records"]) == 0

    # 5. Doctor 2 cannot view or delete Doctor 1's record
    get_unauth = client.get(f"/api/diagnosis/history/{record_id}", headers=auth_headers_two)
    assert get_unauth.status_code == 404

    del_unauth = client.delete(f"/api/diagnosis/history/{record_id}", headers=auth_headers_two)
    assert del_unauth.status_code == 404

    # 6. Doctor 1 deletes own record
    del_auth = client.delete(f"/api/diagnosis/history/{record_id}", headers=auth_headers)
    assert del_auth.status_code == 204

    # 7. Verify Doctor 1 history is now 0 again
    hist_after = client.get("/api/diagnosis/history", headers=auth_headers).json()
    assert hist_after["total"] == 0
    assert len(hist_after["records"]) == 0
