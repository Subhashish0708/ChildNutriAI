"""
ChildNutri AI - Indian Neonatal Anthropometric Regression Training & Evaluation
================================================================================
Trains and benchmarks the EfficientNet-B0 multi-target anthropometric regressor
using the clinically acquired Indian Neonatal Anthropometric Image Dataset.

Data Origin:
  - Combined District Hospital, Manjhanpur, Kaushambi, UP, India
  - Madhuraj Hospital, Kanpur, UP, India
Authors: Anurag Singh & Dr. Rashi Agarwal (© 2026)

Key Methodological Guarantees:
  1. Patient-Level Splitting: Strictly trained on the subject-level train split
     (zero leakage of patient images to val/test splits).
  2. Multi-Target Masked Loss: Missing values (e.g., Chest Girth NA) are masked out
     during loss computation without artificial imputation.
  3. Comprehensive Evaluation: Evaluated on the held-out subject-level test split
     using MAE, RMSE, R², and Median Absolute Error.
  4. Artifact Export: Saves trained weights to ai/models/neonatal_regressor.pth and
     metrics to ai/models/neonatal_regression_metrics.json.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.data.indian_neonatal_dataset import (
    IndianNeonatalDatasetAdapter,
    IndianNeonatalVisionDataset,
    IndianNeonatalSubjectAggregatedDataset,
    ALL_REGRESSION_TARGETS,
    TARGET_SCALING
)
from ai.models.vision_model import EfficientNetB0NeonatalRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("childnutri.train_neonatal")


def compute_masked_loss(
    preds: Dict[str, torch.Tensor],
    targets: Dict[str, torch.Tensor],
    masks: Dict[str, torch.Tensor]
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Computes scale-normalized multi-target MSE loss ignoring missing (masked) values.
    """
    total_loss = torch.tensor(0.0, device=list(preds.values())[0].device)
    component_losses: Dict[str, float] = {}
    valid_tasks = 0

    for target_name in ALL_REGRESSION_TARGETS:
        p = preds[target_name].squeeze()
        t = targets[target_name].squeeze()
        m = masks[target_name].squeeze()

        if m.sum() > 0:
            valid_p = p[m.bool()]
            valid_t = t[m.bool()]
            mse = torch.mean((valid_p - valid_t) ** 2)
            # Scale-normalize by standard deviation squared so gram scale doesn't drown cm scale
            std_val = TARGET_SCALING[target_name]["std"]
            norm_factor = 1.0 / (std_val ** 2)
            scaled_mse = mse * norm_factor

            total_loss = total_loss + scaled_mse
            component_losses[target_name] = float(mse.item())
            valid_tasks += 1

    if valid_tasks > 0:
        total_loss = total_loss / valid_tasks

    return total_loss, component_losses


