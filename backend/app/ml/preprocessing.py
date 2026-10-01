import io
from typing import Tuple
from PIL import Image
import torch
import torchvision.transforms as transforms

# Standard DenseNet121 ImageNet normalization statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_inference_transform(target_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(target_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

def preprocess_image(image_bytes: bytes, target_size: Tuple[int, int] = (224, 224)) -> Tuple[torch.Tensor, Image.Image]:
    """
    Validates, opens, and transforms an uploaded medical image for DenseNet-121 inference.
    Returns:
        - tensor: torch.Tensor of shape (1, 3, target_size[0], target_size[1])
        - original_image: PIL Image in RGB format
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image format: {str(e)}")

    transform = get_inference_transform(target_size)
    tensor = transform(pil_image)
    # Add batch dimension: (3, H, W) -> (1, 3, H, W)
    tensor = tensor.unsqueeze(0)
    return tensor, pil_image
