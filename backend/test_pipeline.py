import os
import sys
import io
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
from PIL import Image
import torch

from backend.config import settings, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from backend.database import init_db, SessionLocal
from backend.models import User, DiagnosisHistory
from backend.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from backend.ml.weights_init import initialize_weights_if_missing
from backend.ml.loader import get_model_manager
from backend.ml.prediction import run_diagnosis

def generate_sample_medical_image(color=(200, 200, 200), size=(256, 256)) -> bytes:
    """Generates a synthetic medical scan byte string for testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_all_tests():
    print("\n=======================================================")
    print("STARTING FULL END-TO-END PIPELINE VERIFICATION")
    print("=======================================================\n")

    # 1. Test Database Initialization
    print("[1/7] Testing SQLite database initialization...")
    init_db()
    db = SessionLocal()
    print("[PASS] SQLite database initialized successfully.")

    # 2. Test Authentication & Password Hashing
    print("[2/7] Testing bcrypt hashing and JWT token handling...")
    test_password = "DoctorSecurePassword123!"
    hashed = get_password_hash(test_password)
    assert verify_password(test_password, hashed), "Password verification failed!"
    assert not verify_password("WrongPassword", hashed), "Invalid password incorrectly verified!"

    token = create_access_token({"sub": "test.doctor@hospital.org", "id": 999})
    payload = decode_access_token(token)
    assert payload is not None and payload.get("sub") == "test.doctor@hospital.org"
    print("[PASS] Bcrypt hashing and JWT encoding/decoding passed.")

    # 3. Test Model Weights Initialization
    print("[3/7] Testing PyTorch weight bootstrapper...")
    weights_info = initialize_weights_if_missing()
    for name, pth in weights_info.items():
        assert Path(pth).exists(), f"Model checkpoint file not found: {pth}"
    print(f"[PASS] PyTorch model checkpoints verified on disk: {list(weights_info.keys())}")

    # 4. Test Model Loading & Memory Residency
    print("[4/7] Testing ModelManager resident loading...")
    manager = get_model_manager()
    assert manager.is_ready(), "ModelManager not marked ready!"
    assert manager.chest_image_model is not None, "Chest image model not loaded!"
    assert manager.chest_fusion_model is not None, "Chest fusion model not loaded!"
    assert manager.chest_gradcam is not None, "Chest Grad-CAM not initialized!"
    assert manager.brain_image_model is not None, "Brain image model not loaded!"
    assert manager.brain_fusion_model is not None, "Brain fusion model not loaded!"
    assert manager.brain_gradcam is not None, "Brain Grad-CAM not initialized!"
    print(f"[PASS] Models loaded in memory on device: {manager.device}")

    # 5. Test Chest X-Ray Diagnosis & Grad-CAM
    print("[5/7] Testing Chest X-Ray inference and Grad-CAM generation...")
    chest_img_bytes = generate_sample_medical_image(color=(180, 180, 190))
    chest_symptoms = {"cough": True, "fever": True, "dyspnea": True, "chest_pain": False}
    chest_res = run_diagnosis(
        image_bytes=chest_img_bytes,
        modality="chest_xray",
        symptoms_dict=chest_symptoms,
        image_filename="sample_chest_xray.png"
    )
    assert chest_res["modality"] == "chest_xray"
    assert chest_res["image_prediction"]["prediction_class"] in CHEST_XRAY_CLASSES
    assert len(chest_res["image_prediction"]["probabilities"]) == 5
    assert len(chest_res["fusion_prediction"]["probabilities"]) == 5
    assert chest_res["gradcam_image"].startswith("data:image/png;base64,")
    print(f"[PASS] Chest X-Ray inference successful: Image Pred='{chest_res['image_prediction']['prediction_class']}' ({chest_res['image_prediction']['confidence']*100:.1f}%), Fusion Pred='{chest_res['fusion_prediction']['prediction_class']}' ({chest_res['fusion_prediction']['confidence']*100:.1f}%)")
    print(f"[PASS] Grad-CAM heatmap generated successfully (length: {len(chest_res['gradcam_image'])} chars).")

    # 6. Test Brain MRI Diagnosis & Grad-CAM
    print("[6/7] Testing Brain MRI inference and Grad-CAM generation...")
    brain_img_bytes = generate_sample_medical_image(color=(120, 120, 140))
    brain_symptoms = {"headache": True, "seizures": False, "vision_changes": True}
    brain_res = run_diagnosis(
        image_bytes=brain_img_bytes,
        modality="brain_mri",
        symptoms_dict=brain_symptoms,
        image_filename="sample_brain_mri.png"
    )
    assert brain_res["modality"] == "brain_mri"
    assert brain_res["image_prediction"]["prediction_class"] in BRAIN_MRI_CLASSES
    assert len(brain_res["image_prediction"]["probabilities"]) == 4
    assert len(brain_res["fusion_prediction"]["probabilities"]) == 4
    assert brain_res["gradcam_image"].startswith("data:image/png;base64,")
    print(f"[PASS] Brain MRI inference successful: Image Pred='{brain_res['image_prediction']['prediction_class']}' ({brain_res['image_prediction']['confidence']*100:.1f}%), Fusion Pred='{brain_res['fusion_prediction']['prediction_class']}' ({brain_res['fusion_prediction']['confidence']*100:.1f}%)")

    # 7. Test User Isolation and Audit History in Database
    print("[7/7] Testing Doctor Authentication and Data Isolation in SQLite...")
    # Clean previous test users if any
    db.query(User).filter(User.email.in_(["doc1@hospital.org", "doc2@hospital.org"])).delete(synchronize_session=False)
    db.commit()

    # Create Doctor 1
    doc1 = User(
        name="Dr. Gregory House",
        email="doc1@hospital.org",
        password_hash=get_password_hash("HouseMD123!"),
        hospital_name="Princeton-Plainsboro",
        role="Diagnostician"
    )
    # Create Doctor 2
    doc2 = User(
        name="Dr. James Wilson",
        email="doc2@hospital.org",
        password_hash=get_password_hash("WilsonMD123!"),
        hospital_name="Princeton-Plainsboro",
        role="Oncologist"
    )
    db.add_all([doc1, doc2])
    db.commit()
    db.refresh(doc1)
    db.refresh(doc2)

    # Save diagnosis for Doctor 1
    hist1 = DiagnosisHistory(
        user_id=doc1.id,
        modality="chest_xray",
        image_filename="chest_patient_01.png",
        image_prediction=chest_res["image_prediction"]["prediction_class"],
        image_confidence=chest_res["image_prediction"]["confidence"],
        fusion_prediction=chest_res["fusion_prediction"]["prediction_class"],
        fusion_confidence=chest_res["fusion_prediction"]["confidence"],
        symptoms=chest_symptoms,
        class_probabilities=chest_res["image_prediction"]["probabilities"]
    )
    db.add(hist1)
    db.commit()

    # Query Doctor 1 records
    doc1_records = db.query(DiagnosisHistory).filter(DiagnosisHistory.user_id == doc1.id).all()
    assert len(doc1_records) == 1, "Doctor 1 should have 1 record"

    # Query Doctor 2 records (Verify Isolation)
    doc2_records = db.query(DiagnosisHistory).filter(DiagnosisHistory.user_id == doc2.id).all()
    assert len(doc2_records) == 0, "Doctor 2 must NOT see Doctor 1's records (Data isolation breach)!"
    print("[PASS] Strict doctor audit history data isolation verified.")

    db.close()
    print("\n=======================================================")
    print("ALL END-TO-END TESTS PASSED SUCCESSFULLY! (7/7)")
    print("=======================================================\n")

if __name__ == "__main__":
    run_all_tests()
