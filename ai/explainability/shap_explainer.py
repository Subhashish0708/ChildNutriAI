"""
=============================================================================
SHAP (SHapley Additive Explanations) Explainer - ChildNutri AI
=============================================================================
Calculates exact Shapley feature attributions using SHAP TreeExplainer
on the Random Forest component of the production Soft-Voting Ensemble:
  • Global Feature Importance (Macro dataset level)
  • Local Individual Patient Explanation ("Why was this child flagged?")

NOTE: For computational determinism and tree-structure decomposition,
SHAP is computed on the Random Forest constituent model of the Soft-Voting
Ensemble. It is explicitly labeled as the Random Forest feature attribution.
=============================================================================
"""

import logging
import shap
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger("childnutri.shap")

class ChildNutriSHAPExplainer:
    """
    Computes SHAP feature attributions on Random Forest for clinical transparency.
    """
    def __init__(self, model, feature_names: List[str], classes: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.classes = classes
        self.explainer = None
        if self.model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                logger.error(f"Failed to initialize SHAP TreeExplainer: {e}")

    def explain_instance(self, X_sample: np.ndarray, top_k: int = 5, predicted_class: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes SHAP contributions for a single child's assessment.
        X_sample: 1D array (num_features,) or 2D (1, num_features)
        """
        if self.explainer is None or self.model is None:
            return {
                "available": False,
                "status": "NOT_AVAILABLE",
                "model": "Random Forest (Component of Soft-Voting Ensemble)",
                "model_version": "2.0.0",
                "predicted_class": predicted_class,
                "top_contributing_features": [],
                "top_feature_attributions": [],
                "features": [],
                "clinical_explanation_summary": ["Feature attribution is not available (explainer uninitialized)."],
                "expected_value_base": None,
                "reason": "SHAP TreeExplainer model component is uninitialized.",
                "disclaimer": "AI explanations describe model behavior and feature attribution, not medical causation."
            }

        try:
            if X_sample.ndim == 1:
                X_sample = X_sample.reshape(1, -1)

            shap_values = self.explainer.shap_values(X_sample)
            if predicted_class and predicted_class in self.classes:
                pred_class_idx = self.classes.index(predicted_class)
                pred_label = predicted_class
            else:
                pred_class_idx = int(self.model.predict(X_sample)[0])
                pred_label = self.classes[pred_class_idx] if pred_class_idx < len(self.classes) else "Unknown"

            if isinstance(shap_values, list):
                class_shap = shap_values[pred_class_idx][0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                class_shap = shap_values[0, :, pred_class_idx]
            else:
                class_shap = shap_values[0]

            attributions = []
            for feat_name, val, sv in zip(self.feature_names, X_sample[0], class_shap):
                sv_float = float(sv)
                attributions.append({
                    "feature": feat_name,
                    "input_value": round(float(val), 3),
                    "feature_value": round(float(val), 3),
                    "shap_value": round(sv_float, 4),
                    "contribution": round(sv_float, 4),
                    "contribution_direction": "increases_screening_concern" if sv_float > 0 else "decreases_screening_concern",
                    "contribution_magnitude": round(abs(sv_float), 4),
                    "impact": "Increased Risk" if sv_float > 0 else "Decreased Risk / Protective",
                    "abs_importance": round(abs(sv_float), 4)
                })

            # Deterministic ranking by absolute contribution magnitude
            attributions.sort(key=lambda x: x["abs_importance"], reverse=True)
            top_factors = attributions[:top_k]

            total_abs = sum(f["abs_importance"] for f in top_factors)
            for f in top_factors:
                f["relative_percentage"] = round((f["abs_importance"] / total_abs * 100.0), 1) if total_abs > 0 else 0.0

            top_reasons = []
            for item in top_factors:
                feat_disp = item["feature"].replace("_", " ").title()
                if item["shap_value"] > 0:
                    top_reasons.append(f"{feat_disp} (+{item['shap_value']:.3f}) contributed toward model concern for {pred_label}.")
                else:
                    top_reasons.append(f"{feat_disp} ({item['shap_value']:.3f}) reduced model concern for {pred_label}.")

            base_val = 0.20
            if hasattr(self.explainer, "expected_value"):
                ev = self.explainer.expected_value
                if isinstance(ev, (list, np.ndarray)) and len(ev) > pred_class_idx:
                    base_val = float(ev[pred_class_idx])
                elif isinstance(ev, (float, int)):
                    base_val = float(ev)

            return {
                "available": True,
                "status": "AVAILABLE",
                "model": "Random Forest (Component of Soft-Voting Ensemble)",
                "model_version": "2.0.0",
                "predicted_class": pred_label,
                "features": top_factors,
                "top_contributing_features": top_factors,
                "top_feature_attributions": top_factors,
                "clinical_explanation_summary": top_reasons,
                "expected_value_base": round(base_val, 3),
                "shap_decision_summary": f"{top_factors[0]['feature'].replace('_', ' ').title()} and {top_factors[1]['feature'].replace('_', ' ').title()} contributed most significantly toward the model's {pred_label} screening output." if len(top_factors) >= 2 else "SHAP attribution complete.",
                "disclaimer": "AI explanations describe model behavior and feature attribution, not medical causation."
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return {
                "available": False,
                "status": "ERROR",
                "model": "Random Forest (Component of Soft-Voting Ensemble)",
                "model_version": "2.0.0",
                "predicted_class": None,
                "top_contributing_features": [],
                "top_feature_attributions": [],
                "features": [],
                "clinical_explanation_summary": ["Feature attribution calculation encountered an error."],
                "expected_value_base": None,
                "reason": f"SHAP calculation error: {e}",
                "message": f"SHAP calculation error: {e}",
                "disclaimer": "AI explanations describe model behavior and feature attribution, not medical causation."
            }
