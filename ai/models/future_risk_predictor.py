from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional

WHO_WEIGHT_MEDIAN_KG = {
    6: 7.9, 9: 9.2, 12: 9.6, 15: 10.2, 18: 10.8, 21: 11.3, 24: 12.2,
    30: 13.3, 36: 14.3, 42: 15.3, 48: 16.3, 54: 17.3, 60: 18.3
}

WHO_HEIGHT_MEDIAN_CM = {
    6: 67.6, 9: 72.0, 12: 75.7, 15: 79.1, 18: 82.3, 21: 85.1, 24: 87.8,
    30: 92.7, 36: 96.1, 42: 99.9, 48: 103.3, 54: 107.0, 60: 110.0
}

def _interp_who(table, age):
    keys = sorted(table.keys())
    if age <= keys[0]: return table[keys[0]]
    if age >= keys[-1]: return table[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= age <= keys[i+1]:
            t = (age - keys[i]) / (keys[i+1] - keys[i])
            return table[keys[i]] + t * (table[keys[i+1]] - table[keys[i]])
    return 10.0

def _classify_risk(weight_deficit_pct, forecast_muac, velocity_trend, current_risk_score, horizon_days: int = 30):
    factor = horizon_days / 30.0
    score = current_risk_score

    if velocity_trend == "Deteriorating":
        score = min(100.0, score + 4.5 * factor)
    elif velocity_trend == "Recovering":
        score = max(5.0, score - 3.8 * factor)

    if weight_deficit_pct > 30:
        score = min(100.0, score + 2.0 * factor)
    elif weight_deficit_pct > 20:
        score = min(100.0, score + 1.0 * factor)
    elif weight_deficit_pct < 10:
        score = max(5.0, score - 2.0 * factor)

    if forecast_muac is not None:
        if forecast_muac < 11.5:
            score = min(100.0, score + 3.0 * factor)
        elif forecast_muac < 12.5:
            score = min(100.0, score + 1.5 * factor)
        elif forecast_muac > 13.5:
            score = max(5.0, score - 2.0 * factor)

    score = round(max(0.0, min(100.0, score)), 1)
    if score >= 70:
        return {"tier": "High", "score": score, "color": "#ef4444",
                "action": "Immediate clinical intervention required. Refer to PHC/hospital.", "urgency": "URGENT"}
    elif score >= 40:
        return {"tier": "Medium", "score": score, "color": "#f59e0b",
                "action": "Increase monitoring frequency. Dietary intervention recommended.", "urgency": "MONITOR"}
    else:
        return {"tier": "Low", "score": score, "color": "#10b981",
                "action": "Continue routine monitoring. Maintain current nutrition plan.", "urgency": "ROUTINE"}


class FutureRiskPredictor:
    """Forecasts child malnutrition trajectory for Day +30, +60, +90 (Experimental Future Risk Projection)."""

    @staticmethod
    def predict_future_risk(
        growth_history: List[Dict[str, Any]],
        current_age_months: float,
        current_weight: float,
        current_height: float,
        current_muac: Optional[float],
        current_risk_score: float,
        gender: str = "Male"
    ) -> Dict[str, Any]:

        valid_history = [
            h for h in (growth_history or [])
            if h.get("weight") is not None or h.get("weight_kg") is not None
        ]

        # REQUIREMENT 16: If fewer than 2 assessments exist, DO NOT fabricate trajectory.
        if len(valid_history) < 2:
            return {
                "available": False,
                "status": "insufficient_history",
                "projection_type": "Experimental Future Risk Projection",
                "has_sufficient_history": False,
                "message": "Insufficient longitudinal history. At least 2 clinical visits are required to compute a growth trajectory forecast.",
                "forecasts": [],
                "chart_data": [{
                    "age_months": round(float(current_age_months), 1),
                    "weight_kg": round(float(current_weight), 2),
                    "height_cm": round(float(current_height), 1),
                    "type": "actual"
                }]
            }

        # Multiple historical records exist -> fit genuine regression trend
        history = list(valid_history)
        ages = np.array([float(h.get("age_months", 0)) for h in history])
        weights = np.array([float(h.get("weight_kg", h.get("weight", current_weight))) for h in history])
        heights = np.array([float(h.get("height_cm", h.get("height", current_height))) for h in history])
        muacs_raw = [float(h.get("muac_cm", h["muac"])) for h in history if h.get("muac") is not None or h.get("muac_cm") is not None]

        weight_coeffs = np.polyfit(ages, weights, deg=min(1, len(ages)-1))
        height_coeffs = np.polyfit(ages, heights, deg=min(1, len(ages)-1))

        muac_coeffs = None
        if len(muacs_raw) >= 2:
            muac_ages = ages[:len(muacs_raw)]
            muac_coeffs = np.polyfit(muac_ages, np.array(muacs_raw), deg=1)

        weight_slope = float(weight_coeffs[0])
        expected_vel = 0.25 if current_age_months <= 12 else 0.15
        if weight_slope >= expected_vel * 0.8:   velocity_trend = "Recovering"
        elif weight_slope >= 0.0:                 velocity_trend = "Stable"
        else:                                     velocity_trend = "Deteriorating"

        forecasts = []
        horizon_days_map = {"30 Days": 30, "60 Days": 60, "90 Days": 90}
        for label, delta in zip(["30 Days", "60 Days", "90 Days"], [1.0, 2.0, 3.0]):
            fa = current_age_months + delta
            fw = max(float(np.polyval(weight_coeffs, fa)), 2.5)
            fh = max(float(np.polyval(height_coeffs, fa)), 45.0)
            fm = None
            if muac_coeffs is not None:
                fm = max(float(np.polyval(muac_coeffs, fa)), 9.0)
            elif current_muac is not None:
                slope = -0.05 if velocity_trend == "Deteriorating" else 0.03
                fm = current_muac + slope * delta

            who_w = _interp_who(WHO_WEIGHT_MEDIAN_KG, fa)
            def_pct = max(0.0, (who_w - fw) / who_w * 100)

            h_days = horizon_days_map[label]
            h_risk = _classify_risk(def_pct, fm, velocity_trend, current_risk_score, horizon_days=h_days)

            forecasts.append({
                "horizon": label,
                "horizon_days": h_days,
                "age_months": round(fa, 1),
                "weight_kg": round(fw, 2),
                "height_cm": round(fh, 1),
                "muac_cm": round(fm, 1) if fm else None,
                "weight_deficit_pct": round(def_pct, 1),
                "who_weight_median_kg": round(who_w, 2),
                "is_muac_critical": (fm is not None and fm < 11.5),
                "projected_risk_score": h_risk["score"],
                "risk_tier": h_risk["tier"],
                "risk_color": h_risk["color"],
                "recommended_action": h_risk["action"]
            })

        chart_data = []
        for h in history:
            chart_data.append({
                "age_months": round(float(h.get("age_months", 0)), 1),
                "weight_kg": round(float(h.get("weight_kg", h.get("weight", 0))), 2),
                "height_cm": round(float(h.get("height_cm", h.get("height", 0))), 1),
                "type": "actual"
            })
        for f in forecasts:
            chart_data.append({
                "age_months": f["age_months"],
                "weight_kg": f["weight_kg"],
                "height_cm": f["height_cm"],
                "type": "forecast"
            })

        return {
            "available": True,
            "status": "available",
            "projection_type": "Experimental Future Risk Projection",
            "has_sufficient_history": True,
            "current_risk_score": current_risk_score,
            "velocity_trend": velocity_trend,
            "weight_velocity_kg_per_month": round(weight_slope, 3),
            "forecasts": forecasts,
            "chart_data": chart_data,
            "disclaimer": "Experimental Future Risk Projection based on linear regression across recorded visits. Intended for clinical decision support only."
        }
