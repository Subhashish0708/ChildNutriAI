"""
=============================================================================
Unsupervised Machine Learning & Anomaly Detection - ChildNutri AI
=============================================================================
Includes:
  1. PyTorch Anthropometric Autoencoder (Anomaly Detection for Unusual Growth Profiles)
  2. K-Means Clustering (Nutritional-Risk Group Discovery & Phenotyping)
=============================================================================
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.cluster import KMeans
from typing import Dict, Any, Tuple

# =============================================================================
# 1. PYTORCH ANTHROPOMETRIC AUTOENCODER
# =============================================================================
class AnthropometricAutoencoder(nn.Module):
    """
    Autoencoder for detecting anomalous or fabricated measurement combinations.
    Encoder: 12-D -> 8-D -> 4-D Latent Bottleneck
    Decoder: 4-D -> 8-D -> 12-D Reconstructed Profile
    """
    def __init__(self, in_features: int = 12, latent_dim: int = 4):
        super(AnthropometricAutoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(in_features, 8),
            nn.LayerNorm(8),
            nn.GELU(),
            nn.Linear(8, latent_dim),
            nn.GELU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 8),
            nn.LayerNorm(8),
            nn.GELU(),
            nn.Linear(8, in_features)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent

    def compute_anomaly_score(self, x: torch.Tensor, threshold: float = 0.45) -> Dict[str, Any]:
        """
        Computes reconstruction MSE. If MSE > threshold, flags anomalous pattern.
        """
        self.eval()
        with torch.no_grad():
            recon, _ = self.forward(x)
            mse = torch.mean((x - recon) ** 2, dim=1).item()

        is_anomaly = (mse > threshold)
        return {
            "reconstruction_error_mse": round(mse, 4),
            "is_anomalous": is_anomaly,
            "interpretation": "Unusual / Conflicting Measurement Pattern (Verify measurements)" if is_anomaly else "Standard Physiological Pattern"
        }


# =============================================================================
# 2. K-MEANS NUTRITIONAL CLUSTERING
# =============================================================================
class NutritionalKMeansClusterer:
    """
    Unsupervised cohort phenotyping into 4 clusters:
      • Cluster 0: Thriving Normal Cohort
      • Cluster 1: Chronic Stunted (Linear Deficit)
      • Cluster 2: Acute Wasted (Mass Deficit)
      • Cluster 3: Critical Multi-Axis SAM
    """
    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        self.cluster_labels = {
            0: "Cohort A: Thriving & Normal Growth",
            1: "Cohort B: Chronic Stunted (Linear Deficit)",
            2: "Cohort C: Acute Wasted (Wasting / Low MUAC)",
            3: "Cohort D: Critical Multi-Axis Severe Malnutrition (SAM)"
        }

    def fit(self, X: np.ndarray):
        self.kmeans.fit(X)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return self.kmeans.predict(X)

    def predict_cluster(self, X: np.ndarray) -> Dict[str, Any]:
        if X.ndim == 1:
            X = X.reshape(1, -1)
        cid = int(self.kmeans.predict(X)[0])
        dist = float(np.min(self.kmeans.transform(X)))
        return {
            "cluster_id": cid,
            "cohort_name": self.cluster_labels.get(cid, f"Cohort {cid}"),
            "distance_to_cluster_center": round(dist, 3)
        }

if __name__ == "__main__":
    ae = AnthropometricAutoencoder(in_features=12)
    t = torch.randn(1, 12)
    score = ae.compute_anomaly_score(t)
    print("Autoencoder Anomaly Test:", score)