def evaluate_regressor(
    model: nn.Module,
    dataloader: DataLoader
) -> Dict[str, Any]:
    """
    Evaluates regressor on a given dataloader, returning MAE, RMSE, R2, MedAE for each target.
    """
    model.eval()
    all_preds: Dict[str, List[float]] = {k: [] for k in ALL_REGRESSION_TARGETS}
    all_truths: Dict[str, List[float]] = {k: [] for k in ALL_REGRESSION_TARGETS}

    with torch.no_grad():
        for batch in dataloader:
            imgs = batch["image"]
            targets = batch["targets"]
            masks = batch["masks"]

            preds, _ = model(imgs)

            for target_name in ALL_REGRESSION_TARGETS:
                p = preds[target_name].squeeze().cpu().numpy()
                t = targets[target_name].squeeze().cpu().numpy()
                m = masks[target_name].squeeze().cpu().numpy()

                p_arr = np.atleast_1d(p)
                t_arr = np.atleast_1d(t)
                m_arr = np.atleast_1d(m)

                for pi, ti, mi in zip(p_arr, t_arr, m_arr):
                    if mi > 0.5:
                        all_preds[target_name].append(float(pi))
                        all_truths[target_name].append(float(ti))

    metrics: Dict[str, Any] = {}
    for target_name in ALL_REGRESSION_TARGETS:
        y_pred = np.array(all_preds[target_name])
        y_true = np.array(all_truths[target_name])

        if len(y_true) >= 2:
            mae = float(mean_absolute_error(y_true, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
            med_ae = float(np.median(np.abs(y_true - y_pred)))
            r2 = float(r2_score(y_true, y_pred)) if np.var(y_true) > 1e-6 else 0.0

            metrics[target_name] = {
                "count": len(y_true),
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "median_absolute_error": round(med_ae, 3),
                "r2_score": round(r2, 4),
                "ground_truth_mean": round(float(np.mean(y_true)), 2),
                "ground_truth_std": round(float(np.std(y_true)), 2)
            }
        else:
            metrics[target_name] = {"count": len(y_true), "status": "INSUFFICIENT_SAMPLES"}

    return metrics


def train_and_export_neonatal_model(
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 0.001,
    dataset_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes training loop on subject-level train split and exports model artifacts.
    """
    logger.info("Initializing Indian Neonatal Vision Dataset partitions...")
    train_dataset = IndianNeonatalVisionDataset(split="train", dataset_dir=dataset_dir)
    val_dataset = IndianNeonatalVisionDataset(split="val", dataset_dir=dataset_dir)
    test_dataset = IndianNeonatalVisionDataset(split="test", dataset_dir=dataset_dir)

    logger.info(f"Dataset partitions loaded: Train={len(train_dataset)} images, Val={len(val_dataset)} images, Test={len(test_dataset)} images")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    logger.info("Instantiating EfficientNetB0NeonatalRegressor...")
    model = EfficientNetB0NeonatalRegressor(pretrained=True)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    logger.info(f"Beginning training for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        batches = 0

        for batch in train_loader:
            imgs = batch["image"]
            targets = batch["targets"]
            masks = batch["masks"]

            optimizer.zero_grad()
            preds, _ = model(imgs)
            loss, _ = compute_masked_loss(preds, targets, masks)

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batches += 1

        avg_loss = epoch_loss / max(1, batches)
        logger.info(f"Epoch {epoch+1}/{epochs} - Normalized Multi-Task Loss: {avg_loss:.4f}")

    # Evaluate on Held-Out Test Split (100% patient-level isolated)
    logger.info("Evaluating on held-out subject-level test split...")
    test_metrics = evaluate_regressor(model, test_loader)
    val_metrics = evaluate_regressor(model, val_loader)

    # Save artifacts
    models_dir = os.path.join(BASE_DIR, "ai", "models")
    os.makedirs(models_dir, exist_ok=True)
    weights_path = os.path.join(models_dir, "neonatal_regressor.pth")
    metrics_path = os.path.join(models_dir, "neonatal_regression_metrics.json")

    torch.save(model.state_dict(), weights_path)
    logger.info(f"Saved neonatal regressor weights to {weights_path}")

    full_results = {
        "model_name": "EfficientNetB0NeonatalRegressor",
        "dataset": "Neonatal Anthropometric Image Dataset for Computer Vision-Based Growth Analysis",
        "attribution": "Anurag Singh & Dr. Rashi Agarwal (2026)",
        "clinical_sites": [
            "Combined District Hospital, Manjhanpur, Kaushambi, UP, India",
            "Madhuraj Hospital, Kanpur, UP, India"
        ],
        "training_metadata": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": lr,
            "train_images": len(train_dataset),
            "val_images": len(val_dataset),
            "test_images": len(test_dataset)
        },
        "test_metrics": test_metrics,
        "val_metrics": val_metrics
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)
    logger.info(f"Saved neonatal regression metrics to {metrics_path}")

    return full_results


if __name__ == "__main__":
    results = train_and_export_neonatal_model(epochs=5, batch_size=16, lr=0.001)
    print("\n--- NEONATAL REGRESSION TEST SET BENCHMARKS ---")
    for target, m in results["test_metrics"].items():
        if "mae" in m:
            print(f"  • {target:<24}: MAE={m['mae']:>6.2f} | RMSE={m['rmse']:>6.2f} | MedAE={m['median_absolute_error']:>6.2f} | R²={m['r2_score']:>6.3f}")
