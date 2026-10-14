"""
=============================================================================
Composite Screening Risk Score (0–100) Model - ChildNutri AI Phase 4
=============================================================================
Methodology & Formulation:
  Synthesizes multi-source evidence into a continuous 0.0 - 100.0 decision-support
  prioritization score combining:
    1. Tabular ML Ensemble Severity & Probability (40% Weight, 0-40 pts)
    2. WHO Anthropometric Deficits (HAZ, WAZ, WHZ) (30% Weight, 0-30 pts)
    3. Peripheral Acute Wasting via MUAC Cutoffs   (20% Weight, 0-20 pts)
    4. Longitudinal Velocity Degradation / Faltering(10% Weight, 0-10 pts)

Terminology & Calibration Mandate:
  This score is an uncalibrated, heuristic multi-factorial index.
  It is NOT a "calibrated probability" or "diagnostic probability".
  The official name is strictly: "Composite Screening Risk Score (0-100)".
  Missing measurements are NOT silently imputed as ideal medians (Z=0.0).

Medical Safety Boundary:
  This composite screening score is a decision-support metric.
  It is not a diagnostic probability and has not been clinically validated.
  It is intended solely for triage prioritization in community settings.
=============================================================================
"""

from typing import Dict, Any, Optional, List

class ContinuousRiskScorer:
    """
    Computes a deterministic 0.0 - 100.0 Composite Screening Risk Score.
    Transparent about missing components and avoids artificial reassurance.
    """

    @classmethod
    def compute_composite_risk_score(
        cls,
        prediction_label: Optional[str] = None,
        confidence: Optional[float] = None,
        haz: Optional[float] = None,
        waz: Optional[float] = None,
        whz: Optional[float] = None,
        muac: Optional[float] = None,
        is_faltering_velocity: bool = False,
        iap_assessment: Optional[Dict[str, Any]] = None,
        age_months: Optional[float] = None,
        has_bilateral_edema: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates the composite screening risk score deterministically.
        Handles missing inputs honestly without defaulting to zero or normal.
        """
        # Immediate escalation for bilateral edema (nutritional emergency across all ages)
        if has_bilateral_edema:
            return {
                "status": "CALCULATED",
                "risk_score": 100.0,
                "risk_score_name": "Composite Screening Risk Score (0-100)",
                "risk_tier": "CRITICAL / HIGH RISK (Immediate Clinical Attention Required)",
                "color_hex": "#dc2626",
                "component_breakdown": {
                    "clinical_emergency": 100.0,
                    "reason": "Bilateral pedal edema is a clinical emergency requiring immediate inpatient triage."
                },
                "clinical_disclaimer": (
                    "This composite screening score is a decision-support metric. "
                    "It is not a diagnostic probability and has not been clinically validated."
                )
            }

        # Check for completely absent intake data
        has_haz = (haz is not None and isinstance(haz, (int, float)))
        has_waz = (waz is not None and isinstance(waz, (int, float)))
        has_whz = (whz is not None and isinstance(whz, (int, float)))
        has_muac = (muac is not None and isinstance(muac, (int, float)) and muac > 0)
        has_ml = (prediction_label is not None and str(prediction_label).strip() not in ["", "None", "UNABLE_TO_ASSESS", "INSUFFICIENT_DATA", "Unclassified"])

        if not has_haz and not has_waz and not has_whz and not has_muac and not has_ml and not iap_assessment:
            return {
                "status": "DATA_INSUFFICIENT",
                "risk_score": None,
                "risk_score_name": "Composite Screening Risk Score (0-100)",
                "risk_tier": "INSUFFICIENT_DATA (Assessment Incomplete)",
                "color_hex": "#9ca3af",
                "component_breakdown": {
                    "status": "UNABLE_TO_CALCULATE",
                    "reason": "Anthropometric measurements missing or uncalculable."
                },
                "clinical_disclaimer": (
                    "This composite screening score is a decision-support metric. "
                    "It is not a diagnostic probability and has not been clinically validated."
                )
            }

        conf_val = max(0.0, min(1.0, float(confidence))) if (confidence is not None and isinstance(confidence, (int, float))) else 0.5
        velocity_points = 10.0 if bool(is_faltering_velocity) else 0.0

        # ---------------------------------------------------------------------
        # COHORT BRANCHING: 5-18 Years (IAP 2015 Standard)
        # ---------------------------------------------------------------------
        if (age_months is not None and age_months >= 60.0) or iap_assessment:
            iap = iap_assessment or {}
            bmi_cat = str(iap.get("bmi_category", "")).lower()
            overall = str(iap.get("overall_category", "")).lower()

            # BMI status severity points (0-50 pts)
            if iap.get("is_obese") or "obese" in bmi_cat or "obese" in overall:
                bmi_pts = 45.0
            elif iap.get("is_overweight") or "overweight" in bmi_cat or "overweight" in overall:
                bmi_pts = 30.0
            elif iap.get("is_underweight") or "thinness" in bmi_cat or "wasted" in overall:
                bmi_pts = 40.0
            elif bmi_cat or overall:
                bmi_pts = 5.0
            else:
                bmi_pts = 0.0

            # Linear Stunting / Underweight Z-score deficit (0-40 pts)
            haz_pts = max(0.0, -float(haz)) * 7.0 if has_haz else 0.0
            waz_pts = max(0.0, -float(waz)) * 6.0 if has_waz else 0.0
            deficit_pts = min(40.0, haz_pts + waz_pts)

            total_raw = bmi_pts + deficit_pts + velocity_points
            final_score = round(max(0.0, min(100.0, total_raw)), 1)

            if final_score >= 80.0:
                tier = "CRITICAL / HIGH RISK (Immediate Clinical Attention Required)"
                color = "#dc2626"
            elif final_score >= 60.0:
                tier = "MODERATE RISK (Therapeutic Monitoring Required)"
                color = "#ea580c"
            elif final_score >= 35.0:
                tier = "MILD / VULNERABLE (Dietary Counseling Recommended)"
                color = "#d97706"
            else:
                tier = "LOW / NORMAL (Healthy Growth Tracking)"
                color = "#16a34a"

            return {
                "status": "CALCULATED",
                "risk_score": final_score,
                "risk_score_name": "Composite Screening Risk Score (0-100)",
                "risk_tier": tier,
                "color_hex": color,
                "component_breakdown": {
                    "iap_bmi_category_points": round(bmi_pts, 1),
                    "iap_zscore_deficit_points": round(deficit_pts, 1),
                    "velocity_faltering_points": round(velocity_points, 1),
                    "muac_points": 0.0
                },
                "clinical_disclaimer": (
                    "This composite screening score is a decision-support metric. "
                    "It is not a diagnostic probability and has not been clinically validated."
                )
            }

        # ---------------------------------------------------------------------
        # COHORT BRANCHING: Under-5 Years (WHO Child Growth Standards + ML)
        # ---------------------------------------------------------------------
        # 1. ML Tabular Ensemble Severity (0 - 40 points)
        # ---------------------------------------------------------------------
        base_severity_weights = {
            "Severe (SAM)": 38.0,
            "Severe": 38.0,
            "SAM": 38.0,
            "Wasted": 30.0,
            "Moderate": 30.0,
            "Stunted": 28.0,
            "Underweight": 20.0,
            "Normal": 3.0
        }
        norm_label = str(prediction_label or "").strip()
        matched_weight = None
        for k, v in base_severity_weights.items():
            if k.lower() in norm_label.lower():
                matched_weight = v
                break

        if matched_weight is not None:
            ml_points = matched_weight * (0.60 + 0.40 * conf_val)
        else:
            # If no ML label provided, ML points are 0.0 rather than an arbitrary default
            ml_points = 0.0

        # ---------------------------------------------------------------------
        # 2. WHO Anthropometric Deficits (0 - 30 points)
        # Sum of negative Z-score deviations below median for available indicators
        # ---------------------------------------------------------------------
        z_deficit = 0.0
        active_z_count = 0
        if has_haz:
            z_deficit += max(0.0, -float(haz)) * 3.5
            active_z_count += 1
        if has_waz:
            z_deficit += max(0.0, -float(waz)) * 3.5
            active_z_count += 1
        if has_whz:
            z_deficit += max(0.0, -float(whz)) * 4.0
            active_z_count += 1

        who_points = min(30.0, z_deficit)

        # ---------------------------------------------------------------------
        # 3. MUAC Acute Emergency Distance Penalty (0 - 20 points)
        # ---------------------------------------------------------------------
        muac_points = 0.0
        if has_muac:
            m_val = float(muac)
            if m_val < 11.5:
                # Severe acute wasting: 15.0 to 20.0 points
                muac_points = min(20.0, max(15.0, 20.0 - (m_val - 8.0) * 1.5))
            elif m_val < 12.5:
                # Moderate acute wasting: 10.0 to 14.0 points
                muac_points = 10.0 + (12.5 - m_val) * 4.0
            elif m_val < 13.5:
                # Mild vulnerability
                muac_points = 4.0

        # ---------------------------------------------------------------------
        # Composite Calculation & Bounding (0.0 - 100.0)
        # ---------------------------------------------------------------------
        total_raw = ml_points + who_points + muac_points + velocity_points
        final_score = round(max(0.0, min(100.0, total_raw)), 1)

        # Clinical Tiers
        if final_score >= 80.0:
            tier = "CRITICAL / HIGH RISK (Immediate Clinical Attention Required)"
            color = "#dc2626"
        elif final_score >= 60.0:
            tier = "MODERATE RISK (Therapeutic Monitoring Required)"
            color = "#ea580c"
        elif final_score >= 35.0:
            tier = "MILD / VULNERABLE (Dietary Counseling Recommended)"
            color = "#d97706"
        else:
            tier = "LOW / NORMAL (Healthy Growth Tracking)"
            color = "#16a34a"

        missing_components: List[str] = []
        if not has_ml:
            missing_components.append("ML Model Prediction")
        if not has_whz:
            missing_components.append("WHZ")
        if not has_haz:
            missing_components.append("HAZ")
        if not has_waz:
            missing_components.append("WAZ")
        if not has_muac:
            missing_components.append("MUAC")

        return {
            "status": "CALCULATED",
            "risk_score": final_score,
            "risk_score_name": "Composite Screening Risk Score (0-100)",
            "risk_tier": tier,
            "color_hex": color,
            "component_breakdown": {
                "ml_probabilistic_points": round(ml_points, 1),
                "who_zscore_deficit_points": round(who_points, 1),
                "muac_emergency_points": round(muac_points, 1),
                "velocity_faltering_points": round(velocity_points, 1),
                "unmeasured_components": missing_components
            },
            "clinical_disclaimer": (
                "This composite screening score is a decision-support metric. "
                "It is not a diagnostic probability and has not been clinically validated."
            )
        }

if __name__ == "__main__":
    scorer = ContinuousRiskScorer()
    res = scorer.compute_composite_risk_score(
        prediction_label="Stunted",
        confidence=0.92,
        haz=-2.8,
        waz=-2.2,
        whz=-1.4,
        muac=11.5,
        is_faltering_velocity=True
    )
    print("Composite Screening Risk Score Output:")
    for k, v in res.items():
        print(f"  {k}: {v}")
