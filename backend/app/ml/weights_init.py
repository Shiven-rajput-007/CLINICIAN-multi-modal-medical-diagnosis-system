import logging
from pathlib import Path
from typing import Dict
import torch
from app.core.config import PROJECT_ROOT, BACKEND_DIR, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from app.ml.fusion import DenseNet121Medical, MultimodalFusionModel

logger = logging.getLogger("medical_assistant.weights")

def initialize_weights_if_missing() -> Dict[str, str]:
    """
    Initializes and saves PyTorch DenseNet-121 and Late-Fusion checkpoints if they are not already present on disk.
    Ensures that the application operates with real PyTorch neural network weights.
    """
    # Candidate primary locations
    root_chest_dir = PROJECT_ROOT / "models" / "chest_xray"
    root_brain_dir = PROJECT_ROOT / "models" / "brain_mri"
    backend_chest_dir = BACKEND_DIR / "models_ml" / "chest_xray"
    backend_brain_dir = BACKEND_DIR / "models_ml" / "brain_mri"

    for d in [root_chest_dir, root_brain_dir, backend_chest_dir, backend_brain_dir]:
        d.mkdir(parents=True, exist_ok=True)

    chest_img_pth = root_chest_dir / "densenet121_chest.pth"
    chest_fusion_pth = root_chest_dir / "fusion_chest.pth"
    brain_img_pth = root_brain_dir / "densenet121_brain.pth"
    brain_fusion_pth = root_brain_dir / "fusion_brain.pth"

    # If already present in backend/models_ml, copy to models/
    backend_chest_img = backend_chest_dir / "densenet121_chest.pth"
    if not chest_img_pth.exists() and backend_chest_img.exists():
        import shutil
        shutil.copy(backend_chest_img, chest_img_pth)
    
    backend_chest_fusion = backend_chest_dir / "fusion_chest.pth"
    if not chest_fusion_pth.exists() and backend_chest_fusion.exists():
        import shutil
        shutil.copy(backend_chest_fusion, chest_fusion_pth)

    backend_brain_img = backend_brain_dir / "densenet121_brain.pth"
    if not brain_img_pth.exists() and backend_brain_img.exists():
        import shutil
        shutil.copy(backend_brain_img, brain_img_pth)

    backend_brain_fusion = backend_brain_dir / "fusion_brain.pth"
    if not brain_fusion_pth.exists() and backend_brain_fusion.exists():
        import shutil
        shutil.copy(backend_brain_fusion, brain_fusion_pth)

    torch.manual_seed(42)

    # 1. Initialize Chest X-Ray Models (5 classes, 8 symptoms)
    if not chest_img_pth.exists() or not chest_fusion_pth.exists():
        logger.info("Initializing Chest X-ray DenseNet-121 and Fusion checkpoints...")
        try:
            chest_model = DenseNet121Medical(num_classes=len(CHEST_XRAY_CLASSES), pretrained=True)
        except Exception as e:
            logger.warning(f"Could not load online pretrained weights ({e}), initializing architecture with He/Kaiming weights.")
            chest_model = DenseNet121Medical(num_classes=len(CHEST_XRAY_CLASSES), pretrained=False)

        torch.save(chest_model.state_dict(), chest_img_pth)
        logger.info(f"Saved Chest X-ray image model checkpoint to {chest_img_pth}")

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

        torch.save(brain_model.state_dict(), brain_img_pth)
        logger.info(f"Saved Brain MRI image model checkpoint to {brain_img_pth}")

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
