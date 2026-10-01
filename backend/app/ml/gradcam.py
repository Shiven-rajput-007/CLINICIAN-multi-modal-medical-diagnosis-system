import io
import base64
from typing import Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn as nn

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM) for DenseNet-121.
    Computes visual explainability heatmaps highlighting the anatomical regions
    influencing the neural network's diagnosis.
    Target layer: DenseNet-121 last dense block conv layer (model.features.denseblock4.denselayer16.conv2).
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self.hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self.hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: Optional[int] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Generates a 2D normalized Grad-CAM heatmap for the specified target class.
        """
        self.model.eval()
        input_tensor = input_tensor.clone().detach().requires_grad_(True)

        # Forward pass
        logits = self.model(input_tensor)

        if target_class_idx is None:
            target_class_idx = int(torch.argmax(logits, dim=1).item())

        score = logits[0, target_class_idx]

        # Backward pass to get gradients
        self.model.zero_grad()
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed to capture gradients or activations.")

        # Global average pooling of gradients: shape (1, C, 1, 1)
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)

        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)

        # Apply ReLU to retain only positive contributions
        cam = torch.relu(cam)

        # Normalize to [0, 1]
        cam_min = torch.min(cam)
        cam_max = torch.max(cam)
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)

        heatmap = cam.squeeze().cpu().detach().numpy()
        return heatmap, target_class_idx

    def overlay_on_image(
        self,
        heatmap: np.ndarray,
        original_image: Image.Image,
        alpha: float = 0.45,
        colormap_name: str = "jet"
    ) -> Image.Image:
        """
        Resizes heatmap to original image size, applies colormap, and blends with scan.
        """
        orig_w, orig_h = original_image.size

        # Resize heatmap to match image dimensions
        heatmap_pil = Image.fromarray((heatmap * 255).astype(np.uint8))
        heatmap_resized = heatmap_pil.resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)
        heatmap_norm = np.array(heatmap_resized).astype(np.float32) / 255.0

        # Apply Matplotlib colormap
        try:
            import matplotlib
            cmap = matplotlib.colormaps[colormap_name]
        except Exception:
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap(colormap_name)
        heatmap_colored = cmap(heatmap_norm)[:, :, :3]  # (H, W, 3) in [0, 1]
        heatmap_colored_uint8 = (heatmap_colored * 255).astype(np.uint8)

        # Convert original image to RGB numpy array
        original_np = np.array(original_image.convert("RGB"))

        # Blend original scan with heatmap
        blended = (1.0 - alpha) * original_np.astype(np.float32) + alpha * heatmap_colored_uint8.astype(np.float32)
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        return Image.fromarray(blended)

    def generate_base64_overlay(
        self,
        input_tensor: torch.Tensor,
        original_image: Image.Image,
        target_class_idx: Optional[int] = None,
        alpha: float = 0.45
    ) -> str:
        """
        Generates Grad-CAM, overlays it on original image, and returns a Base64 PNG data URL.
        """
        heatmap, _ = self.generate_heatmap(input_tensor, target_class_idx)
        overlay_pil = self.overlay_on_image(heatmap, original_image, alpha=alpha)

        buffer = io.BytesIO()
        overlay_pil.save(buffer, format="PNG", optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def remove_hooks(self):
        for hook in self.hooks:
            hook.remove()
        self.hooks.clear()
