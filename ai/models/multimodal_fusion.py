"""
=============================================================================
1292-D Multimodal Feature Fusion Network (Prototype) - ChildNutri AI
=============================================================================
Combines:
  • 1280-D Deep Visual Embeddings (from EfficientNet-B0 infant photo analysis)
  • 12-D Clinical Anthropometric Measurements (Age, Gender, Wt, Ht, MUAC, Ratios)
Total Input Vector: 1292-Dimensional Multimodal Representation (1280 + 12).

Outputs:
  • Multi-class Malnutrition Classification (Normal, Severe (SAM), Stunted, Underweight, Wasted)
  • Continuous Malnutrition Risk Score (0.0 - 100.0)
  • Modality Contribution Gating Weights (Image Weight vs Clinical Data Weight)

NOTE: This multimodal fusion model is an experimental architectural prototype.
In clinical production without photographic inputs, the Soft-Voting Tabular
Ensemble is the validated production screening model.
=============================================================================
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Tuple

class MultimodalFusionNetwork1292D(nn.Module):
    """
    1292-Dimensional Multimodal Neural Network for Integrated Pediatric Screening.
    Fuses deep visual features (1280-D) and 12-D clinical measurements (1280 + 12 = 1292-D).
    """
    def __init__(self, visual_dim: int = 1280, anthro_dim: int = 12, num_classes: int = 5):
        super(MultimodalFusionNetwork1292D, self).__init__()
        
        self.visual_dim = visual_dim
        self.anthro_dim = anthro_dim
        self.total_dim = visual_dim + anthro_dim  # 1280 + 12 = 1292

        # 1. Visual Feature Compression & Normalization (1280 -> 128)
        self.visual_proj = nn.Sequential(
            nn.Linear(visual_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.2)
        )

        # 2. Anthropometric Projection (12 -> 32)
        self.anthro_proj = nn.Sequential(
            nn.Linear(anthro_dim, 32),
            nn.LayerNorm(32),
            nn.GELU(),
            nn.Dropout(0.1)
        )

        # 3. Cross-Modal Attention Gating (Learns which modality to trust more per sample)
        self.gate_layer = nn.Sequential(
            nn.Linear(128 + 32, 2),
            nn.Softmax(dim=-1)
        )

        # 4. Joint Multimodal Fusion MLP (160 -> 256 -> 128 -> 64)
        self.fusion_mlp = nn.Sequential(
            nn.Linear(128 + 32, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.25),
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(128, 64),
            nn.GELU()
        )

        # 5. Multi-Task Output Heads
        # Head A: 5-Class Diagnostic Classification
        self.classifier_head = nn.Linear(64, num_classes)
        # Head B: Continuous 0-100 Risk Score Regression
        self.risk_score_head = nn.Sequential(
            nn.Linear(64, 1),
            nn.Sigmoid()  # Multiplied by 100 in forward
        )

    def forward(self, visual_feats: torch.Tensor, anthro_feats: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        visual_feats: (B, 1280)
        anthro_feats: (B, 12) or (B, anthro_dim)
        """
        if anthro_feats.shape[1] != self.anthro_dim:
            if anthro_feats.shape[1] > self.anthro_dim:
                anthro_feats = anthro_feats[:, :self.anthro_dim]

        v_proj = self.visual_proj(visual_feats)   # (B, 128)
        a_proj = self.anthro_proj(anthro_feats)   # (B, 32)

        # Concat features (160-D fused representation)
        fused_raw = torch.cat([v_proj, a_proj], dim=-1) # (B, 160)

        # Calculate modality gating weights (e.g. 70% clinical data, 30% image)
        modality_weights = self.gate_layer(fused_raw) # (B, 2)
        v_weighted = v_proj * modality_weights[:, 0:1]
        a_weighted = a_proj * modality_weights[:, 1:2]

        fused_weighted = torch.cat([v_weighted, a_weighted], dim=-1)

        # Process through Fusion MLP
        hidden = self.fusion_mlp(fused_weighted) # (B, 64)

        logits = self.classifier_head(hidden)     # (B, 5)
        risk_pct = self.risk_score_head(hidden) * 100.0 # (B, 1)

        return {
            "logits": logits,
            "risk_score": risk_pct,
            "modality_weights": modality_weights, # [visual_contrib, clinical_contrib]
            "fused_representation": hidden
        }

# Backward compatibility alias
MultimodalFusionNetwork1285D = MultimodalFusionNetwork1292D

if __name__ == "__main__":
    model = MultimodalFusionNetwork1292D(visual_dim=1280, anthro_dim=12, num_classes=5)
    v_in = torch.randn(4, 1280)
    a_in = torch.randn(4, 12)
    out = model(v_in, a_in)
    print("1292-D Multimodal Fusion Network Test:")
    print("  Input: Visual (4, 1280) + Anthro (4, 12) = 1292-D")
    print("  Logits Output Shape:     ", out["logits"].shape)
    print("  Risk Score Output (0-100):", out["risk_score"].squeeze().tolist())
    print("  Modality Weights:        ", out["modality_weights"][0].tolist())
