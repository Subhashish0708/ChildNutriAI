"""
=============================================================================
Unified Production Inference Engine - ChildNutri AI
=============================================================================
Orchestrates the multi-layered pediatric screening pipeline:
  • Layer 1: Deterministic WHO Growth Standards (Box-Cox LMS Z-Scores)
  • Layer 2A: Official Tabular Production Ensemble (XGBoost 40% + LightGBM 35% + Random Forest 25%)
  • Layer 2B: Vision & 1292-D Multimodal Feature Fusion (Architectural Research Prototype)
  • Layer 3: Deterministic Clinical Safety Triage (IMCI / CMAM)
  • Layer 4: Explainability (SHAP TreeExplainer on Random Forest & Genuine Grad-CAM)
  • Layer 5: Unsupervised Anomaly Screening (Autoencoder) & Exploratory Cohorts (K-Means)

DETERMINISTIC INFERENCE RULES:
  1. Without image:
     prediction_source = "tabular_ensemble"
     No random visual tensors are generated.
     Vision and fusion branches are cleanly marked unavailable.
  2. With valid image & valid model:
     prediction_source = "multimodal_fusion"
     Real EfficientNet 1280-D embeddings + 12-D anthropometric features (1292-D input).
=============================================================================
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import torch

# Preprocessors & Core Models
from ai.preprocess import DataCleaner, DataTransformer, ImagePreprocessor
from ai.models.tabular_models import SoftVotingEnsemble
from ai.models.vision_model import EfficientNetB0MalnutritionClassifier
from ai.models.multimodal_fusion import MultimodalFusionNetwork1292D
from ai.models.unsupervised import AnthropometricAutoencoder, NutritionalKMeansClusterer
from ai.models.future_risk_predictor import FutureRiskPredictor
from ai.models.nutrition_recommender import NutritionRecommender

# Clinical & Explainability Engines
from ai.clinical_algorithms.who_lms import WHOLMSEngine
from ai.clinical_algorithms.longitudinal_velocity import LongitudinalGrowthVelocityEngine
from ai.clinical_algorithms.clinical_triage import ClinicalTriageEngine
from ai.clinical_algorithms.risk_scorer import ContinuousRiskScorer
from ai.explainability.shap_explainer import ChildNutriSHAPExplainer
from ai.explainability.gradcam import GradCAMVisualExplainer
from ai.registry import TABULAR_12_FEATURES, CLASSES_5
from ai.vision_pipeline import (
    validate_child_image,
    preprocess_child_image,
    predict_from_image,
    predict_multimodal,
    build_image_processing_status_pipeline
)
from ai.early_warning import EarlyDetectionEngine

logger = logging.getLogger("childnutri.predict")
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")


class ChildNutriMultimodalPredictor:
    """
    Pediatric Assessment Engine connecting production tabular ML,
    exploratory vision prototypes, deterministic WHO growth tables, and clinical triage.
    """
    def __init__(self):
        # 1. Load Preprocessors
        self.cleaner: DataCleaner = joblib.load(os.path.join(MODELS_DIR, "cleaner.pkl"))
        self.transformer: DataTransformer = joblib.load(os.path.join(MODELS_DIR, "transformer.pkl"))
        self.img_preprocessor: ImagePreprocessor = joblib.load(os.path.join(MODELS_DIR, "image_preprocessor.pkl"))
        self.feature_names = getattr(self.transformer, "feature_names", TABULAR_12_FEATURES)

        # 2. Load Production Tabular Soft-Voting Ensemble (Reject anthropometric_model.pkl as ensemble)
        ensemble_path = os.path.join(MODELS_DIR, "ensemble_model.pkl")
        if os.path.exists(ensemble_path):
            loaded_ens = joblib.load(ensemble_path)
            if isinstance(loaded_ens, SoftVotingEnsemble):
                self.ensemble_model = loaded_ens
                self.classes = list(getattr(loaded_ens, "classes_", CLASSES_5))
            else:
                raise TypeError(f"ensemble_model.pkl must be SoftVotingEnsemble, got {type(loaded_ens).__name__}")
        else:
            raise FileNotFoundError(f"Production ensemble artifact missing: {ensemble_path}")

        # 3. Load Vision Model Prototype (EfficientNet-B0)
        self.vision_model = EfficientNetB0MalnutritionClassifier(num_classes=len(self.classes), pretrained=False)
        vision_weights = os.path.join(MODELS_DIR, "vision_efficientnet.pth")
        if os.path.exists(vision_weights):
            try:
                self.vision_model.load_state_dict(torch.load(vision_weights, map_location="cpu", weights_only=False))
            except Exception as e:
                logger.warning(f"Could not load vision weights: {e}")
        self.vision_model.eval()

        # 4. Load 1292-D Multimodal Fusion Network Prototype (1280 visual + 12 anthro)
        self.fusion_net = MultimodalFusionNetwork1292D(
            visual_dim=1280,
            anthro_dim=len(self.feature_names),
            num_classes=len(self.classes)
        )
        fusion_weights = os.path.join(MODELS_DIR, "multimodal_fusion.pth")
        if os.path.exists(fusion_weights):
            try:
                self.fusion_net.load_state_dict(torch.load(fusion_weights, map_location="cpu", weights_only=False))
            except Exception as e:
                logger.warning(f"Could not load fusion weights: {e}")
        self.fusion_net.eval()

        # 5. Load Unsupervised Anomaly Screening & Clustering Models
        self.autoencoder = AnthropometricAutoencoder(in_features=len(self.feature_names), latent_dim=4)
        ae_weights = os.path.join(MODELS_DIR, "autoencoder.pth")
        if os.path.exists(ae_weights):
            try:
                self.autoencoder.load_state_dict(torch.load(ae_weights, map_location="cpu", weights_only=False))
            except Exception as e:
                logger.warning(f"Could not load autoencoder weights: {e}")
        self.autoencoder.eval()

        self.kmeans: NutritionalKMeansClusterer = joblib.load(os.path.join(MODELS_DIR, "kmeans_clusterer.pkl"))

        # 6. Load Explainers
        rf_path = os.path.join(MODELS_DIR, "random_forest_model.pkl")
        rf_model = joblib.load(rf_path) if os.path.exists(rf_path) else None
        self.shap_explainer = ChildNutriSHAPExplainer(rf_model, feature_names=self.feature_names, classes=self.classes)
        self.gradcam_explainer = GradCAMVisualExplainer(self.vision_model)

    def assess_child(
        self,
        age_months: float,
        gender: str,
        weight: float,
        height: float,
        muac: Optional[float] = None,
        head_circumference: Optional[float] = None,
        image_path: Optional[str] = None,
        growth_history: Optional[List[Dict[str, Any]]] = None,
        has_bilateral_edema: bool = False,
        child_name: str = "Child",
        doctor_name: str = "Dr. Meena Rao"
    ) -> Dict[str, Any]:
        """
        Executes complete child nutrition assessment.
        Guarantees deterministic, traceable inference without random visual tensors.
        """
        # ---------------------------------------------------------------------
        # 1. DATA CLEANING & TRANSFORMATION (Production Tabular Pipeline)
        # ---------------------------------------------------------------------
        raw_df = pd.DataFrame([{
            "age_months": float(age_months),
            "gender": str(gender),
            "weight": float(weight),
            "height": float(height),
            "muac": float(muac) if muac is not None else None,
            "head_circumference": float(head_circumference) if head_circumference is not None else None
        }])

        cleaned_df = self.cleaner.clean(raw_df, is_training=False)
        X_scaled = self.transformer.transform(cleaned_df)
        t_anthro = torch.tensor(X_scaled, dtype=torch.float32)

        # ---------------------------------------------------------------------
        # 2. DETERMINISTIC WHO LMS GROWTH STANDARDS
        # ---------------------------------------------------------------------
        who_scores = WHOLMSEngine.calculate_all_zscores(
            age_months=float(age_months),
            gender=str(gender),
            weight=float(weight),
            height=float(height),
            muac=float(cleaned_df["muac"].iloc[0]),
            head_circumference=float(cleaned_df["head_circumference"].iloc[0])
        )

        # ---------------------------------------------------------------------
        # 3. PRODUCTION TABULAR ENSEMBLE PREDICTION
        # ---------------------------------------------------------------------
        probs_ensemble = self.ensemble_model.predict_proba(X_scaled)[0]
        ens_pred_idx = int(np.argmax(probs_ensemble))
        ens_pred_label = self.classes[ens_pred_idx]
        ens_confidence = float(np.max(probs_ensemble))

        # ---------------------------------------------------------------------
        # 4. IMAGE BRANCH & MULTIMODAL INFERENCE (Zero Random Tensors)
        # ---------------------------------------------------------------------
        vision_available = False
        fusion_available = False
        modality_weights = [0.0, 1.0]
        vision_screening_data = None
        multimodal_screening_data = None
        val_res = {"is_valid": False, "quality": "NOT_PROVIDED", "error_message": "No child photograph provided."}

        if image_path and os.path.exists(image_path):
            val_res = validate_child_image(image_path)
            if val_res["is_valid"]:
                try:
                    vis_out = predict_from_image(image_path, vision_model=self.vision_model, classes=self.classes)
                    if vis_out["available"]:
                        vision_screening_data = vis_out
                        vision_available = True
                        vision_status = "available"

                        # Multimodal fusion (1280-D visual + 12-D anthropometric -> 1292-D)
                        fus_out = predict_multimodal(
                            visual_features_1280d=vis_out["visual_features"],
                            anthro_features_12d=t_anthro,
                            fusion_model=self.fusion_net,
                            classes=self.classes
                        )
                        if fus_out["available"]:
                            multimodal_screening_data = fus_out
                            fusion_available = True
                            multimodal_status = "experimental"
                            prediction_source = "multimodal_fusion"
                            final_pred_label = fus_out["prediction"]
                            final_confidence = fus_out["confidence"]
                            modality_weights = [
                                fus_out["modality_weights"]["visual_contribution_pct"] / 100.0,
                                fus_out["modality_weights"]["anthropometric_contribution_pct"] / 100.0
                            ]
                        else:
                            multimodal_status = "not_applicable"
                            prediction_source = "tabular_ensemble"
                            final_pred_label = ens_pred_label
                            final_confidence = ens_confidence

                        # Grad-CAM overlay
                        img_tensor = preprocess_child_image(image_path)
                        gradcam_data = self.gradcam_explainer.generate_gradcam_overlay(
                            image_path_or_pil=image_path,
                            input_tensor=img_tensor,
                            class_idx=self.classes.index(final_pred_label) if final_pred_label in self.classes else 0
                        )
                    else:
                        vision_status = "not_available"
                        multimodal_status = "not_applicable"
                        prediction_source = "tabular_ensemble"
                        final_pred_label = ens_pred_label
                        final_confidence = ens_confidence
                        gradcam_data = {
                            "available": False,
                            "status": "error",
                            "message": vis_out.get("message", "Vision screening failed.")
                        }
                except Exception as e:
                    logger.error(f"Vision inference failed on image: {e}")
                    prediction_source = "tabular_ensemble"
                    final_pred_label = ens_pred_label
                    final_confidence = ens_confidence
                    vision_status = "not_available"
                    multimodal_status = "not_applicable"
                    gradcam_data = {
                        "available": False,
                        "status": "error",
                        "message": f"Vision processing error: {e}"
                    }
            else:
                # Invalid image quality
                prediction_source = "tabular_ensemble"
                final_pred_label = ens_pred_label
                final_confidence = ens_confidence
                vision_status = "not_available"
                multimodal_status = "not_applicable"
                gradcam_data = {
                    "available": False,
                    "status": "error",
                    "message": val_res.get("error_message") or "Image validation failed."
                }
        else:
            # NO IMAGE: Tabular-only screening. NO random visual tensors.
            prediction_source = "tabular_ensemble"
            final_pred_label = ens_pred_label
            final_confidence = ens_confidence
            vision_status = "not_available"
            multimodal_status = "not_applicable"
            gradcam_data = {
                "available": False,
                "status": "no_image",
                "original_image_base64": None,
                "pure_heatmap_base64": None,
                "gradcam_heatmap_base64": None,
                "gradcam_overlay_base64": None,
                "focus_regions": [],
                "disclaimer": "No photographic assessment is available for this assessment.",
                "message": "No photographic record uploaded for this assessment."
            }

        # Build 7-stage image processing tracker
        image_pipeline_tracker = build_image_processing_status_pipeline(
            image_attached=bool(image_path and os.path.exists(image_path)),
            val_result=val_res,
            vision_result=vision_screening_data or {"available": False, "status": vision_status},
            fusion_result=multimodal_screening_data or {"available": False, "status": multimodal_status}
        )

        # ---------------------------------------------------------------------
        # 5. SHAP EXPLAINABILITY (Random Forest Component)
        # ---------------------------------------------------------------------
        shap_explanation = self.shap_explainer.explain_instance(X_scaled[0], top_k=4)

        # ---------------------------------------------------------------------
        # 6. LONGITUDINAL GROWTH-VELOCITY ANALYSIS
        # ---------------------------------------------------------------------
        velocity_analysis = LongitudinalGrowthVelocityEngine.analyze_growth_history(growth_history or [])

        # ---------------------------------------------------------------------
        # 7. DETERMINISTIC CLINICAL SAFETY TRIAGE (IMCI / CMAM)
        # ---------------------------------------------------------------------
        triage = ClinicalTriageEngine.evaluate_triage(
            age_months=float(age_months),
            weight=float(weight),
            height=float(height),
            muac=float(cleaned_df["muac"].iloc[0]),
            has_bilateral_edema=has_bilateral_edema,
            whz=who_scores.get("whz"),
            haz=who_scores.get("haz"),
            waz=who_scores.get("waz"),
            prediction_label=final_pred_label,
            confidence=final_confidence
        )

        # ---------------------------------------------------------------------
        # 8. COMPOSITE SCREENING RISK SCORE (0 - 100)
        # ---------------------------------------------------------------------
        risk_evaluation = ContinuousRiskScorer.compute_composite_risk_score(
            prediction_label=final_pred_label,
            confidence=final_confidence,
            haz=who_scores.get("haz"),
            waz=who_scores.get("waz"),
            whz=who_scores.get("whz"),
            muac=float(cleaned_df["muac"].iloc[0]),
            is_faltering_velocity=velocity_analysis.get("early_warning_alert", False)
        )

        # ---------------------------------------------------------------------
        # 9. UNSUPERVISED ANOMALY SCREENING & COHORT CLUSTERING
        # ---------------------------------------------------------------------
        anomaly_check = self.autoencoder.compute_anomaly_score(t_anthro)
        cohort = self.kmeans.predict_cluster(X_scaled[0])

        # ---------------------------------------------------------------------
        # 10. EXPERIMENTAL FUTURE RISK PROJECTION
        # ---------------------------------------------------------------------
        future_risk = FutureRiskPredictor.predict_future_risk(
            growth_history=growth_history or [],
            current_age_months=float(age_months),
            current_weight=float(weight),
            current_height=float(height),
            current_muac=float(cleaned_df["muac"].iloc[0]),
            current_risk_score=risk_evaluation["risk_score"],
            gender=str(gender)
        )

        # ---------------------------------------------------------------------
        # 11. RULE-BASED NUTRITION RECOMMENDATION (Decision Support)
        # ---------------------------------------------------------------------
        nutrition_plan = NutritionRecommender.generate_plan(
            child_name=child_name,
            age_months=float(age_months),
            gender=str(gender),
            weight_kg=float(weight),
            prediction=final_pred_label,
            muac=float(cleaned_df["muac"].iloc[0]),
            waz=who_scores.get("waz", 0.0),
            haz=who_scores.get("haz", 0.0),
            whz=who_scores.get("whz", 0.0),
            cohort_name=cohort.get("cohort_name", "General"),
            doctor_name=doctor_name
        )

        # ---------------------------------------------------------------------
        # 12. PEDIATRIC EARLY DETECTION & DEVIATION ENGINE
        # ---------------------------------------------------------------------
        prev_asmt = None
        if growth_history and len(growth_history) > 1:
            prev_asmt = growth_history[-2]
        elif growth_history and len(growth_history) == 1:
            gh_wt = float(growth_history[0].get("weight") or growth_history[0].get("weight_kg") or 0.0)
            if abs(gh_wt - float(weight)) > 1e-4:
                prev_asmt = growth_history[0]

        early_warning_data = EarlyDetectionEngine.evaluate_early_warning(
            current_assessment={
                "weight": float(weight),
                "height": float(height),
                "muac": float(cleaned_df["muac"].iloc[0]),
                "whz": who_scores.get("whz"),
                "haz": who_scores.get("haz"),
                "waz": who_scores.get("waz"),
                "has_bilateral_edema": has_bilateral_edema,
                "age_months": float(age_months)
            },
            previous_assessment=prev_asmt,
            growth_history=growth_history or [],
            prediction_label=final_pred_label,
            risk_score=risk_evaluation["risk_score"],
            triage_level=triage.get("level", "ROUTINE (GREEN)"),
            child_name=child_name
        )

        # ---------------------------------------------------------------------
        # 13. EVIDENCE-BASED CLINICAL & DOCTOR-LIKE EXPLANATION DOSSIER
        # ---------------------------------------------------------------------
        from ai.clinical_algorithms.clinical_explanation_engine import ClinicalExplanationEngine
        clinical_explanation = ClinicalExplanationEngine.generate_clinical_explanation(
            child_name=child_name,
            age_months=float(age_months),
            gender=str(gender),
            weight=float(weight),
            height=float(height),
            muac=float(cleaned_df["muac"].iloc[0]),
            head_circumference=float(cleaned_df["head_circumference"].iloc[0]),
            has_bilateral_edema=has_bilateral_edema,
            whz=who_scores.get("whz"),
            haz=who_scores.get("haz"),
            waz=who_scores.get("waz"),
            baz=who_scores.get("baz"),
            prediction_label=final_pred_label,
            confidence=final_confidence,
            risk_score=risk_evaluation["risk_score"],
            triage_level=triage.get("level", "ROUTINE (GREEN)"),
            is_emergency=triage.get("is_emergency", False),
            longitudinal_data={
                "has_history": bool(prev_asmt is not None),
                "early_warning_alert": early_warning_data.get("has_early_warning", False),
                "velocity_alert": early_warning_data.get("has_early_warning", False),
                "weight_velocity_g_day": early_warning_data.get("weight_velocity_g_day")
            },
            shap_factors=shap_explanation.get("top_feature_attributions", [])
        )

        return {
            "prediction": final_pred_label,
            "confidence": round(final_confidence, 3),
            "prediction_source": prediction_source,
            "modality_mode": "MULTIMODAL" if prediction_source == "multimodal_fusion" else "TABULAR_ONLY",
            "vision_status": vision_status,
            "multimodal_status": multimodal_status,
            "vision_available": vision_available,
            "fusion_available": fusion_available,
            "vision_screening": vision_screening_data,
            "multimodal_screening": multimodal_screening_data,
            "image_processing_pipeline": image_pipeline_tracker,
            "early_warning": early_warning_data,
            "doctor_explanation": clinical_explanation.get("doctor_explanation"),
            "clinical_explanation": clinical_explanation,
            "risk_score": risk_evaluation["risk_score"],
            "risk_score_name": "Composite Screening Risk Score",
            "risk_tier": risk_evaluation["risk_tier"],
            "risk_color": risk_evaluation["color_hex"],
            "models_used": {
                "ensemble": "Soft-Voting Ensemble (XGBoost 40% + LightGBM 35% + Random Forest 25%)",
                "vision": "EfficientNet-B0 (1280-D Embeddings, Prototype)",
                "multimodal_fusion": "1292-D Multimodal Feature Fusion Network (Prototype)"
            },
            "modality_contributions": {
                "visual_evidence_weight": round(modality_weights[0] * 100.0, 1),
                "clinical_anthropometric_weight": round(modality_weights[1] * 100.0, 1)
            },
            "who_lms_zscores": who_scores,
            "longitudinal_velocity": velocity_analysis,
            "clinical_triage": triage,
            "explainability": {
                "shap_feature_attributions": shap_explanation.get("top_feature_attributions", []),
                "shap_clinical_reasons": shap_explanation.get("clinical_explanation_summary", []),
                "shap_model": shap_explanation.get("model_explained", "Random Forest"),
                "gradcam": gradcam_data
            },
            "unsupervised_intelligence": {
                "growth_cohort": cohort["cohort_name"],
                "cohort_classification_type": "Exploratory cohort classification",
                "anomaly_screening": {
                    "reconstruction_error": anomaly_check["reconstruction_error_mse"],
                    "is_anomalous": anomaly_check["is_anomalous"],
                    "interpretation": anomaly_check["interpretation"]
                }
            },
            "future_risk_prediction": future_risk,
            "nutrition_recommendation": nutrition_plan
        }


__all__ = [
    "ChildNutriMultimodalPredictor",
    "validate_child_image",
    "preprocess_child_image",
    "predict_from_image",
    "predict_multimodal",
    "build_image_processing_status_pipeline",
    "EarlyDetectionEngine"
]
