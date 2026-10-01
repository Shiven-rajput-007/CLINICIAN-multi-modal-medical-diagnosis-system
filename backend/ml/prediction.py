import logging
from typing import Dict, Any
import torch
from backend.config import MODEL_METADATA
from backend.ml.preprocessing import preprocess_image
from backend.ml.fusion import build_symptom_tensor
from backend.ml.loader import get_model_manager

logger = logging.getLogger("medical_assistant.prediction")

def run_diagnosis(
    image_bytes: bytes,
    modality: str,
    symptoms_dict: Dict[str, bool],
    image_filename: str
) -> Dict[str, Any]:
    """
    Executes end-to-end multimodal diagnosis:
    1. Preprocesses medical image
    2. Runs PyTorch DenseNet-121 image model inference
    3. Runs Late-Fusion multimodal model inference with symptom vector
    4. Computes Grad-CAM explainability heatmap overlay
    5. Returns structured prediction results
    """
    if modality not in MODEL_METADATA:
        raise ValueError(f"Unsupported modality '{modality}'. Supported modalities: {list(MODEL_METADATA.keys())}")

    meta = MODEL_METADATA[modality]
    classes = meta["classes"]
    symptom_order = meta["symptoms"]

    # 1. Image preprocessing
    input_tensor, pil_image = preprocess_image(image_bytes, target_size=meta["image_size"])

    # 2. Retrieve resident models
    manager = get_model_manager()
    device = manager.device
    input_tensor = input_tensor.to(device)

    if modality == "chest_xray":
        image_model = manager.chest_image_model
        fusion_model = manager.chest_fusion_model
        gradcam = manager.chest_gradcam
    else:
        image_model = manager.brain_image_model
        fusion_model = manager.brain_fusion_model
        gradcam = manager.brain_gradcam

    # 3. Prepare symptom tensor
    symptom_tensor = build_symptom_tensor(symptoms_dict, symptom_order, device)

    # 4. Image-only Inference
    with torch.no_grad():
        img_logits = image_model(input_tensor)
        img_probs = torch.softmax(img_logits, dim=1)[0]
        img_pred_idx = int(torch.argmax(img_probs).item())
        img_pred_class = classes[img_pred_idx]
        img_confidence = float(img_probs[img_pred_idx].item())
        img_probs_dict = {
            classes[i]: round(float(img_probs[i].item()), 4)
            for i in range(len(classes))
        }

    # 5. Multimodal Late-Fusion Inference
    with torch.no_grad():
        _, fusion_logits = fusion_model(input_tensor, symptom_tensor)
        fusion_probs = torch.softmax(fusion_logits, dim=1)[0]
        fusion_pred_idx = int(torch.argmax(fusion_probs).item())
        fusion_pred_class = classes[fusion_pred_idx]
        fusion_confidence = float(fusion_probs[fusion_pred_idx].item())
        fusion_probs_dict = {
            classes[i]: round(float(fusion_probs[i].item()), 4)
            for i in range(len(classes))
        }

    # 6. Grad-CAM Explainability Generation
    # We pass the input_tensor to compute gradient maps for the predicted class
    try:
        gradcam_b64 = gradcam.generate_base64_overlay(
            input_tensor=input_tensor,
            original_image=pil_image,
            target_class_idx=img_pred_idx,
            alpha=0.45
        )
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=True)
        gradcam_b64 = ""

    return {
        "modality": modality,
        "image_prediction": {
            "prediction_class": img_pred_class,
            "confidence": round(img_confidence, 4),
            "probabilities": img_probs_dict
        },
        "fusion_prediction": {
            "prediction_class": fusion_pred_class,
            "confidence": round(fusion_confidence, 4),
            "probabilities": fusion_probs_dict
        },
        "gradcam_image": gradcam_b64,
        "image_filename": image_filename,
        "symptoms": symptoms_dict
    }
