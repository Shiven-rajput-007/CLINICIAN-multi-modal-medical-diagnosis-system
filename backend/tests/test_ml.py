import pytest
import io
from PIL import Image
from backend.app.ml.model_loader import get_model_manager
from backend.app.ml.preprocessing import preprocess_image
from backend.app.ml.inference import run_diagnosis
from backend.app.core.config import CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES

def generate_test_image(color=(128, 128, 128), size=(256, 256)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_model_manager_readiness():
    manager = get_model_manager()
    assert manager.is_ready()
    assert manager.chest_image_model is not None
    assert manager.chest_fusion_model is not None
    assert manager.brain_image_model is not None
    assert manager.brain_fusion_model is not None
    assert manager.chest_gradcam is not None
    assert manager.brain_gradcam is not None

def test_preprocessing():
    img_bytes = generate_test_image(size=(300, 300))
    tensor, pil_img = preprocess_image(img_bytes, target_size=(224, 224))
    assert tensor.shape == (1, 3, 224, 224)
    assert pil_img.size == (300, 300)

def test_chest_xray_inference_and_gradcam():
    img_bytes = generate_test_image(color=(160, 160, 170))
    symptoms = {"cough": True, "fever": True, "dyspnea": True}
    res = run_diagnosis(
        image_bytes=img_bytes,
        modality="chest_xray",
        symptoms_dict=symptoms,
        image_filename="test_chest.png"
    )
    assert res["modality"] == "chest_xray"
    assert res["predicted_class"] in CHEST_XRAY_CLASSES
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["class_probabilities"]) == 5
    for c in CHEST_XRAY_CLASSES:
        assert c in res["class_probabilities"]
    assert res["gradcam_base64"].startswith("data:image/png;base64,")

def test_brain_mri_inference_and_gradcam():
    img_bytes = generate_test_image(color=(110, 120, 130))
    symptoms = {"headache": True, "vision_changes": True}
    res = run_diagnosis(
        image_bytes=img_bytes,
        modality="brain_mri",
        symptoms_dict=symptoms,
        image_filename="test_brain.png"
    )
    assert res["modality"] == "brain_mri"
    assert res["predicted_class"] in BRAIN_MRI_CLASSES
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["class_probabilities"]) == 4
    for c in BRAIN_MRI_CLASSES:
        assert c in res["class_probabilities"]
    assert res["gradcam_base64"].startswith("data:image/png;base64,")
