"""
=============================================================================
ChildNutri AI - Central AI Model Registry
=============================================================================
Authoritative registry containing metadata, operational status, input/output
contracts, and clinical purposes for all machine learning, deep learning,
and clinical algorithms in ChildNutri AI.
=============================================================================
"""

import os
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")

CLASSES_5 = ["Normal", "Severe (SAM)", "Stunted", "Underweight", "Wasted"]

TABULAR_12_FEATURES = [
    "age_months",
    "gender_code",
    "weight",
    "height",
    "muac",
    "head_circumference",
    "bmi",
    "weight_to_height_ratio",
    "muac_to_height_ratio",
    "head_to_height_ratio",
    "height_deficit_ratio",
    "weight_deficit_ratio"
]

AI_MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── 1. PREPROCESSING & FEATURE ENGINEERING ───────────────────────────────
    "data_cleaner": {
        "model_name": "Anthropometric Data Cleaner",
        "artifact_file": "cleaner.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "cleaner.pkl"),
        "model_type": "Data Preprocessor",
        "python_class": "ai.preprocess.DataCleaner",
        "input_features": ["age_months", "gender", "weight", "height", "muac", "head_circumference"],
        "output_features": ["age_months", "gender", "weight", "height", "muac", "head_circumference"],
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Biological range validation, physiological bounds checking, and median imputation."
    },
    "data_transformer": {
        "model_name": "Anthropometric Feature Transformer",
        "artifact_file": "transformer.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "transformer.pkl"),
        "model_type": "Feature Transformer and Scaler",
        "python_class": "ai.preprocess.DataTransformer",
        "input_features": ["age_months", "gender", "weight", "height", "muac", "head_circumference"],
        "output_features": TABULAR_12_FEATURES,
        "input_dim": 6,
        "output_dim": 12,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Engineers 6 clinical deficit/ratio features and applies standard normal scaling."
    },
    "image_preprocessor": {
        "model_name": "Visual Image Preprocessor",
        "artifact_file": "image_preprocessor.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "image_preprocessor.pkl"),
        "model_type": "Image Normalizer and Augmenter",
        "python_class": "ai.preprocess.ImagePreprocessor",
        "input_features": ["raw_rgb_image"],
        "output_features": ["normalized_tensor_3x224x224"],
        "input_dim": "arbitrary_resolution",
        "output_dim": "3x224x224",
        "training_status": "configured",
        "production_status": "prototype",
        "used_in_production": False,
        "version": "2.0.0",
        "purpose": "Resizes pediatric photos to 224x224 and normalizes via ImageNet mean and std."
    },

    # ── 2. PRODUCTION TABULAR ENSEMBLE & CONSTITUENT MODELS ───────────────────
    "tabular_ensemble": {
        "model_name": "Soft-Voting Tabular Ensemble (XGB + LGB + RF)",
        "artifact_file": "ensemble_model.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "ensemble_model.pkl"),
        "model_type": "Soft-Voting Ensemble Classifier",
        "python_class": "ai.models.tabular_models.SoftVotingEnsemble",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "output_classes": CLASSES_5,
        "weights": [0.40, 0.35, 0.25],  # XGB, LGB, RF
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Authoritative production tabular malnutrition classifier blending XGBoost, LightGBM, and Random Forest."
    },
    "xgboost": {
        "model_name": "XGBoost Classifier",
        "artifact_file": "xgboost_model.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "xgboost_model.pkl"),
        "model_type": "Gradient Boosted Decision Trees",
        "python_class": "xgboost.sklearn.XGBClassifier",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "output_classes": CLASSES_5,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Ensemble component 1 (40 percent weight). Captures non-linear anthropometric interactions."
    },
    "lightgbm": {
        "model_name": "LightGBM Classifier",
        "artifact_file": "lightgbm_model.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "lightgbm_model.pkl"),
        "model_type": "Leaf-wise Gradient Boosted Trees",
        "python_class": "lightgbm.sklearn.LGBMClassifier",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "output_classes": CLASSES_5,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Ensemble component 2 (35 percent weight). High-speed leaf-wise gradient boosting."
    },
    "random_forest": {
        "model_name": "Random Forest Classifier",
        "artifact_file": "random_forest_model.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "random_forest_model.pkl"),
        "model_type": "Bagged Decision Tree Forest",
        "python_class": "sklearn.ensemble._forest.RandomForestClassifier",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "output_classes": CLASSES_5,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Ensemble component 3 (25 percent weight). Explaining baseline for SHAP TreeExplainer."
    },
    "pytorch_mlp": {
        "model_name": "Tabular Clinical MLP with Residual Connections",
        "artifact_file": "pytorch_mlp.pth",
        "artifact_path": os.path.join(MODELS_DIR, "pytorch_mlp.pth"),
        "model_type": "Deep Neural Network",
        "python_class": "ai.models.tabular_models.TabularClinicalMLP",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "output_classes": CLASSES_5,
        "training_status": "trained",
        "production_status": "experimental",
        "used_in_production": False,
        "version": "2.0.0",
        "purpose": "Deep learning tabular baseline with LayerNorm, GELU, and residual skip connections."
    },

    # ── 3. IMAGE & MULTIMODAL PROTOTYPE MODELS ───────────────────────────────
    "vision_efficientnet": {
        "model_name": "EfficientNet-B0 Visual Feature Extractor",
        "artifact_file": "vision_efficientnet.pth",
        "artifact_path": os.path.join(MODELS_DIR, "vision_efficientnet.pth"),
        "model_type": "Convolutional Neural Network (Transfer Learning)",
        "python_class": "ai.models.vision_model.EfficientNetB0MalnutritionClassifier",
        "input_features": ["normalized_tensor_3x224x224"],
        "input_dim": "3x224x224",
        "output_features": ["visual_embedding_1280d", "logits_5class"],
        "embedding_dim": 1280,
        "output_classes": CLASSES_5,
        "training_status": "synthetic_prototype",
        "production_status": "prototype",
        "used_in_production": False,
        "version": "2.0.0",
        "purpose": "Architectural prototype for visual screening. Generates 1280-D embeddings and Grad-CAM maps."
    },
    "multimodal_fusion": {
        "model_name": "1292-D Multimodal Feature Fusion Network",
        "artifact_file": "multimodal_fusion.pth",
        "artifact_path": os.path.join(MODELS_DIR, "multimodal_fusion.pth"),
        "model_type": "Cross-Modal Gated Fusion Neural Network",
        "python_class": "ai.models.multimodal_fusion.MultimodalFusionNetwork1292D",
        "input_features": ["visual_embedding_1280d", "anthropometric_features_12d"],
        "visual_dim": 1280,
        "anthro_dim": 12,
        "total_input_dim": 1292,
        "output_classes": CLASSES_5,
        "training_status": "synthetic_prototype",
        "production_status": "prototype",
        "used_in_production": False,
        "version": "2.0.0",
        "purpose": "Architectural prototype combining 1280-D visual embeddings + 12-D anthropometric measurements with gating."
    },

    # ── 4. UNSUPERVISED & ANOMALY MODELS ─────────────────────────────────────
    "autoencoder": {
        "model_name": "Anthropometric Autoencoder (Anomaly Detection)",
        "artifact_file": "autoencoder.pth",
        "artifact_path": os.path.join(MODELS_DIR, "autoencoder.pth"),
        "model_type": "Deep Autoencoder",
        "python_class": "ai.models.unsupervised.AnthropometricAutoencoder",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "latent_dim": 4,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Measurement consistency and anomaly screening. Flags impossible or conflicting anthropometric combinations."
    },
    "kmeans_clusterer": {
        "model_name": "Nutritional K-Means Clusterer",
        "artifact_file": "kmeans_clusterer.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "kmeans_clusterer.pkl"),
        "model_type": "K-Means Clustering (k=4)",
        "python_class": "ai.models.unsupervised.NutritionalKMeansClusterer",
        "input_features": TABULAR_12_FEATURES,
        "input_dim": 12,
        "n_clusters": 4,
        "training_status": "trained",
        "production_status": "exploratory",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Exploratory cohort grouping for population-level phenotyping (not for clinical diagnosis)."
    },
    "label_encoder": {
        "model_name": "Diagnostic Label Encoder",
        "artifact_file": "label_encoder.pkl",
        "artifact_path": os.path.join(MODELS_DIR, "label_encoder.pkl"),
        "model_type": "Class Label Encoder",
        "python_class": "sklearn.preprocessing._label.LabelEncoder",
        "classes": CLASSES_5,
        "training_status": "trained",
        "production_status": "production",
        "used_in_production": True,
        "version": "2.0.0",
        "purpose": "Maps numerical class indices 0..4 to canonical diagnostic labels."
    }
}

def get_registry() -> Dict[str, Dict[str, Any]]:
    return AI_MODEL_REGISTRY

def get_production_models() -> Dict[str, Dict[str, Any]]:
    return {k: v for k, v in AI_MODEL_REGISTRY.items() if v.get("production_status") == "production"}

def get_prototype_models() -> Dict[str, Dict[str, Any]]:
    return {k: v for k, v in AI_MODEL_REGISTRY.items() if v.get("production_status") == "prototype"}
