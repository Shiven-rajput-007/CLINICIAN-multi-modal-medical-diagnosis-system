import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn as nn
from backend.config import settings, BASE_DIR, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from backend.ml.fusion import DenseNet121Medical, MultimodalFusionModel
from backend.ml.gradcam import GradCAM
from backend.ml.weights_init import initialize_weights_if_missing

logger = logging.getLogger("medical_assistant.loader")

class ModelManager:
    """
    Singleton manager for loading, caching, and serving PyTorch diagnostic models.
    Prevents repeated disk I/O and keeps models resident in memory in eval mode.
    """
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.device = self._resolve_device()
        self.models_loaded = False

        # Chest X-ray models
        self.chest_image_model: Optional[DenseNet121Medical] = None
        self.chest_fusion_model: Optional[MultimodalFusionModel] = None
        self.chest_gradcam: Optional[GradCAM] = None

        # Brain MRI models
        self.brain_image_model: Optional[DenseNet121Medical] = None
        self.brain_fusion_model: Optional[MultimodalFusionModel] = None
        self.brain_gradcam: Optional[GradCAM] = None

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def _resolve_device(self) -> torch.device:
        target = settings.DEVICE.lower()
        if target in ("auto", "cuda") and torch.cuda.is_available():
            dev = torch.device("cuda")
            logger.info(f"Using GPU device: {torch.cuda.get_device_name(0)}")
        else:
            dev = torch.device("cpu")
            logger.info("Using CPU device for inference.")
        return dev

    def _load_checkpoint(self, path_str: Optional[str], default_path: Path) -> Any:
        checkpoint_path = Path(path_str) if (path_str and path_str.strip()) else default_path
        if not checkpoint_path.exists():
            logger.info(f"Checkpoint not found at {checkpoint_path}. Running weight initialization...")
            initialize_weights_if_missing()
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Model checkpoint could not be resolved at {checkpoint_path}")

        logger.info(f"Loading checkpoint from: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        return checkpoint

    def _apply_weights(self, model: nn.Module, checkpoint: Any):
        """Robustly extracts state_dict from various checkpoint formats."""
        if isinstance(checkpoint, nn.Module):
            model.load_state_dict(checkpoint.state_dict())
        elif isinstance(checkpoint, dict):
            if "state_dict" in checkpoint:
                model.load_state_dict(checkpoint["state_dict"])
            elif "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            else:
                model.load_state_dict(checkpoint)
        else:
            raise ValueError(f"Unrecognized checkpoint format: {type(checkpoint)}")

    def load_all_models(self):
        """Loads all modality image and late-fusion models into memory and registers Grad-CAM."""
        if self.models_loaded:
            return

        logger.info("Starting PyTorch model loading...")
        chest_dir = BASE_DIR / "backend" / "models_ml" / "chest_xray"
        brain_dir = BASE_DIR / "backend" / "models_ml" / "brain_mri"

        # 1. Chest X-Ray Models (5 classes)
        num_chest_classes = len(CHEST_XRAY_CLASSES)
        self.chest_image_model = DenseNet121Medical(num_classes=num_chest_classes, pretrained=False).to(self.device)
        chest_ckpt = self._load_checkpoint(settings.CHEST_IMAGE_MODEL_PATH, chest_dir / "densenet121_chest.pth")
        self._apply_weights(self.chest_image_model, chest_ckpt)
        self.chest_image_model.eval()

        self.chest_fusion_model = MultimodalFusionModel(num_classes=num_chest_classes, num_symptoms=8).to(self.device)
        chest_fusion_ckpt = self._load_checkpoint(settings.CHEST_FUSION_MODEL_PATH, chest_dir / "fusion_chest.pth")
        self._apply_weights(self.chest_fusion_model, chest_fusion_ckpt)
        self.chest_fusion_model.eval()

        # Attach GradCAM to DenseNet121's last dense block layer
        target_layer_chest = self.chest_image_model.features.denseblock4.denselayer16.conv2
        self.chest_gradcam = GradCAM(self.chest_image_model, target_layer_chest)

        # 2. Brain MRI Models (4 classes)
        num_brain_classes = len(BRAIN_MRI_CLASSES)
        self.brain_image_model = DenseNet121Medical(num_classes=num_brain_classes, pretrained=False).to(self.device)
        brain_ckpt = self._load_checkpoint(settings.BRAIN_IMAGE_MODEL_PATH, brain_dir / "densenet121_brain.pth")
        self._apply_weights(self.brain_image_model, brain_ckpt)
        self.brain_image_model.eval()

        self.brain_fusion_model = MultimodalFusionModel(num_classes=num_brain_classes, num_symptoms=8).to(self.device)
        brain_fusion_ckpt = self._load_checkpoint(settings.BRAIN_FUSION_MODEL_PATH, brain_dir / "fusion_brain.pth")
        self._apply_weights(self.brain_fusion_model, brain_fusion_ckpt)
        self.brain_fusion_model.eval()

        target_layer_brain = self.brain_image_model.features.denseblock4.denselayer16.conv2
        self.brain_gradcam = GradCAM(self.brain_image_model, target_layer_brain)

        self.models_loaded = True
        logger.info("All PyTorch diagnostic models successfully loaded and ready for inference.")

    def is_ready(self) -> bool:
        return self.models_loaded

def get_model_manager() -> ModelManager:
    manager = ModelManager.get_instance()
    if not manager.is_ready():
        manager.load_all_models()
    return manager
