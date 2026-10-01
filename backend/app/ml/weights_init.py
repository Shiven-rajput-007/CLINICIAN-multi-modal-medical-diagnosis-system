"""
Weight initialization module.
NOTE: In production, training or synthetic weight initialization at runtime is strictly disabled.
Pre-trained checkpoints must be present on disk in models/ or at MODEL_BASE_DIR.
"""
from typing import Dict

def initialize_weights_if_missing() -> Dict[str, str]:
    """
    Guards against automatic synthetic/random weight initialization.
    """
    raise RuntimeError(
        "Automated weight initialization at runtime is strictly disabled in production.\n"
        "The application requires real pre-trained PyTorch checkpoints.\n"
        "Ensure densenet121_chest.pth, fusion_chest.pth, densenet121_brain.pth, and fusion_brain.pth "
        "exist in models/ or set MODEL_BASE_DIR."
    )
