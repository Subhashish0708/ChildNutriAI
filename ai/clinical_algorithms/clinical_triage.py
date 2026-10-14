"""
=============================================================================
Rule-Based Clinical Decision & Safety Triage Engine - ChildNutri AI Phase 4
=============================================================================
Academic Protocols & Guidelines:
  • WHO Guideline: Updates on the management of severe acute malnutrition
    in infants and children. Geneva: World Health Organization; 2013.
  • WHO/UNICEF Joint Statement: Child growth standards and the identification
    of severe acute malnutrition in infants and children (2009).
  • WHO Integrated Management of Childhood Illness (IMCI) Clinical Protocols.
  • IAP 2015 Revised Growth Charts (Khadilkar et al., Indian Pediatrics).

7 Separated Architectural Concepts:
  1. Data Quality Status (DATA_VALID, DATA_INCOMPLETE, BIOLOGICAL_OUTLIER_DETECTED)
  2. Growth Indicators (WHZ, HAZ, WAZ, BAZ, MUAC, edema)
  3. Reference Interpretation (WHO 2006 / IAP 2015 criteria)
  4. Model Estimates (ML ensemble prediction, confidence)
  5. Overall Screening Status (AT_RISK, LOW_RISK, REVIEW_REQUIRED, ASSESSMENT_INCOMPLETE)
  6. Recommended Follow-up (Non-prescriptive guidance with explicit timeframes)
  7. Human Review Status (REQUIRED, RECOMMENDED, ROUTINE)

Cardinal Safety Rule:
  Machine Learning predictions MUST NEVER override clinical red flags.
  If bilateral pitting edema, MUAC < 11.5 cm (6-59m), or WHZ < -3.0 SD is present,
  clinical safety triage forces an immediate URGENT (RED) emergency referral,
  regardless of what the ML ensemble outputs.

Medical Safety Boundary:
  ChildNutri AI is a screening and clinical decision-support prototype.
  It does not provide a medical diagnosis or autonomously prescribe medications
  or therapeutic dosages. All treatment prescriptions must be made by a licensed
  healthcare professional.
=============================================================================
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("childnutri.clinical_triage")

RULES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinical_rules.json")

class ClinicalTriageEngine:
    """
    Deterministic clinical safety layer overriding probabilistic ML output
    when severe medical red flags or emergency criteria are met.
    Implements explicit separation of data quality, reference interpretation,
    screening status, follow-up guidance, and human review status.
    """

    @classmethod
    def evaluate_triage(
        cls,
        age_months: Optional[float],
        weight: Optional[float],
        height: Optional[float],
        muac: Optional[float] = None,
        has_bilateral_edema: bool = False,
        appetite_test_pass: bool = True,
        medical_complications: bool = False,
        whz: Optional[float] = None,
        haz: Optional[float] = None,
        waz: Optional[float] = None,
        prediction_label: Optional[str] = None,
        confidence: Optional[float] = None,
        iap_assessment: Optional[Dict[str, Any]] = None,
        data_quality_issues: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive clinical safety triage evaluating emergency red flags,
        moderate malnutrition/growth risks, and discrepancy between ML and clinical standards.
        Age-aware: Under-5 evaluates WHO/IMCI guidelines; 5-18 evaluates IAP 2015 criteria.
        """
        red_flags: List[str] = []
        moderate_flags: List[str] = []
        action_plan: List[str] = []
        data_warnings: List[str] = list(data_quality_issues or [])

        # ---------------------------------------------------------------------
        # 0. INPUT DATA VALIDATION & BIOLOGICAL PLAUSIBILITY CHECK
        # ---------------------------------------------------------------------
        if age_months is None or weight is None or height is None:
            data_warnings.append("Essential anthropometric measurements (age, weight, or height) are missing.")
            return {
                "status": "available",
                "level": "REVIEW_REQUIRED (AMBER)",
                "triage_level": "REVIEW_REQUIRED (AMBER)",
                "is_emergency": False,
                "color": "#d97706",
                "flags": data_warnings,
                "red_flags": [],
                "reasons": ["Essential clinical measurements are incomplete; triage requires complete anthropometric profile."],
                "facility_referral": "Primary Health Centre / Community Health Worker",
                "action_plan": ["Complete physical measurements (weight, recumbent length/height, MUAC) using calibrated clinical equipment."],
                "action": "Complete physical measurements using calibrated clinical equipment before clinical triage interpretation.",
                "referral_recommended": False,
                "treatment_prescription": False,
                "discrepancy_detected": False,
                "discrepancy_note": None,
                # 7 Concepts Separation
                "data_quality_status": "DATA_INCOMPLETE",
                "growth_indicators": {
                    "whz": whz, "haz": haz, "waz": waz, "muac": muac, "has_bilateral_edema": has_bilateral_edema
                },
                "reference_interpretation": "Incomplete data — unable to calculate growth percentiles",
                "model_estimates": {
                    "prediction_label": prediction_label, "confidence": confidence, "status": "INSUFFICIENT_INPUTS"
                },
                "screening_status": "ASSESSMENT_INCOMPLETE",
                "recommended_followup": {
                    "action": "Complete anthropometric intake using calibrated pediatric equipment.",
                    "timeframe": "Prompt (re-measurement required)",
                    "facility": "Primary Health Centre / Anganwadi"
                },
                "human_review_status": "REQUIRED",
                "followup_timeframe": "Prompt (re-measurement required)",
                "safety_disclaimer": "ChildNutri AI is a screening and clinical decision-support prototype. It does not provide medical diagnoses or prescribe medications."
            }

        # Check for Extreme Biological Outliers (|Z| > 5.0 SD)
        outlier_flags: List[str] = []
        for z_name, z_val in [("WHZ", whz), ("HAZ", haz), ("WAZ", waz)]:
            if z_val is not None and abs(z_val) > 5.0:
                outlier_flags.append(f"{z_name} ({z_val:+.2f} SD)")

        is_under_5 = (age_months < 60.0)
        is_emergency = False
        triage_level = "ROUTINE (GREEN)"
        facility = "Community Health Post / Home"
        color = "#16a34a"
        human_review = "ROUTINE"
        followup_timeframe = "Routine monthly screening (30 days)"
        screening_status = "LOW_RISK"
        ref_interpretation = "All measured growth parameters track within reference parameters."

        # ---------------------------------------------------------------------
        # 1. EMERGENCY RED FLAGS (Rule-based clinical overrides)
        # ---------------------------------------------------------------------
        # Red Flag 1: Bilateral Pitting Edema (Kwashiorkor hallmark) - applicable to ALL ages
        if has_bilateral_edema:
            red_flags.append("Bilateral Pitting Edema (+ / ++ / +++)")
            is_emergency = True
            triage_level = "URGENT (RED)"
            facility = "Nutrition Rehabilitation Centre (NRC) / Hospital Inpatient"
            color = "#dc2626"
            action_plan.append("Urgent clinical evaluation/referral recommended.")
            action_plan.append("Inpatient medical stabilization should follow current WHO/national clinical guidelines under medical officer supervision.")
            human_review = "REQUIRED"
            followup_timeframe = "Immediate (within 24–48 hours)"
            screening_status = "AT_RISK"
            ref_interpretation = "Clinical emergency: Bilateral pedal edema indicates severe acute malnutrition regardless of anthropometric measurements."

        # Red Flag 2: Critical MUAC Threshold (< 11.5 cm) - strictly for children 6 to 59 months
        elif is_under_5 and age_months >= 6.0 and muac is not None and muac < 11.5:
            red_flags.append(f"MUAC critically low ({muac:.1f} cm < 11.5 cm threshold)")
            is_emergency = True
            triage_level = "URGENT (RED)"
            color = "#dc2626"
            human_review = "REQUIRED"
            screening_status = "AT_RISK"
            ref_interpretation = f"Severe Acute Malnutrition (SAM): MUAC {muac:.1f} cm is below 11.5 cm emergency threshold."
            if not appetite_test_pass or medical_complications:
                facility = "Nutrition Rehabilitation Centre (NRC) / Hospital Inpatient"
                action_plan.append("Urgent clinical evaluation/referral recommended.")
                action_plan.append("Inpatient admission required for complicated Severe Acute Malnutrition (SAM).")
                followup_timeframe = "Immediate inpatient evaluation (within 24–48 hours)"
            else:
                facility = "Outpatient Therapeutic Programme (OTP) / Primary Health Centre"
                action_plan.append("Urgent clinical evaluation/referral recommended.")
                action_plan.append("Outpatient therapeutic management under qualified healthcare supervision per national CMAM protocol.")
                followup_timeframe = "Urgent outpatient evaluation (within 48–72 hours)"

        # Red Flag 3: Severe Wasting by WHZ (< -3.0 SD) - strictly for under-5
        elif is_under_5 and whz is not None and whz < -3.0:
            red_flags.append(f"Severe Wasting: WHZ critically low ({whz:.2f} SD < -3.0 SD threshold)")
            is_emergency = True
            triage_level = "URGENT (RED)"
            facility = "Nutrition Rehabilitation Centre (NRC) / Medical Officer"
            color = "#dc2626"
            action_plan.append("Urgent clinical evaluation/referral recommended.")
            action_plan.append("Comprehensive pediatric diagnostic workup and therapeutic nutrition evaluation indicated.")
            human_review = "REQUIRED"
            followup_timeframe = "Urgent evaluation (within 48–72 hours)"
            screening_status = "AT_RISK"
            ref_interpretation = f"Severe Wasting (SAM): Weight-for-Height Z-score ({whz:.2f} SD) is below -3.0 SD cutoff."

        # ---------------------------------------------------------------------
        # 1.5. EXTREME BIOLOGICAL OUTLIERS (Measurements requiring physical verification)
        # ---------------------------------------------------------------------
        elif outlier_flags:
            triage_level = "REVIEW_REQUIRED (AMBER)"
            facility = "Pediatric Clinic / PHC (Equipment Calibration Check)"
            color = "#d97706"
            action_plan.append(f"Extreme biological outlier values detected ({', '.join(outlier_flags)}).")
            action_plan.append("Physical measurement verification using calibrated equipment is recommended prior to clinical intervention.")
            human_review = "REQUIRED"
            followup_timeframe = "Within 24–48 hours for measurement verification"
            screening_status = "REVIEW_REQUIRED"
            ref_interpretation = f"Measurement plausibility alert: Value exceeds biologically plausible threshold (±5.0 SD). Verification advised."

        # ---------------------------------------------------------------------
        # 2. MODERATE RISK FLAGS
        # ---------------------------------------------------------------------
        elif is_under_5:
            # Under-5 WHO/IMCI Moderate Flags
            has_mod = False
            mod_reasons = []
            if age_months >= 6.0 and muac is not None and muac < 12.5:
                moderate_flags.append(f"MUAC in moderate risk zone ({muac:.1f} cm in 11.5–12.4 cm range)")
                mod_reasons.append(f"Moderate acute wasting by MUAC ({muac:.1f} cm)")
                has_mod = True
            if whz is not None and whz < -2.0:
                moderate_flags.append(f"Moderate Wasting: WHZ {whz:.2f} SD (< -2.0 SD)")
                mod_reasons.append(f"Moderate wasting (WHZ {whz:.2f} SD)")
                has_mod = True
            if haz is not None and haz < -2.0:
                moderate_flags.append(f"Stunting (Linear Deficit): HAZ {haz:.2f} SD (< -2.0 SD)")
                mod_reasons.append(f"Linear stunting (HAZ {haz:.2f} SD)")
                has_mod = True
            if waz is not None and waz < -2.0:
                moderate_flags.append(f"Underweight: WAZ {waz:.2f} SD (< -2.0 SD)")
                mod_reasons.append(f"Underweight (WAZ {waz:.2f} SD)")
                has_mod = True

            if has_mod:
                triage_level = "MONITOR (YELLOW)"
                facility = "Anganwadi / Supplementary Nutrition Center / PHC"
                color = "#d97706"
                action_plan.append("Targeted supplementary nutritional support and dietary counseling recommended.")
                action_plan.append("Follow-up evaluation within 14 days by community healthcare provider.")
                human_review = "RECOMMENDED"
                followup_timeframe = "Within 7–14 days"
                screening_status = "AT_RISK"
                ref_interpretation = f"Nutritional vulnerability: {', '.join(mod_reasons)}."

        elif not is_under_5 and iap_assessment:
            # 5-18 Years IAP 2015 Moderate / Special Attention Flags
            has_mod = False
            mod_reasons = []
            if iap_assessment.get("is_obese"):
                b_val = iap_assessment.get("bmi_assessment", {}).get("value")
                c27 = iap_assessment.get("bmi_assessment", {}).get("cutoff_27_obese")
                moderate_flags.append(f"Pediatric Obesity: BMI {b_val} kg/m² >= IAP 27 kg/m² adult-equivalent cutoff ({c27} kg/m²)")
                action_plan.append("Pediatric endocrine and metabolic evaluation recommended for obesity screening.")
                mod_reasons.append("Pediatric Obesity (IAP 2015)")
                has_mod = True
            elif iap_assessment.get("is_overweight"):
                b_val = iap_assessment.get("bmi_assessment", {}).get("value")
                c23 = iap_assessment.get("bmi_assessment", {}).get("cutoff_23_overweight")
                moderate_flags.append(f"Pediatric Overweight: BMI {b_val} kg/m² >= IAP 23 kg/m² adult-equivalent cutoff ({c23} kg/m²)")
                action_plan.append("Nutritional counseling, reduced ultra-processed food intake, and daily active physical play advised.")
                mod_reasons.append("Pediatric Overweight (IAP 2015)")
                has_mod = True

            if iap_assessment.get("is_stunted"):
                h_val = iap_assessment.get("height_assessment", {}).get("value")
                moderate_flags.append(f"Short Stature / Stunting: Height {h_val} cm (< 3rd percentile IAP 2015)")
                action_plan.append("Pediatrician evaluation for chronic linear growth faltering / short stature recommended.")
                mod_reasons.append("Short Stature (IAP 2015)")
                has_mod = True

            if iap_assessment.get("is_underweight"):
                w_val = iap_assessment.get("weight_assessment", {}).get("value")
                moderate_flags.append(f"Underweight: Weight {w_val} kg (< 3rd percentile IAP 2015)")
                action_plan.append("Dietary intake assessment and supplementary balanced family nutrition recommended.")
                mod_reasons.append("Underweight (IAP 2015)")
                has_mod = True

            if has_mod:
                triage_level = "MONITOR (YELLOW)"
                facility = "Pediatric Clinic / Hospital Outpatient"
                color = "#d97706"
                human_review = "RECOMMENDED"
                followup_timeframe = "Within 14–30 days"
                screening_status = "AT_RISK"
                ref_interpretation = f"IAP 2015 Pediatric growth classification: {', '.join(mod_reasons)}."

        # ---------------------------------------------------------------------
        # 3. ROUTINE GROWTH MONITORING
        # ---------------------------------------------------------------------
        else:
            triage_level = "ROUTINE (GREEN)"
            facility = "Community Health Post / Home"
            color = "#16a34a"
            action_plan.append("Standard pediatric monitoring, age-appropriate complementary feeding, and routine immunization.")
            human_review = "ROUTINE"
            followup_timeframe = "Routine monthly screening (30 days)"
            screening_status = "LOW_RISK"
            ref_interpretation = "All measured growth parameters track within reference parameters."

        # ---------------------------------------------------------------------
        # 4. DISCREPANCY & CONFLICT DETECTION (ML vs Clinical Rules)
        # ---------------------------------------------------------------------
        discrepancy_detected = False
        discrepancy_note = None

        if prediction_label and prediction_label.strip() not in ["", "UNABLE_TO_ASSESS", "INSUFFICIENT_DATA", "None"]:
            ml_is_normal = (prediction_label.strip().lower() == "normal")
            clinical_is_urgent = (triage_level.startswith("URGENT") or is_emergency)
            clinical_is_abnormal = clinical_is_urgent or triage_level.startswith("MONITOR")

            if ml_is_normal and clinical_is_urgent:
                discrepancy_detected = True
                discrepancy_note = (
                    "CRITICAL DISCREPANCY: AI tabular ensemble predicted 'Normal', but deterministic "
                    "clinical red flags were detected (e.g. edema or severe anthropometric deficit). "
                    "Per clinical safety protocols, emergency triage overrides AI output."
                )
                human_review = "REQUIRED"
            elif ml_is_normal and clinical_is_abnormal:
                discrepancy_detected = True
                discrepancy_note = (
                    "DISCREPANCY: AI tabular ensemble predicted 'Normal', but WHO growth reference "
                    "standards indicate nutritional deficits (HAZ/WAZ/WHZ < -2.0 SD). Clinical review recommended."
                )
                if human_review == "ROUTINE":
                    human_review = "RECOMMENDED"
            elif not ml_is_normal and not clinical_is_abnormal and triage_level.startswith("ROUTINE"):
                discrepancy_detected = True
                discrepancy_note = (
                    f"DISCREPANCY: AI tabular ensemble predicted '{prediction_label}', but WHO growth reference "
                    "indicators are currently within normal ranges. Clinical monitoring advised."
                )
                if human_review == "ROUTINE":
                    human_review = "RECOMMENDED"

        return {
            "status": "available",
            "level": triage_level,
            "triage_level": triage_level,
            "is_emergency": is_emergency,
            "color": color,
            "flags": red_flags + moderate_flags + [f"Outlier: {f}" for f in outlier_flags],
            "red_flags": red_flags,
            "reasons": red_flags if red_flags else (moderate_flags if moderate_flags else (outlier_flags if outlier_flags else ["Anthropometric parameters align with standard pediatric ranges."])),
            "facility_referral": facility,
            "action_plan": action_plan,
            "action": " ".join(action_plan),
            "referral_recommended": is_emergency or triage_level.startswith("URGENT"),
            "treatment_prescription": False,
            "discrepancy_detected": discrepancy_detected,
            "discrepancy_note": discrepancy_note,
            # 7 Concepts Separation
            "data_quality_status": "BIOLOGICAL_OUTLIER_DETECTED" if outlier_flags else ("DATA_VALID" if not data_warnings else "DATA_REVIEW_RECOMMENDED"),
            "growth_indicators": {
                "whz": whz, "haz": haz, "waz": waz, "muac": muac, "has_bilateral_edema": has_bilateral_edema
            },
            "reference_interpretation": ref_interpretation,
            "model_estimates": {
                "prediction_label": prediction_label, "confidence": confidence
            },
            "screening_status": screening_status,
            "recommended_followup": {
                "action": " ".join(action_plan),
                "timeframe": followup_timeframe,
                "facility": facility
            },
            "human_review_status": human_review,
            "followup_timeframe": followup_timeframe,
            "safety_disclaimer": "ChildNutri AI is a screening and clinical decision-support prototype. It does not provide medical diagnoses or prescribe medications."
        }

    @classmethod
    def classify(
        cls,
        prediction: Optional[str] = None,
        risk_score: Optional[float] = None,
        muac: Optional[float] = None,
        waz: Optional[float] = None,
        haz: Optional[float] = None,
        whz: Optional[float] = None,
        has_bilateral_edema: bool = False,
        appetite_test_pass: bool = True,
        medical_complications: bool = False
    ) -> Dict[str, Any]:
        """
        Compact classification method for backwards compatibility with backend routers and PDF reporting.
        Guarantees ML prediction never overrides clinical red flags.
        Does NOT silently default missing data to Normal or Routine.
        """
        # If all indicator inputs are None/omitted, return explicit review required
        if (prediction is None and risk_score is None and muac is None and
            waz is None and haz is None and whz is None and not has_bilateral_edema):
            return {
                "level": "REVIEW_REQUIRED (AMBER)",
                "action": "Insufficient measurements provided for definitive clinical triage. Physical examination and anthropometric measurement required.",
                "color": "#d97706",
                "is_emergency": False,
                "facility_referral": "Primary Health Centre",
                "referral_recommended": False,
                "treatment_prescription": False,
                "discrepancy_detected": False,
                "human_review_status": "REQUIRED",
                "screening_status": "ASSESSMENT_INCOMPLETE",
                "safety_disclaimer": "ChildNutri AI is a screening and clinical decision-support prototype. It does not provide medical diagnoses or prescribe medications."
            }

        # Clinical Red Flags
        if has_bilateral_edema or (muac is not None and muac < 11.5) or (whz is not None and whz < -3.0):
            level = "URGENT (RED)"
            color = "#dc2626"
            is_emergency = True
            facility = "Nutrition Rehabilitation Centre (NRC) / Hospital Inpatient" if (has_bilateral_edema or medical_complications or not appetite_test_pass) else "Outpatient Therapeutic Programme (OTP)"
            action = "Urgent clinical evaluation/referral recommended. Inpatient medical stabilization or outpatient therapeutic feeding should follow national CMAM/WHO guidelines under qualified healthcare supervision."
            human_review = "REQUIRED"
            screening_status = "AT_RISK"
        elif (risk_score is not None and risk_score >= 70.0) or (prediction and any(k in prediction.lower() for k in ["severe", "sam"])):
            level = "URGENT (RED)"
            color = "#dc2626"
            is_emergency = True
            facility = "Nutrition Rehabilitation Centre (NRC) / Medical Officer"
            action = "Urgent clinical evaluation/referral recommended. High composite screening risk warrants comprehensive pediatric assessment."
            human_review = "REQUIRED"
            screening_status = "AT_RISK"
        elif ((muac is not None and muac < 12.5) or (whz is not None and whz < -2.0) or
              (haz is not None and haz < -2.0) or (waz is not None and waz < -2.0) or
              (risk_score is not None and risk_score >= 35.0) or
              (prediction and any(k in prediction.lower() for k in ["moderate", "wasted", "stunted", "underweight"]))):
            level = "MONITOR (YELLOW)"
            color = "#d97706"
            is_emergency = False
            facility = "Anganwadi / Supplementary Nutrition Center / PHC"
            action = "Targeted Supplementary Nutrition Support recommended. Dietary counseling and biweekly growth monitoring by frontline healthcare provider."
            human_review = "RECOMMENDED"
            screening_status = "AT_RISK"
        else:
            level = "ROUTINE (GREEN)"
            color = "#16a34a"
            is_emergency = False
            facility = "Community Health Post / Home"
            action = "Standard pediatric monitoring, age-appropriate complementary feeding, and routine immunization follow-up."
            human_review = "ROUTINE"
            screening_status = "LOW_RISK"

        # Check discrepancy
        ml_normal = (prediction is not None and prediction.strip().lower() == "normal")
        discrepancy = ml_normal and ("URGENT" in level or "MONITOR" in level)

        return {
            "level": level,
            "action": action,
            "color": color,
            "is_emergency": is_emergency,
            "facility_referral": facility,
            "referral_recommended": is_emergency or "URGENT" in level,
            "treatment_prescription": False,
            "discrepancy_detected": discrepancy,
            "human_review_status": human_review,
            "screening_status": screening_status,
            "safety_disclaimer": "ChildNutri AI is a screening and clinical decision-support prototype. It does not provide medical diagnoses or prescribe medications."
        }

if __name__ == "__main__":
    triage = ClinicalTriageEngine()
    print("Clinical Triage Demo (Severe Wasting + ML Normal):")
    res = triage.evaluate_triage(
        age_months=14.0,
        weight=6.8,
        height=72.0,
        muac=11.2,
        whz=-3.2,
        prediction_label="Normal",
        confidence=0.91
    )
    for k, v in res.items():
        print(f"  {k:<24}: {v}")
