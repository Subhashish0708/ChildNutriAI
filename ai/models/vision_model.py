"""
=============================================================================
EfficientNet-B0 Vision Models - ChildNutri AI
=============================================================================
Deep Learning Vision Architecture supporting:
  1. Real Indian Neonatal Anthropometric Regression (Multi-target continuous estimation)
     • Backbone: EfficientNet-B0 (Pretrained Transfer Learning)
     • Visual Embeddings: 1280-Dimensional Bottleneck Features
     • Regression Heads: Weight (g), Body Length (cm), Head Circumference (cm),
       Chest Girth (cm), Arm Length (cm), Leg Length (cm).
     • Subject-level Multi-image Feature Pooling.
  2. Pediatric Malnutrition Screening Classifier (Legacy 5-Class)
=============================================================================
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image

# Canonical regression targets
NEONATAL_TARGETS = [
    "weight_g",
    "body_length_cm",
    "head_circumference_cm",
    "chest_girth_cm",
    "arm_length_cm",
    "leg_length_cm"
]

# Baseline empirical prior centers for Indian neonates (for stable initialization)
EMPIRICAL_PRIORS = {
    "weight_g": 2400.0,
    "body_length_cm": 46.0,
    "head_circumference_cm": 31.0,
    "chest_girth_cm": 31.0,
    "arm_length_cm": 17.0,
    "leg_length_cm": 20.0
}


class EfficientNetB0NeonatalRegressor(nn.Module):
    """
    EfficientNet-B0 Multi-Target Regressor for Neonatal Anthropometric Estimation.
    Trained on authentic clinically acquired Indian neonatal photographs.
    Predicts continuous physical measurements with multi-task masked loss.
    """
    def __init__(self, pretrained: bool = True):
        super(EfficientNetB0NeonatalRegressor, self).__init__()

        # 1. Backbone Feature Extractor
        if pretrained:
            try:
                self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
            except Exception:
                self.backbone = models.efficientnet_b0(weights=None)
        else:
            self.backbone = models.efficientnet_b0(weights=None)

        # Freeze early stem layers for transfer learning stability
        for param in self.backbone.features[:3].parameters():
            param.requires_grad = False

        in_features = self.backbone.classifier[1].in_features  # 1280
        self.backbone.classifier = nn.Identity()

        # 2. Shared Multi-Task Projection Representation (1280 -> 256)
        self.shared_proj = nn.Sequential(
            nn.Dropout(0.30),
            nn.Linear(in_features, 256),
            nn.LayerNorm(256),
            nn.GELU()
        )

        # 3. Independent Task-Specific Regression Heads
        self.head_weight = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )
        self.head_body_length = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )
        self.head_head_cc = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )
        self.head_chest_girth = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )
        self.head_arm_length = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )
        self.head_leg_length = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1)
        )

        # Initialize output biases to empirical cohort priors for smooth convergence
        with torch.no_grad():
            self.head_weight[-1].bias.fill_(EMPIRICAL_PRIORS["weight_g"])
            self.head_body_length[-1].bias.fill_(EMPIRICAL_PRIORS["body_length_cm"])
            self.head_head_cc[-1].bias.fill_(EMPIRICAL_PRIORS["head_circumference_cm"])
            self.head_chest_girth[-1].bias.fill_(EMPIRICAL_PRIORS["chest_girth_cm"])
            self.head_arm_length[-1].bias.fill_(EMPIRICAL_PRIORS["arm_length_cm"])
            self.head_leg_length[-1].bias.fill_(EMPIRICAL_PRIORS["leg_length_cm"])

    def extract_visual_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts 1280-D visual embeddings from the EfficientNet bottleneck."""
        return self.backbone(x)

    def forward_from_features(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Runs shared projection and regression heads from 1280-D feature vectors."""
        h = self.shared_proj(features)
        return {
            "weight_g": self.head_weight(h).squeeze(-1),
            "body_length_cm": self.head_body_length(h).squeeze(-1),
            "head_circumference_cm": self.head_head_cc(h).squeeze(-1),
            "chest_girth_cm": self.head_chest_girth(h).squeeze(-1),
            "arm_length_cm": self.head_arm_length(h).squeeze(-1),
            "leg_length_cm": self.head_leg_length(h).squeeze(-1)
        }

    def forward(self, x: torch.Tensor) -> Tuple[Dict[str, torch.Tensor], torch.Tensor]:
        """
        Forward pass for a batch of images.
        x: (B, 3, 224, 224)
        Returns:
          (predictions_dict, visual_features_1280d)
        """
        features = self.extract_visual_features(x)
        preds = self.forward_from_features(features)
        return preds, features

    def aggregate_subject_features(self, image_tensors: torch.Tensor) -> Tuple[Dict[str, torch.Tensor], torch.Tensor]:
        """
        Aggregates multiple images belonging to the same baby via mean feature pooling.
        image_tensors: (K, 3, 224, 224) where K is the number of viewpoints/photos for the neonate.
        Returns:
          (aggregated_predictions_dict, pooled_1280d_feature)
        """
        if image_tensors.dim() == 3:
            image_tensors = image_tensors.unsqueeze(0)
        features = self.extract_visual_features(image_tensors)  # (K, 1280)
        pooled_feature = torch.mean(features, dim=0, keepdim=True)  # (1, 1280)
        preds = self.forward_from_features(pooled_feature)
        return preds, pooled_feature


class EfficientNetB0MalnutritionClassifier(nn.Module):
    """
    EfficientNet-B0 with Transfer Learning for visual malnutrition screening.
    Extracts 1280-D embeddings from infant facial/full-body photos.
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = True):
        super(EfficientNetB0MalnutritionClassifier, self).__init__()
        
        # Load backbone
        if pretrained:
            try:
                self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
            except Exception:
                self.backbone = models.efficientnet_b0(weights=None)
        else:
            self.backbone = models.efficientnet_b0(weights=None)

        # Freeze initial stages, keep higher stages fine-tunable
        for param in self.backbone.features[:4].parameters():
            param.requires_grad = False

        # Custom Pediatric Classification Head
        in_features = self.backbone.classifier[1].in_features  # 1280
        self.backbone.classifier = nn.Identity()  # Outputs 1280-D vector

        self.classifier_head = nn.Sequential(
            nn.Dropout(0.35),
            nn.Linear(in_features, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(256, num_classes)
        )

    def extract_visual_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extracts 1280-D visual embeddings for Multimodal Fusion Network.
        x: (B, 3, 224, 224)
        Returns: (B, 1280)
        """
        return self.backbone(x)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (logits, 1280-D visual features)
        """
        features = self.extract_visual_features(x)
        logits = self.classifier_head(features)
        return logits, features


class ResNet50MalnutritionClassifier(nn.Module):
    """
    ResNet-50 with Transfer Learning for visual malnutrition screening.
    Extracts 2048-D deep visual embeddings (or project to 1280-D).
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = True, output_dim: int = 1280):
        super(ResNet50MalnutritionClassifier, self).__init__()
        if pretrained:
            try:
                self.backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            except Exception:
                self.backbone = models.resnet50(weights=None)
        else:
            self.backbone = models.resnet50(weights=None)

        in_features = self.backbone.fc.in_features  # 2048
        self.backbone.fc = nn.Identity()

        # Projection layer to match unified multimodal embedding dimension (1280-D)
        self.proj = nn.Sequential(
            nn.Linear(in_features, output_dim),
            nn.LayerNorm(output_dim),
            nn.ReLU()
        )

        self.classifier_head = nn.Sequential(
            nn.Dropout(0.35),
            nn.Linear(output_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(256, num_classes)
        )

    def extract_visual_features(self, x: torch.Tensor) -> torch.Tensor:
        raw_feats = self.backbone(x)
        return self.proj(raw_feats)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.extract_visual_features(x)
        logits = self.classifier_head(features)
        return logits, features


def get_neonatal_regressor(pretrained: bool = True) -> EfficientNetB0NeonatalRegressor:
    """Factory to instantiate the Indian Neonatal Anthropometric Regressor."""
    return EfficientNetB0NeonatalRegressor(pretrained=pretrained)


def get_vision_model(model_name: str = "efficientnet", num_classes: int = 5, pretrained: bool = True) -> nn.Module:
    """
    Factory to return either EfficientNet-B0 or ResNet-50 visual model.
    """
    model_name = model_name.lower()
    if "regressor" in model_name or "neonatal" in model_name:
        return EfficientNetB0NeonatalRegressor(pretrained=pretrained)
    if "resnet" in model_name:
        return ResNet50MalnutritionClassifier(num_classes=num_classes, pretrained=pretrained)
    return EfficientNetB0MalnutritionClassifier(num_classes=num_classes, pretrained=pretrained)


if __name__ == "__main__":
    reg = EfficientNetB0NeonatalRegressor(pretrained=False)
    dummy = torch.randn(2, 3, 224, 224)
    preds, feats = reg(dummy)
    print("Neonatal Regressor Output:")
    print("  Visual features:", feats.shape)
    for k, v in preds.items():
        print(f"  {k}: shape {v.shape}, sample value {v[0].item():.2f}")

    # Test subject aggregation with 3 viewpoints
    dummy_multi = torch.randn(3, 3, 224, 224)
    agg_preds, agg_feat = reg.aggregate_subject_features(dummy_multi)
    print("Multi-image Subject Aggregation:")
    print("  Aggregated feature:", agg_feat.shape)
    for k, v in agg_preds.items():
        print(f"  Aggregated {k}: {v[0].item():.2f}")
