import os
import gc
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import torch.nn as nn

from app.core.config import settings, PROJECT_ROOT, BACKEND_DIR, CHEST_XRAY_CLASSES, BRAIN_MRI_CLASSES
from app.ml.fusion import DenseNet121Medical, MultimodalFusionModel
from app.ml.gradcam import GradCAM

logger = logging.getLogger("medical_assistant.model_loader")

class ModelManager:
    """
    Singleton manager providing memory-conscious, lazy-loaded PyTorch inference.
    Engineered for memory-constrained production environments (<= 512 MiB RAM).

    Architectural guarantees:
    1. Zero pre-warming at startup (models loaded only when inference is requested).
    2. Single-modality residency: at most 1 modality resident in RAM at any time.
       Switching modalities automatically evicts the previous model and invokes gc.collect().
    3. Shared image backbone: MultimodalFusionModel contains DenseNet121Medical.
       Grad-CAM and image-only inference reuse this single instance, eliminating
       duplicate 1024-d DenseNet feature extractors.
    4. Strict checkpoint validation: Missing checkpoints immediately raise FileNotFoundError.
       Never generates or initializes synthetic/random replacement weights.
    """
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.device = self._resolve_device()
        self._active_modality: Optional[str] = None
        self._active_bundle: Optional[Dict[str, Any]] = None

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

    def resolve_checkpoint_path(
        self,
        modality: str,
        filename: str,
        configured_path_str: Optional[str] = None
    ) -> Path:
        """
        Discovers pre-trained checkpoint across configurable paths without synthetic weight creation.
        """
        candidates = []
        if configured_path_str and configured_path_str.strip():
            candidates.append(Path(configured_path_str.strip()))

        base_dir = settings.MODEL_BASE_DIR or os.getenv("MODEL_BASE_DIR")
        if base_dir and base_dir.strip():
            candidates.append(Path(base_dir.strip()) / modality / filename)
            candidates.append(Path(base_dir.strip()) / filename)

        rel_path = f"{modality}/{filename}"
        candidates.append(PROJECT_ROOT / "models" / rel_path)
        candidates.append(BACKEND_DIR / "models_ml" / rel_path)
        candidates.append(BACKEND_DIR / "models" / rel_path)
        candidates.append(PROJECT_ROOT / "models_ml" / rel_path)

        for p in candidates:
            if p.exists() and p.is_file():
                return p.resolve()

        error_msg = (
            f"Required model checkpoint '{filename}' for modality '{modality}' was not found.\n"
            f"Checked paths:\n" + "\n".join(f" - {c}" for c in candidates) +
            "\n\nCRITICAL: Automatic weight initialization is strictly prohibited in production.\n"
            "Please ensure trained checkpoints are present or configure MODEL_BASE_DIR."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    def verify_checkpoints_exist(self, raise_error: bool = True) -> bool:
        """
        Lightweight existence check for all trained checkpoints on disk.
        Executes in <2ms with zero RAM allocation.
        """
        required = [
            ("chest_xray", "densenet121_chest.pth", settings.CHEST_IMAGE_MODEL_PATH),
            ("chest_xray", "fusion_chest.pth", settings.CHEST_FUSION_MODEL_PATH),
            ("brain_mri", "densenet121_brain.pth", settings.BRAIN_IMAGE_MODEL_PATH),
            ("brain_mri", "fusion_brain.pth", settings.BRAIN_FUSION_MODEL_PATH),
        ]
        for modality, filename, custom_path in required:
            try:
                self.resolve_checkpoint_path(modality, filename, custom_path)
            except FileNotFoundError:
                if raise_error:
                    raise
                return False
        return True

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

    def unload_active_modality(self):
        """Releases the currently resident modality from memory and runs garbage collection."""
        if self._active_bundle is not None:
            logger.info(f"Unloading modality '{self._active_modality}' from resident memory...")
            gradcam: Optional[GradCAM] = self._active_bundle.get("gradcam")
            if gradcam:
                gradcam.remove_hooks()
            self._active_bundle = None
            self._active_modality = None
            gc.collect()
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

    def get_modality_bundle(self, modality: str) -> Dict[str, Any]:
        """
        Retrieves or lazy-loads the active modality bundle (fusion_model, image_model, gradcam).
        Reuses the image backbone inside MultimodalFusionModel to halve RAM consumption.
        """
        if self._active_modality == modality and self._active_bundle is not None:
            return self._active_bundle

        # Evict currently resident modality to preserve 512 MiB limit
        if self._active_modality is not None and self._active_modality != modality:
            self.unload_active_modality()

        logger.info(f"Lazy-loading PyTorch models for modality '{modality}' into resident memory...")
        if modality == "chest_xray":
            classes = CHEST_XRAY_CLASSES
            fusion_file = "fusion_chest.pth"
            custom_fusion = settings.CHEST_FUSION_MODEL_PATH
        elif modality == "brain_mri":
            classes = BRAIN_MRI_CLASSES
            fusion_file = "fusion_brain.pth"
            custom_fusion = settings.BRAIN_FUSION_MODEL_PATH
        else:
            raise ValueError(f"Unsupported modality '{modality}'")

        fusion_path = self.resolve_checkpoint_path(modality, fusion_file, custom_fusion)
        fusion_model = MultimodalFusionModel(num_classes=len(classes), num_symptoms=8).to(self.device)
        fusion_ckpt = self._load_checkpoint(fusion_path)
        self._apply_weights(fusion_model, fusion_ckpt)
        fusion_model.eval()

        # Shared image backbone - eliminates duplicate DenseNet instance in RAM
        image_model = fusion_model.image_model
        image_model.eval()

        # Attach GradCAM to DenseNet121's last dense block layer
        target_layer = image_model.features.denseblock4.denselayer16.conv2
        gradcam = GradCAM(image_model, target_layer)

        self._active_bundle = {
            "image_model": image_model,
            "fusion_model": fusion_model,
            "gradcam": gradcam
        }
        self._active_modality = modality
        logger.info(f"Modality '{modality}' successfully resident in memory.")
        return self._active_bundle

    def get_active_modality(self) -> Optional[str]:
        return self._active_modality

    def is_ready(self) -> bool:
        """Returns True if all required model checkpoints are available on disk."""
        return self.verify_checkpoints_exist(raise_error=False)

    # Backward compatibility properties for test suites
    @property
    def chest_image_model(self) -> DenseNet121Medical:
        return self.get_modality_bundle("chest_xray")["image_model"]

    @property
    def chest_fusion_model(self) -> MultimodalFusionModel:
        return self.get_modality_bundle("chest_xray")["fusion_model"]

    @property
    def chest_gradcam(self) -> GradCAM:
        return self.get_modality_bundle("chest_xray")["gradcam"]

    @property
    def brain_image_model(self) -> DenseNet121Medical:
        return self.get_modality_bundle("brain_mri")["image_model"]

    @property
    def brain_fusion_model(self) -> MultimodalFusionModel:
        return self.get_modality_bundle("brain_mri")["fusion_model"]

    @property
    def brain_gradcam(self) -> GradCAM:
        return self.get_modality_bundle("brain_mri")["gradcam"]

def get_model_manager() -> ModelManager:
    """Returns singleton ModelManager without triggering memory-heavy model prewarming."""
    return ModelManager.get_instance()
