import torch
import torch.nn as nn
import torchvision.models as models
from typing import Dict, List, Any, Tuple

class SymptomMLP(nn.Module):
    """
    Multilayer Perceptron to embed structured symptom feature vectors.
    Maps binary symptom indicators into a dense semantic representation.
    """
    def __init__(self, num_symptoms: int = 8, hidden_dim: int = 32, embedding_dim: int = 16):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(num_symptoms, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, embedding_dim),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class DenseNet121Medical(nn.Module):
    """
    DenseNet-121 Transfer Learning model for Medical Imaging.
    Exposes both convolutional feature embeddings and class logits.
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = False):
        super().__init__()
        weights = models.DenseNet121_Weights.DEFAULT if pretrained else None
        densenet = models.densenet121(weights=weights)
        self.features = densenet.features
        num_features = densenet.classifier.in_features  # 1024
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(num_features, num_classes)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        out = nn.functional.relu(features, inplace=True)
        out = self.pool(out)
        out = torch.flatten(out, 1)
        return out

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.extract_features(x)
        logits = self.classifier(features)
        return logits


class MultimodalFusionModel(nn.Module):
    """
    Late-Fusion Multimodal Architecture.
    Combines high-level visual features from DenseNet-121 with
    symptom embeddings from the SymptomMLP to generate comprehensive multimodal predictions.
    """
    def __init__(self, num_classes: int, num_symptoms: int = 8, symptom_emb_dim: int = 16):
        super().__init__()
        self.num_classes = num_classes
        self.image_model = DenseNet121Medical(num_classes=num_classes, pretrained=False)
        self.symptom_mlp = SymptomMLP(num_symptoms=num_symptoms, embedding_dim=symptom_emb_dim)

        fusion_in_dim = 1024 + symptom_emb_dim
        self.fusion_head = nn.Sequential(
            nn.Linear(fusion_in_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, image: torch.Tensor, symptoms: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            - image_logits: torch.Tensor of shape (batch, num_classes)
            - fusion_logits: torch.Tensor of shape (batch, num_classes)
        """
        img_features = self.image_model.extract_features(image)
        image_logits = self.image_model.classifier(img_features)
        symptom_emb = self.symptom_mlp(symptoms)
        fused_features = torch.cat([img_features, symptom_emb], dim=1)
        fusion_logits = self.fusion_head(fused_features)
        return image_logits, fusion_logits


def build_symptom_tensor(symptoms_dict: Dict[str, Any], symptom_order: List[str], device: torch.device) -> torch.Tensor:
    """
    Converts a dictionary of symptom keys to a deterministic 2D float tensor matching the required model order.
    """
    vec = [1.0 if bool(symptoms_dict.get(key, False)) else 0.0 for key in symptom_order]
    tensor = torch.tensor([vec], dtype=torch.float32, device=device)
    return tensor
