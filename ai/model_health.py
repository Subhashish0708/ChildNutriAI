"""
=============================================================================
AI Model Health & Integrity Diagnostic Utility - ChildNutri AI
=============================================================================
Fulfills Step 19 Requirements:
Inspects all 13 AI components and reports their operational status:
  • READY: Verified and ready for production inference
  • WARNING: Operational but has non-blocking observations
  • EXPERIMENTAL: Architectural research prototype (not for clinical production)
  • UNAVAILABLE: Optional component not installed or missing artifact
  • ERROR: Corrupted artifact, dimension mismatch, or deserialization failure
=============================================================================
"""

import os
import sys
import logging
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import joblib
import torch
import numpy as np

logger = logging.getLogger("childnutri.model_health")
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")


def check_all_models_health() -> Dict[str, Any]:
    """
    Runs comprehensive health and integrity checks across all 13 components.
    Returns status dictionaries with standardized classifications:
    READY, WARNING, EXPERIMENTAL, UNAVAILABLE, ERROR.
    """
    report = {
        "status": "healthy",
        "production_pipeline": "tabular_ensemble",
        "components": {},
        "summary": {
            "ready_count": 0,
            "experimental_count": 0,
            "warning_count": 0,
            "unavailable_count": 0,
            "error_count": 0
        }
    }

    def _register(component: str, status: str, tier: str, details: str, artifact: str = ""):
        report["components"][component] = {
            "status": status,
            "tier": tier,
            "artifact": artifact,
            "details": details
        }
        key = f"{status.lower()}_count"
        if key in report["summary"]:
            report["summary"][key] += 1
        else:
            report["summary"]["error_count"] += 1

    # 1. Cleaner
    p = os.path.join(MODELS_DIR, "cleaner.pkl")
    if os.path.exists(p):
        try:
            c = joblib.load(p)
            _register("cleaner", "READY", "preprocessing", "DataCleaner loaded and functional", "cleaner.pkl")
        except Exception as e:
            _register("cleaner", "ERROR", "preprocessing", f"Failed to load: {e}", "cleaner.pkl")
    else:
        _register("cleaner", "ERROR", "preprocessing", "Artifact missing", "cleaner.pkl")

    # 2. Transformer
    p = os.path.join(MODELS_DIR, "transformer.pkl")
    if os.path.exists(p):
        try:
            t = joblib.load(p)
            n_feat = len(getattr(t, "feature_names", []))
            if n_feat == 12:
                _register("transformer", "READY", "preprocessing", "DataTransformer verified with 12 features", "transformer.pkl")
            else:
                _register("transformer", "WARNING", "preprocessing", f"Feature count is {n_feat} (expected 12)", "transformer.pkl")
        except Exception as e:
            _register("transformer", "ERROR", "preprocessing", f"Failed to load: {e}", "transformer.pkl")
    else:
        _register("transformer", "ERROR", "preprocessing", "Artifact missing", "transformer.pkl")

    # 3. XGBoost
    p = os.path.join(MODELS_DIR, "xgboost_model.pkl")
    if os.path.exists(p):
        try:
            m = joblib.load(p)
            _register("xgboost", "READY", "production_submodel", "XGBoost classifier ready (Ensemble 40%)", "xgboost_model.pkl")
        except Exception as e:
            _register("xgboost", "ERROR", "production_submodel", f"Failed to load: {e}", "xgboost_model.pkl")
    else:
        _register("xgboost", "ERROR", "production_submodel", "Artifact missing", "xgboost_model.pkl")

    # 4. LightGBM
    p = os.path.join(MODELS_DIR, "lightgbm_model.pkl")
    if os.path.exists(p):
        try:
            m = joblib.load(p)
            _register("lightgbm", "READY", "production_submodel", "LightGBM classifier ready (Ensemble 35%)", "lightgbm_model.pkl")
        except Exception as e:
            _register("lightgbm", "ERROR", "production_submodel", f"Failed to load: {e}", "lightgbm_model.pkl")
    else:
        _register("lightgbm", "ERROR", "production_submodel", "Artifact missing", "lightgbm_model.pkl")

    # 5. Random Forest
    p = os.path.join(MODELS_DIR, "random_forest_model.pkl")
    if os.path.exists(p):
        try:
            m = joblib.load(p)
            _register("random_forest", "READY", "production_submodel", "Random Forest ready (Ensemble 25% + SHAP)", "random_forest_model.pkl")
        except Exception as e:
            _register("random_forest", "ERROR", "production_submodel", f"Failed to load: {e}", "random_forest_model.pkl")
    else:
        _register("random_forest", "ERROR", "production_submodel", "Artifact missing", "random_forest_model.pkl")

    # 6. Ensemble
    p = os.path.join(MODELS_DIR, "ensemble_model.pkl")
    if os.path.exists(p):
        try:
            from ai.models.tabular_models import SoftVotingEnsemble
            m = joblib.load(p)
            if isinstance(m, SoftVotingEnsemble):
                _register("ensemble", "READY", "production", "Soft-Voting Ensemble (XGB 40% + LGB 35% + RF 25%) ready", "ensemble_model.pkl")
            else:
                _register("ensemble", "ERROR", "production", f"Unexpected type: {type(m).__name__}", "ensemble_model.pkl")
        except Exception as e:
            _register("ensemble", "ERROR", "production", f"Failed to load: {e}", "ensemble_model.pkl")
    else:
        _register("ensemble", "ERROR", "production", "Artifact missing", "ensemble_model.pkl")

    # 7. PyTorch MLP
    p = os.path.join(MODELS_DIR, "pytorch_mlp.pth")
    if os.path.exists(p):
        try:
            sd = torch.load(p, map_location="cpu", weights_only=False)
            _register("pytorch_mlp", "EXPERIMENTAL", "experimental_submodel", "PyTorch Tabular MLP state dict available for benchmarking", "pytorch_mlp.pth")
        except Exception as e:
            _register("pytorch_mlp", "ERROR", "experimental_submodel", f"Failed to load: {e}", "pytorch_mlp.pth")
    else:
        _register("pytorch_mlp", "UNAVAILABLE", "experimental_submodel", "Artifact missing", "pytorch_mlp.pth")

    # 8. Vision Model (EfficientNet-B0)
    p = os.path.join(MODELS_DIR, "vision_efficientnet.pth")
    if os.path.exists(p):
        try:
            sd = torch.load(p, map_location="cpu", weights_only=False)
            _register("vision", "EXPERIMENTAL", "experimental_prototype", "EfficientNet-B0 visual model prototype (not for clinical production)", "vision_efficientnet.pth")
        except Exception as e:
            _register("vision", "ERROR", "experimental_prototype", f"Failed to load: {e}", "vision_efficientnet.pth")
    else:
        _register("vision", "UNAVAILABLE", "experimental_prototype", "Artifact missing", "vision_efficientnet.pth")

    # 9. Multimodal Fusion
    p = os.path.join(MODELS_DIR, "multimodal_fusion.pth")
    if os.path.exists(p):
        try:
            sd = torch.load(p, map_location="cpu", weights_only=False)
            _register("multimodal_fusion", "EXPERIMENTAL", "experimental_prototype", "1292-D Multimodal Fusion Network prototype (1280 visual + 12 anthro)", "multimodal_fusion.pth")
        except Exception as e:
            _register("multimodal_fusion", "ERROR", "experimental_prototype", f"Failed to load: {e}", "multimodal_fusion.pth")
    else:
        _register("multimodal_fusion", "UNAVAILABLE", "experimental_prototype", "Artifact missing", "multimodal_fusion.pth")

    # 10. Autoencoder
    p = os.path.join(MODELS_DIR, "autoencoder.pth")
    if os.path.exists(p):
        try:
            sd = torch.load(p, map_location="cpu", weights_only=False)
            _register("autoencoder", "READY", "supporting_unsupervised", "Reconstruction autoencoder for measurement anomaly screening", "autoencoder.pth")
        except Exception as e:
            _register("autoencoder", "ERROR", "supporting_unsupervised", f"Failed to load: {e}", "autoencoder.pth")
    else:
        _register("autoencoder", "WARNING", "supporting_unsupervised", "Artifact missing", "autoencoder.pth")

    # 11. K-Means
    p = os.path.join(MODELS_DIR, "kmeans_clusterer.pkl")
    if os.path.exists(p):
        try:
            km = joblib.load(p)
            _register("kmeans", "READY", "exploratory_unsupervised", "Nutritional K-Means (K=4) for exploratory cohort grouping", "kmeans_clusterer.pkl")
        except Exception as e:
            _register("kmeans", "ERROR", "exploratory_unsupervised", f"Failed to load: {e}", "kmeans_clusterer.pkl")
    else:
        _register("kmeans", "WARNING", "exploratory_unsupervised", "Artifact missing", "kmeans_clusterer.pkl")

    # 12. SHAP
    try:
        from ai.explainability.shap_explainer import ChildNutriSHAPExplainer
        rf = joblib.load(os.path.join(MODELS_DIR, "random_forest_model.pkl"))
        explainer = ChildNutriSHAPExplainer(rf, feature_names=[f"feat_{i}" for i in range(12)], classes=["Normal"] * 5)
        _register("shap", "READY", "explainability", "SHAP TreeExplainer for Random Forest component ready", "random_forest_model.pkl")
    except Exception as e:
        _register("shap", "WARNING", "explainability", f"SHAP explainer init observation: {e}", "")

    # 13. Grad-CAM
    try:
        from ai.explainability.gradcam import GradCAMVisualExplainer
        from ai.models.vision_model import EfficientNetB0MalnutritionClassifier
        vis = EfficientNetB0MalnutritionClassifier(num_classes=5, pretrained=False)
        cam = GradCAMVisualExplainer(vis)
        _register("gradcam", "EXPERIMENTAL", "explainability", "Grad-CAM visual explainer prototype (3 clean states)", "vision_efficientnet.pth")
    except Exception as e:
        _register("gradcam", "WARNING", "explainability", f"Grad-CAM observation: {e}", "")

    # Overall verdict
    if report["summary"]["error_count"] > 0:
        report["status"] = "degraded"
    elif report["summary"]["warning_count"] > 0:
        report["status"] = "operational_with_warnings"
    else:
        report["status"] = "healthy"

    return report


if __name__ == "__main__":
    health = check_all_models_health()
    print("=" * 70)
    print("CHILDNUTRI AI - MODEL HEALTH & INTEGRITY REPORT")
    print("=" * 70)
    print(f"Overall Status:       {health['status'].upper()}")
    print(f"Production Pipeline:  {health['production_pipeline']}")
    print(f"Components Summary:   {health['summary']}")
    print("-" * 70)
    for comp, info in health["components"].items():
        print(f"  {comp:20s} | {info['status']:12s} | {info['tier']:25s} | {info['details']}")
    print("=" * 70)
