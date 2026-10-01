import logging
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import torch.nn as nn

from backend.app.core.config import settings, PROJECT_ROOT, BACKEND_DIR, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from backend.app.ml.fusion import DenseNet121Medical, MultimodalFusionModel
from backend.app.ml.gradcam import GradCAM
from backend.app.ml.weights_init import initialize_weights_if_missing

logger = logging.getLogger("medical_assistant.model_loader")

class ModelManager:
    """
    Singleton manager for loading, caching, and serving PyTorch diagnostic models.
    Keeps models resident in memory in eval mode to minimize inference latency.
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
        target = (settings.MODEL_DEVICE or "cpu").lower()
        if target in ("auto", "cuda") and torch.cuda.is_available():
            dev = torch.device("cuda")
            logger.info(f"Using GPU device: {torch.cuda.get_device_name(0)}")
        else:
            dev = torch.device("cpu")
            logger.info("Using CPU device for PyTorch inference.")
        return dev

    def _resolve_checkpoint_path(self, configured_path_str: Optional[str], fallback_rel_path: str) -> Path:
        """Finds checkpoint from configured path, or root models/, or backend/models_ml/."""
        candidates = []
        if configured_path_str and configured_path_str.strip():
            candidates.append(Path(configured_path_str))
        candidates.append(PROJECT_ROOT / "models" / fallback_rel_path)
        candidates.append(BACKEND_DIR / "models_ml" / fallback_rel_path)

        for p in candidates:
            if p.exists():
                return p

        # If none exist, trigger weight bootstrapper
        logger.info(f"Checkpoint not found in candidates {[str(c) for c in candidates]}. Initializing weights...")
        initialize_weights_if_missing()
        for p in candidates:
            if p.exists():
                return p

        raise FileNotFoundError(f"Model checkpoint for '{fallback_rel_path}' could not be resolved.")

    def _load_checkpoint(self, path: Path) -> Any:
        logger.info(f"Loading PyTorch checkpoint from: {path}")
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        return checkpoint

    def _apply_weights(self, model: nn.Module, checkpoint: Any):
        """Robustly loads state_dict from various checkpoint formats."""
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
        """Loads all modality image models and late-fusion models into memory and attaches Grad-CAM."""
        if self.models_loaded:
            return

        logger.info("Loading PyTorch diagnostic models into resident memory...")

        # 1. Chest X-Ray Models (5 classes)
        num_chest_classes = len(CHEST_XRAY_CLASSES)
        self.chest_image_model = DenseNet121Medical(num_classes=num_chest_classes, pretrained=False).to(self.device)
        chest_img_path = self._resolve_checkpoint_path(
            settings.CHEST_IMAGE_MODEL_PATH,
            "chest_xray/densenet121_chest.pth"
        )
        chest_ckpt = self._load_checkpoint(chest_img_path)
        self._apply_weights(self.chest_image_model, chest_ckpt)
        self.chest_image_model.eval()

        self.chest_fusion_model = MultimodalFusionModel(num_classes=num_chest_classes, num_symptoms=8).to(self.device)
        chest_fusion_path = self._resolve_checkpoint_path(
            settings.CHEST_FUSION_MODEL_PATH,
            "chest_xray/fusion_chest.pth"
        )
        chest_fusion_ckpt = self._load_checkpoint(chest_fusion_path)
        self._apply_weights(self.chest_fusion_model, chest_fusion_ckpt)
        self.chest_fusion_model.eval()

        # Attach GradCAM to DenseNet121's last dense block layer
        target_layer_chest = self.chest_image_model.features.denseblock4.denselayer16.conv2
        self.chest_gradcam = GradCAM(self.chest_image_model, target_layer_chest)

        # 2. Brain MRI Models (4 classes)
        num_brain_classes = len(BRAIN_MRI_CLASSES)
        self.brain_image_model = DenseNet121Medical(num_classes=num_brain_classes, pretrained=False).to(self.device)
        brain_img_path = self._resolve_checkpoint_path(
            settings.BRAIN_IMAGE_MODEL_PATH,
            "brain_mri/densenet121_brain.pth"
        )
        brain_ckpt = self._load_checkpoint(brain_img_path)
        self._apply_weights(self.brain_image_model, brain_ckpt)
        self.brain_image_model.eval()

        self.brain_fusion_model = MultimodalFusionModel(num_classes=num_brain_classes, num_symptoms=8).to(self.device)
        brain_fusion_path = self._resolve_checkpoint_path(
            settings.BRAIN_FUSION_MODEL_PATH,
            "brain_mri/fusion_brain.pth"
        )
        brain_fusion_ckpt = self._load_checkpoint(brain_fusion_path)
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
