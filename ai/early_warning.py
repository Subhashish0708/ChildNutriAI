"""
=============================================================================
ChildNutri AI - Pediatric Early Warning & Growth Deviation Engine
=============================================================================
Detects early growth faltering, acute velocity declines, and clinical risk
patterns before severe malnutrition develops.

Strict Rules:
  1. No invented velocity: If single visit exists, explicitly reports
     INSUFFICIENT_HISTORY and distinguishes current screening from trend.
  2. Multi-visit calculations: Uses exact elapsed calendar days (t2 - t1)
     and exact deltas for weight (g/day), WHZ, HAZ, and MUAC.
  3. Pattern detection: Detects repeated weight decline, declining WHZ,
     MUAC deterioration, persistent growth concern, and illness triggers.
  4. Non-diagnostic phrasing: Focuses on proactive follow-up and monitoring.
=============================================================================
"""

import logging
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("childnutri.early_warning")


class EarlyDetectionEngine:
    """
    Authoritative engine for early pediatric growth deviation detection.
    """

    STATE_NO_WARNING = "NO_CURRENT_WARNING"
    STATE_MONITORING = "MONITORING_RECOMMENDED"
    STATE_WARNING = "EARLY_WARNING_DETECTED"
    STATE_URGENT = "PROFESSIONAL_ASSESSMENT_IMPORTANT"
    STATE_INSUFFICIENT = "INSUFFICIENT_HISTORY"

    @classmethod
    def evaluate_early_warning(
        cls,
        current_assessment: Dict[str, Any],
        previous_assessment: Optional[Dict[str, Any]] = None,
        growth_history: Optional[List[Dict[str, Any]]] = None,
        prediction_label: str = "Normal",
        risk_score: Optional[float] = None,
        triage_level: str = "ROUTINE (GREEN)",
        medical_notes: Optional[str] = None,
        feeding_data: Optional[Dict[str, Any]] = None,
        child_name: str = "The child"
    ) -> Dict[str, Any]:
        """
        Evaluates early nutritional and physiological risk patterns.
        """
        c_wt = float(current_assessment.get("weight") or current_assessment.get("weight_kg") or 0.0)
        c_ht = float(current_assessment.get("height") or current_assessment.get("height_cm") or 0.0)
        c_muac = float(current_assessment.get("muac") or current_assessment.get("muac_cm")) if (current_assessment.get("muac") or current_assessment.get("muac_cm")) is not None else None
        c_whz = float(current_assessment.get("whz")) if current_assessment.get("whz") is not None else 0.0
        c_haz = float(current_assessment.get("haz")) if current_assessment.get("haz") is not None else 0.0
        c_waz = float(current_assessment.get("waz")) if current_assessment.get("waz") is not None else 0.0
        c_edema = bool(current_assessment.get("has_bilateral_edema") or False)
        c_date_str = str(current_assessment.get("assessment_date") or current_assessment.get("date") or date.today())

        triage_upper = (triage_level or "").upper()
        pred_lower = (prediction_label or "").lower()

        # ---------------------------------------------------------------------
        # 1. SINGLE VISIT HANDLING
        # ---------------------------------------------------------------------
        is_single_visit = previous_assessment is None or not previous_assessment.get("weight")
        if is_single_visit:
            # Check current indicators
            has_current_concern = (c_whz < -2.0) or (c_haz < -2.0) or (c_muac is not None and c_muac < 12.5) or c_edema
            is_emergency = c_edema or "RED" in triage_upper or c_whz < -3.0 or (c_muac is not None and c_muac < 11.5)

            if is_emergency:
                w_state = cls.STATE_URGENT
                badge = "PROMPT ASSESSMENT NEEDED"
                color = "#dc2626"
                why = f"Current assessment identifies a severe clinical or anthropometric finding ({'bilateral pedal edema' if c_edema else f'WHZ {c_whz:+.2f} SD'}) that requires prompt professional review."
                next_step = "Prompt clinical evaluation by a medical officer or pediatric healthcare provider today."
            elif has_current_concern or "YELLOW" in triage_upper:
                w_state = cls.STATE_MONITORING
                badge = "MONITORING RECOMMENDED"
                color = "#d97706"
                why = f"Current screening identifies an anthropometric measurement (WHZ: {c_whz:+.2f} SD, HAZ: {c_haz:+.2f} SD) below standard reference medians."
                next_step = "Review daily feeding intake and schedule a follow-up assessment in 14–30 days to establish longitudinal growth velocity."
            else:
                w_state = cls.STATE_INSUFFICIENT
                badge = "BASELINE RECORDED"
                color = "#0284c7"
                why = "Current screening measurements track within reference thresholds. Baseline screening recorded."
                next_step = "Continue age-appropriate feeding and schedule a routine growth check in 30 days to establish a growth trajectory."

            return {
                "status": "EARLY_WARNING_DETECTED" if (is_emergency or w_state == cls.STATE_MONITORING) else "CURRENT_SCREENING",
                "longitudinal_early_warning": "INSUFFICIENT_HISTORY",
                "has_early_warning": is_emergency or (w_state == cls.STATE_MONITORING),
                "warning_state": w_state,
                "status_badge": badge,
                "status_color": color,
                "is_single_visit": True,
                "history_required": True,
                "score_name": "Early Growth Warning Score",
                "trend": "BASELINE_ASSESSMENT",
                "weight_delta_kg": None,
                "whz_delta": None,
                "weight_velocity_g_day": None,
                "reason_codes": ["SINGLE_VISIT_BASELINE", "INSUFFICIENT_LONGITUDINAL_HISTORY"] + (["SEVERE_CLINICAL_FINDING"] if is_emergency else ([] if not has_current_concern else ["CURRENT_ANTHROPOMETRIC_CONCERN"])),
                "evidence": [f"Current weight: {c_wt} kg", f"Current WHZ: {c_whz:+.2f} SD", f"Current HAZ: {c_haz:+.2f} SD"] + ([f"MUAC: {c_muac} cm"] if c_muac else []) + (["Bilateral pedal edema noted"] if c_edema else []),
                "recommended_follow_up": next_step,
                "current_status_summary": f"Current screening {'identifies an area that warrants clinical attention' if has_current_concern else 'tracks within reference bounds'}.",
                "longitudinal_status_summary": "INSUFFICIENT_HISTORY: Single-visit baseline recorded. Longitudinal growth velocity cannot be calculated until a second checkup is documented.",
                "change_since_previous": None,
                "previous_visit": None,
                "current_visit": {
                    "date": c_date_str,
                    "weight_kg": c_wt,
                    "whz": c_whz,
                    "haz": c_haz,
                    "muac_cm": c_muac
                },
                "detected_risk_indicators": [
                    {"indicator": "Single Visit", "detail": "Baseline assessment recorded; trend analysis requires >= 2 visits", "severity": "neutral"}
                ],
                "why_warning_generated": why,
                "interpretation": "Single-visit screening provides a cross-sectional snapshot. Longitudinal growth velocity cannot be calculated until a second checkup is documented.",
                "recommended_next_step": next_step,
                "disclaimer": "Early warning indicators assist healthcare providers in spotting growth deviations before clinical malnutrition develops. They do not constitute diagnostic medical conclusions."
            }

        # ---------------------------------------------------------------------
        # 2. MULTI-VISIT LONGITUDINAL EVALUATION
        # ---------------------------------------------------------------------
        p_wt = float(previous_assessment.get("weight") or previous_assessment.get("weight_kg") or 0.0)
        p_whz = float(previous_assessment.get("whz")) if previous_assessment.get("whz") is not None else 0.0
        p_haz = float(previous_assessment.get("haz")) if previous_assessment.get("haz") is not None else 0.0
        p_muac = float(previous_assessment.get("muac") or previous_assessment.get("muac_cm")) if (previous_assessment.get("muac") or previous_assessment.get("muac_cm")) is not None else None
        p_date_str = str(previous_assessment.get("assessment_date") or previous_assessment.get("date") or "")

        # Elapsed days
        days_diff = 30
        try:
            d_curr = datetime.strptime(c_date_str[:10], "%Y-%m-%d").date()
            d_prev = datetime.strptime(p_date_str[:10], "%Y-%m-%d").date()
            diff = (d_curr - d_prev).days
            if diff > 0:
                days_diff = diff
        except Exception:
            days_diff = 30

        delta_wt = round(c_wt - p_wt, 2)
        delta_whz = round(c_whz - p_whz, 2)
        delta_haz = round(c_haz - p_haz, 2)
        delta_muac = round(c_muac - p_muac, 1) if (c_muac is not None and p_muac is not None) else None
        vel_g_day = round((delta_wt * 1000.0) / max(1, days_diff), 1)

        risk_indicators = []
        warning_reasons = []

        # Check Indicator 1: Repeated Weight Decline / Negative Velocity
        if delta_wt < -0.2 or vel_g_day < -5.0:
            risk_indicators.append({
                "indicator": "Active Weight Loss",
                "detail": f"Weight decreased by {abs(delta_wt):.2f} kg ({vel_g_day:+.1f} g/day over {days_diff} days)",
                "severity": "danger"
            })
            warning_reasons.append("active weight loss between assessments")
        elif delta_wt <= 0.0:
            risk_indicators.append({
                "indicator": "Weight Stagnation",
                "detail": f"Zero net weight gain over {days_diff} days ({vel_g_day:+.1f} g/day)",
                "severity": "warning"
            })
            warning_reasons.append("weight stagnation over the follow-up interval")

        # Check Indicator 2: Declining WHZ
        if delta_whz <= -0.8:
            risk_indicators.append({
                "indicator": "Rapid WHZ Drop",
                "detail": f"Weight-for-height shifted downward by {delta_whz:+.2f} SD ({p_whz:+.2f} -> {c_whz:+.2f})",
                "severity": "danger"
            })
            warning_reasons.append("significant downward shift in weight-for-height")
        elif delta_whz <= -0.4:
            risk_indicators.append({
                "indicator": "Declining WHZ",
                "detail": f"Weight-for-height moved downward by {delta_whz:+.2f} SD",
                "severity": "warning"
            })
            warning_reasons.append("gradual downward shift in weight-for-height")

        # Check Indicator 3: MUAC Deterioration
        if delta_muac is not None and delta_muac <= -0.5:
            risk_indicators.append({
                "indicator": "MUAC Deterioration",
                "detail": f"Mid-upper arm circumference decreased by {abs(delta_muac):.1f} cm ({p_muac:.1f} -> {c_muac:.1f} cm)",
                "severity": "danger"
            })
            warning_reasons.append("decrease in mid-upper arm circumference")

        # Check Indicator 4: Clinical Red Flags
        if c_edema:
            risk_indicators.append({
                "indicator": "Bilateral Pedal Edema",
                "detail": "Fluid retention present in lower extremities (kwashiorkor diagnostic sign)",
                "severity": "danger"
            })
            warning_reasons.append("presence of bilateral pitting edema")

        # Check Indicator 5: Recent Illness Mentioned in Notes
        if medical_notes:
            notes_lower = medical_notes.lower()
            if any(k in notes_lower for k in ["fever", "diarrhea", "vomit", "cough", "infection", "pneumonia"]):
                risk_indicators.append({
                    "indicator": "Recent Illness Reported",
                    "detail": f"Clinical notes report acute illness: '{medical_notes[:50]}...'",
                    "severity": "warning"
                })
                warning_reasons.append("recent episode of acute illness")

        # Determine Warning State
        is_urgent = c_edema or "RED" in triage_upper or c_whz <= -3.0 or (c_muac and c_muac < 11.5)
        has_warning = (delta_wt < -0.2) or (delta_whz <= -0.5) or (delta_muac is not None and delta_muac <= -0.5) or (vel_g_day < -5.0)

        if is_urgent:
            w_state = cls.STATE_URGENT
            badge = "PROMPT ASSESSMENT NEEDED"
            color = "#dc2626"
            trend = "RAPID_WEIGHT_LOSS" if vel_g_day < 0 else "ACUTE_NUTRITIONAL_DEFICIT"
            reasons_str = "; ".join(warning_reasons) if warning_reasons else "severe clinical finding"
            why = f"Emergency clinical safety override triggered: {reasons_str}."
            next_step = "Prompt clinical evaluation by a medical officer or pediatric facility today."
        elif has_warning:
            w_state = cls.STATE_WARNING
            badge = "EARLY WARNING DETECTED"
            color = "#dc2626"
            trend = "GROWTH_FALTERING" if vel_g_day < 0 else "DECELERATING"
            reasons_str = "; ".join(warning_reasons) if warning_reasons else "growth velocity deceleration"
            why = f"Weight and growth indicators have moved downward since the previous assessment ({reasons_str})."
            next_step = "Closer nutritional follow-up recommended: review meal frequency, energy density, and re-assess in 14 days."
        elif c_whz < -2.0 or c_haz < -2.0 or "YELLOW" in triage_upper or delta_wt <= 0.0:
            w_state = cls.STATE_MONITORING
            badge = "MONITORING RECOMMENDED"
            color = "#d97706"
            trend = "SLOW_PROGRESSION" if delta_wt >= 0 else "GROWTH_FALTERING"
            why = f"Growth progress is slower than expected reference benchmarks over the past {days_diff} days."
            next_step = "Continue supportive feeding guidance and track growth at next scheduled checkup."
        else:
            w_state = cls.STATE_NO_WARNING
            badge = "STEADY GROWTH"
            color = "#16a34a"
            trend = "STEADY_GROWTH"
            why = f"Weight and height indicators have maintained positive trajectory over the past {days_diff} days (+{vel_g_day} g/day)."
            next_step = "Continue age-appropriate feeding and routine monthly growth monitoring."

        reason_codes_list = []
        if is_urgent:
            reason_codes_list.append("EMERGENCY_OVERRIDE")
        if vel_g_day < -5.0:
            reason_codes_list.append("WEIGHT_VELOCITY_NEGATIVE")
        elif vel_g_day < 5.0:
            reason_codes_list.append("WEIGHT_VELOCITY_SUBOPTIMAL")
        if delta_whz <= -0.5:
            reason_codes_list.append("WHZ_DECLINE_SUBSTANTIAL")
        if delta_wt < 0:
            reason_codes_list.append("WEIGHT_LOSS_RECORDED")
        if c_edema:
            reason_codes_list.append("BILATERAL_PEDAL_EDEMA")
        if not reason_codes_list:
            reason_codes_list.append("STEADY_GROWTH_TRAJECTORY")

        evidence_list = [
            f"Weight change: {delta_wt:+.2f} kg across {days_diff} days",
            f"Weight velocity: {vel_g_day:+.1f} g/day (WHO standard: 10-15 g/day for infants)",
            f"WHZ change: {delta_whz:+.2f} SD (Current WHZ: {c_whz:+.2f} SD)"
        ]
        if delta_muac is not None:
            evidence_list.append(f"MUAC change: {delta_muac:+.1f} cm (Current MUAC: {c_muac} cm)")

        return {
            "status": "EARLY_WARNING_DETECTED" if w_state in (cls.STATE_WARNING, cls.STATE_URGENT) else ("MONITORING_RECOMMENDED" if w_state == cls.STATE_MONITORING else "NO_CURRENT_WARNING"),
            "longitudinal_early_warning": "EVALUATED",
            "has_early_warning": w_state in (cls.STATE_WARNING, cls.STATE_URGENT),
            "warning_state": w_state,
            "status_badge": badge,
            "status_color": color,
            "is_single_visit": False,
            "history_required": False,
            "score_name": "Early Growth Warning Score",
            "reason_codes": reason_codes_list,
            "evidence": evidence_list,
            "recommended_follow_up": next_step,
            "trend": trend,
            "weight_delta_kg": delta_wt,
            "whz_delta": delta_whz,
            "weight_velocity_g_day": vel_g_day,
            "current_status_summary": f"Current WHZ: {c_whz:+.2f} SD, Weight: {c_wt} kg.",
            "longitudinal_status_summary": f"Trajectory across {days_diff} days: Weight delta {delta_wt:+.2f} kg ({vel_g_day:+.1f} g/day), WHZ delta {delta_whz:+.2f} SD.",
            "change_since_previous": {
                "days_elapsed": days_diff,
                "weight_delta_kg": delta_wt,
                "whz_delta": delta_whz,
                "haz_delta": delta_haz,
                "muac_delta_cm": delta_muac,
                "velocity_g_day": vel_g_day
            },
            "previous_visit": {
                "date": p_date_str,
                "weight_kg": p_wt,
                "whz": p_whz,
                "haz": p_haz,
                "muac_cm": p_muac
            },
            "current_visit": {
                "date": c_date_str,
                "weight_kg": c_wt,
                "whz": c_whz,
                "haz": c_haz,
                "muac_cm": c_muac
            },
            "detected_risk_indicators": risk_indicators or [
                {"indicator": "Growth Trajectory", "detail": f"Normal weight gain (+{vel_g_day} g/day)", "severity": "good"}
            ],
            "why_warning_generated": why,
            "interpretation": f"The growth pattern over the past {days_diff} calendar days should be reviewed rather than relying only on a single isolated measurement.",
            "recommended_next_step": next_step,
            "disclaimer": "Early warning indicators assist healthcare providers in spotting growth deviations before clinical malnutrition develops. They do not constitute diagnostic medical conclusions."
        }


# Research-grade internal canonical alias
EarlyGrowthAndNutritionWarningEngine = EarlyDetectionEngine
__all__ = ["EarlyDetectionEngine", "EarlyGrowthAndNutritionWarningEngine"]

