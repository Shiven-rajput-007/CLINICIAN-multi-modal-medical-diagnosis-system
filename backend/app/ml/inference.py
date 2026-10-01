import logging
from typing import Dict, Any, Tuple
from PIL import Image
import torch

from app.core.config import MODEL_METADATA
from app.ml.preprocessing import preprocess_image
from app.ml.fusion import build_symptom_tensor
from app.ml.model_loader import get_model_manager

logger = logging.getLogger("medical_assistant.inference")

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
    5. Returns structured prediction results and PIL images
    """
    if modality not in MODEL_METADATA:
        raise ValueError(f"Unsupported modality '{modality}'. Supported modalities: {list(MODEL_METADATA.keys())}")

    meta = MODEL_METADATA[modality]
    classes = meta["classes"]
    symptom_order = meta["symptoms"]

    # 1. Preprocess Image
    input_tensor, pil_image = preprocess_image(image_bytes, target_size=meta["image_size"])

    # 2. Retrieve lazy-loaded modality bundle
    manager = get_model_manager()
    device = manager.device
    input_tensor = input_tensor.to(device)

    bundle = manager.get_modality_bundle(modality)
    image_model = bundle["image_model"]
    fusion_model = bundle["fusion_model"]
    gradcam = bundle["gradcam"]

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
    gradcam_b64 = ""
    gradcam_pil: Image.Image = pil_image.copy()
    try:
        heatmap, _ = gradcam.generate_heatmap(input_tensor, target_class_idx=img_pred_idx)
        gradcam_pil = gradcam.overlay_on_image(heatmap, pil_image, alpha=0.45)
        gradcam_b64 = gradcam.generate_base64_overlay(
            input_tensor=input_tensor,
            original_image=pil_image,
            target_class_idx=img_pred_idx,
            alpha=0.45
        )
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=True)

    return {
        "modality": modality,
        "image_filename": image_filename,
        "predicted_class": fusion_pred_class,
        "confidence": round(fusion_confidence, 4),
        "class_probabilities": fusion_probs_dict,
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
        "gradcam_base64": gradcam_b64,
        "gradcam_pil": gradcam_pil,
        "pil_image": pil_image,
        "symptoms": symptoms_dict
    }
