"""
ChildNutri AI — Future Risk Engine
Combines trend signals, closeness-to-cutoff, and ML risk-factor model.

Output: { "tier": "LOW"|"WATCH"|"HIGH", "points": {...}, "reasons": [...] }
"""
from __future__ import annotations
import os
import math
from typing import Optional, List
import joblib

# ── Risk-model loader ─────────────────────────────────────────────────────────
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml_artifacts", "risk_model.joblib")
_risk_model = None


def _load_model():
    global _risk_model
    if _risk_model is not None:
        return _risk_model
    if os.path.exists(_MODEL_PATH):
        try:
            _risk_model = joblib.load(_MODEL_PATH)
        except Exception:
            _risk_model = None
    return _risk_model


# ── Trend engine (Layer 4A) ───────────────────────────────────────────────────

def _trend_points(history: List[dict], current_waz: Optional[float],
                  current_haz: Optional[float]) -> tuple[int, list]:
    """Compute trend-based risk points from growth history."""
    points = 0
    reasons = []

    if not history or len(history) < 2:
        return 0, []

    # Sort history ascending by date
    hist = sorted(history, key=lambda x: x.get("measurement_date", ""))
    prev = hist[-1]  # most recent prior visit

    prev_waz = prev.get("waz")
    prev_haz = prev.get("haz")

    if current_waz is not None and prev_waz is not None:
        drop = prev_waz - current_waz
        if drop >= 0.5:
            points += 2
            reasons.append(f"WAZ dropped {drop:.2f} SD since last visit (growth faltering)")
        elif drop >= 0.2:
            points += 1
            reasons.append(f"WAZ decreased {drop:.2f} SD since last visit (slow gain)")

    if current_haz is not None and prev_haz is not None:
        drop = prev_haz - current_haz
        if drop >= 0.5:
            points += 2
            reasons.append(f"Height z-score dropped {drop:.2f} SD since last visit")
        elif drop >= 0.2:
            points += 1
            reasons.append(f"Height z-score decreased slightly since last visit")

    return min(points, 3), reasons  # cap at 3


# ── Closeness-to-cutoff (Layer 4B) ───────────────────────────────────────────

def _closeness_points(waz: Optional[float], haz: Optional[float],
                      whz: Optional[float]) -> tuple[int, list]:
    """Award risk points when z-scores are close to malnutrition cut-offs."""
    points = 0
    reasons = []

    def _check(z, label):
        nonlocal points
        if z is None:
            return
        if -2.5 <= z < -2.0:
            points += 2
            reasons.append(f"{label} z-score {z:.2f} is very close to the moderate cut-off")
        elif -2.0 <= z < -1.5:
            points += 1
            reasons.append(f"{label} z-score {z:.2f} is in the watch zone")

    _check(waz, "Weight-for-age")
    _check(haz, "Height-for-age")
    _check(whz, "Weight-for-height")

    return min(points, 2), reasons  # cap at 2


# ── ML risk model (Layer 4C) ─────────────────────────────────────────────────

def _model_points(features: dict) -> tuple[int, list, list]:
    """
    Get risk points from the trained LightGBM model.
    features: dict of all non-anthropometric risk factors.
    Returns (points, reasons, shap_values)
    """
    model = _load_model()
    if model is None:
        return 0, ["ML risk model not yet available (use deterministic rules only)"], []

    try:
        import pandas as pd

        feature_cols = model.get("feature_cols", [])
        lgb_model = model.get("lgb_stunting")
        calibrator = model.get("calibrator_stunting")

        if lgb_model is None:
            return 0, [], []

        row = {col: features.get(col, 0) for col in feature_cols}
        X = pd.DataFrame([row])

        proba = lgb_model.predict_proba(X)[0][1] if hasattr(lgb_model, "predict_proba") else 0.0
        if calibrator is not None:
            proba = float(calibrator.predict([[proba]])[0])

        # Convert probability to points (0-3 scale)
        pts = 0
        if proba >= 0.6:
            pts = 3
        elif proba >= 0.4:
            pts = 2
        elif proba >= 0.25:
            pts = 1

        reasons = []
        if proba >= 0.25:
            reasons.append(f"Context risk model: {proba*100:.0f}% estimated risk of stunting")

        # Lightweight explanation for live requests. SHAP is intentionally kept
        # out of the request path because it imports plotting/font stacks that
        # are slow and brittle in local/demo environments.
        feature_importances = getattr(lgb_model, "feature_importances_", None)
        if feature_importances is not None:
            pairs = sorted(zip(feature_cols, feature_importances), key=lambda x: x[1], reverse=True)[:3]
            for feat, _ in pairs:
                value = row.get(feat)
                if feat == "food_groups" and value is not None and value < 4:
                    reasons.append("Low diet diversity is an important risk driver")
                elif feat == "meals_per_day" and value is not None and value < 3:
                    reasons.append("Low meal frequency is an important risk driver")
                elif feat == "diarrhoea" and value:
                    reasons.append("Recent diarrhoea is an important risk driver")
                elif feat == "wealth_score" and value is not None and value <= 2:
                    reasons.append("Lower household resource score is an important risk driver")
                elif feat == "mother_education" and value is not None and value <= 1:
                    reasons.append("Lower caregiver education is an important risk driver")
                else:
                    reasons.append(f"{feat.replace('_', ' ').title()} contributed to the risk estimate")

        return pts, reasons, []

    except Exception as e:
        return 0, [f"ML model error: {str(e)}"], []


# ── Main future-risk function ─────────────────────────────────────────────────

def compute_future_risk(
    waz: Optional[float],
    haz: Optional[float],
    whz: Optional[float],
    history: Optional[List[dict]] = None,
    context_features: Optional[dict] = None,
) -> dict:
    """
    Combine all four sub-engines into a final risk tier.

    Returns:
        {
          "tier": "LOW" | "WATCH" | "HIGH",
          "total_points": int,
          "breakdown": { "trend": int, "closeness": int, "model": int },
          "reasons": list[str],
          "horizon": str
        }
    """
    trend_pts, trend_reasons = _trend_points(history or [], waz, haz)
    close_pts, close_reasons = _closeness_points(waz, haz, whz)
    model_pts, model_reasons, _ = _model_points(context_features or {})

    total = trend_pts + close_pts + model_pts

    if total >= 6:
        tier = "HIGH"
    elif total >= 3:
        tier = "WATCH"
    else:
        tier = "LOW"

    all_reasons = trend_reasons + close_reasons + model_reasons

    return {
        "tier": tier,
        "total_points": total,
        "breakdown": {
            "trend": trend_pts,
            "closeness": close_pts,
            "model": model_pts,
        },
        "reasons": all_reasons if all_reasons else ["No significant risk factors identified"],
        "horizon": "over the next 3–6 months, if current conditions do not change",
    }
