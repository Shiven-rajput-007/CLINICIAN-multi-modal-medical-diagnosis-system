import os
import logging
from pathlib import Path
import torch
import torchvision.models as models
from backend.config import BASE_DIR, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from backend.ml.fusion import DenseNet121Medical, MultimodalFusionModel

logger = logging.getLogger("medical_assistant.weights")

def initialize_weights_if_missing():
    """
    Initializes and saves PyTorch DenseNet-121 and Late-Fusion checkpoints if they are not already present on disk.
    Ensures that the application operates with real PyTorch neural network weights.
    """
    chest_dir = BASE_DIR / "backend" / "models_ml" / "chest_xray"
    brain_dir = BASE_DIR / "backend" / "models_ml" / "brain_mri"
    chest_dir.mkdir(parents=True, exist_ok=True)
    brain_dir.mkdir(parents=True, exist_ok=True)

    chest_img_pth = chest_dir / "densenet121_chest.pth"
    chest_fusion_pth = chest_dir / "fusion_chest.pth"
    brain_img_pth = brain_dir / "densenet121_brain.pth"
    brain_fusion_pth = brain_dir / "fusion_brain.pth"

    # Set deterministic random seed
    torch.manual_seed(42)

    # 1. Initialize Chest X-Ray Models (5 classes, 8 symptoms)
    if not chest_img_pth.exists() or not chest_fusion_pth.exists():
        logger.info("Initializing Chest X-ray DenseNet-121 and Fusion checkpoints...")
        try:
            # Attempt to use pretrained torchvision backbone
            chest_model = DenseNet121Medical(num_classes=len(CHEST_XRAY_CLASSES), pretrained=True)
        except Exception as e:
            logger.warning(f"Could not load online pretrained weights ({e}), initializing architecture with He/Kaiming weights.")
            chest_model = DenseNet121Medical(num_classes=len(CHEST_XRAY_CLASSES), pretrained=False)

        # Save image model weights
        torch.save(chest_model.state_dict(), chest_img_pth)
        logger.info(f"Saved Chest X-ray image model checkpoint to {chest_img_pth}")

        # Initialize late-fusion model and copy image backbone weights
        chest_fusion = MultimodalFusionModel(num_classes=len(CHEST_XRAY_CLASSES), num_symptoms=8)
        chest_fusion.image_model.load_state_dict(chest_model.state_dict())
        torch.save(chest_fusion.state_dict(), chest_fusion_pth)
        logger.info(f"Saved Chest X-ray fusion model checkpoint to {chest_fusion_pth}")

    # 2. Initialize Brain MRI Models (4 classes, 8 symptoms)
    if not brain_img_pth.exists() or not brain_fusion_pth.exists():
        logger.info("Initializing Brain MRI DenseNet-121 and Fusion checkpoints...")
        try:
            brain_model = DenseNet121Medical(num_classes=len(BRAIN_MRI_CLASSES), pretrained=True)
        except Exception as e:
            logger.warning(f"Could not load online pretrained weights ({e}), initializing architecture with He/Kaiming weights.")
            brain_model = DenseNet121Medical(num_classes=len(BRAIN_MRI_CLASSES), pretrained=False)

        # Save image model weights
        torch.save(brain_model.state_dict(), brain_img_pth)
        logger.info(f"Saved Brain MRI image model checkpoint to {brain_img_pth}")

        # Initialize late-fusion model and copy image backbone weights
        brain_fusion = MultimodalFusionModel(num_classes=len(BRAIN_MRI_CLASSES), num_symptoms=8)
        brain_fusion.image_model.load_state_dict(brain_model.state_dict())
        torch.save(brain_fusion.state_dict(), brain_fusion_pth)
        logger.info(f"Saved Brain MRI fusion model checkpoint to {brain_fusion_pth}")

    return {
        "chest_image": str(chest_img_pth),
        "chest_fusion": str(chest_fusion_pth),
        "brain_image": str(brain_img_pth),
        "brain_fusion": str(brain_fusion_pth),
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = initialize_weights_if_missing()
    print("Checkpoint initialization complete:", res)
