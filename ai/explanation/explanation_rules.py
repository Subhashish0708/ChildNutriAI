"""
=============================================================================
ChildNutri AI - Explanation Rules & Logic Engine
=============================================================================
Deterministic rules for clinical severity categorization, age segmentation,
contributing factor extraction, discrepancy reconciliation, and section status resolution.
=============================================================================
"""

from typing import Dict, Any, Optional, List, Tuple
from ai.explanation.explanation_safety import (
    STATUS_AVAILABLE, STATUS_PARTIAL, STATUS_NOT_ASSESSED, STATUS_NOT_AVAILABLE, STATUS_ERROR
)


class ExplanationRules:
    """
    Deterministic rule engine translating raw assessment data into structured,
    evidence-based categories and status flags.
    """

    # Clinical Severity Categories
    CAT_NORMAL = "NORMAL"
    CAT_MILD_CONCERN = "MILD_CONCERN"
    CAT_MODERATE_CONCERN = "MODERATE_CONCERN"
    CAT_HIGHER_CONCERN = "HIGHER_CONCERN"
    CAT_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

    # Age Brackets
    AGE_UNDER_6M = "UNDER_6M"
    AGE_6_TO_23M = "6_TO_23M"
    AGE_24_TO_59M = "24_TO_59M"
    AGE_OVER_59M = "OVER_59M"

    @classmethod
    def determine_age_bracket(cls, age_months: float) -> Tuple[str, str]:
        """Returns age bracket code and human label."""
        if age_months < 6.0:
            return cls.AGE_UNDER_6M, "Infant under 6 months (<6m)"
        elif age_months < 24.0:
            return cls.AGE_6_TO_23M, "Child 6 to 23 months (Complementary Feeding)"
        elif age_months < 60.0:
            return cls.AGE_24_TO_59M, "Child 24 to 59 months (Young Child / Family Diet)"
        else:
            return cls.AGE_OVER_59M, "Child 60 months or older"

    @classmethod
    def evaluate_primary_clinical_status(
        cls,
        has_bilateral_edema: bool,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        muac: Optional[float],
        prediction_label: str,
        longitudinal_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classifies overall clinical status and severity with strict hierarchical rules:
        Nutritional Edema / Severe Wasting > Growth Faltering > Moderate Wasting > Stunting > Underweight > Normal.
        """
        has_faltering = bool(longitudinal_data and longitudinal_data.get("early_warning_alert"))
        pred_lower = (prediction_label or "").lower()

        # 1. Bilateral Edema (Kwashiorkor / Nutritional Edema - Emergency)
        if has_bilateral_edema:
            return {
                "category": cls.CAT_HIGHER_CONCERN,
                "code": "EDEMA_SAM",
                "title": "Severe Acute Malnutrition (Nutritional Edema)",
                "simple_title": "Severe nutritional concern (fluid swelling in both feet)",
                "severity_level": "Higher Concern",
                "summary": "Bilateral pitting pedal edema was identified. Fluid swelling in both feet is a key clinical sign that requires immediate medical care at a hospital or nutrition centre.",
                "measurements_summary": "Bilateral pedal edema: Present (+)"
            }

        # 2. Severe Wasting (WHZ < -3 SD or MUAC < 11.5 cm)
        if (whz is not None and whz < -3.0) or (muac is not None and muac < 11.5):
            meas = []
            if whz is not None and whz < -3.0: meas.append(f"weight-for-height ({whz:+.2f} SD)")
            if muac is not None and muac < 11.5: meas.append(f"arm circumference ({muac:.1f} cm)")
            meas_str = " and ".join(meas)
            return {
                "category": cls.CAT_HIGHER_CONCERN,
                "code": "SEVERE_WASTING",
                "title": "Severe Acute Malnutrition (Severe Wasting)",
                "simple_title": "Severe growth concern (weight is very low for height)",
                "severity_level": "Higher Concern",
                "summary": f"Your child's current {meas_str} is significantly lower than expected. This indicates acute nutritional vulnerability that requires prompt clinical attention.",
                "measurements_summary": f"WHZ: {whz:+.2f} SD, MUAC: {muac:.1f} cm" if (whz and muac) else f"WHZ: {whz} SD"
            }

        # 3. Growth Faltering across sequential visits
        if has_faltering:
            vel = longitudinal_data.get("weight_velocity_g_day")
            vel_str = f"{vel:+.1f} g/day" if vel is not None else "downward"
            return {
                "category": cls.CAT_MODERATE_CONCERN,
                "code": "GROWTH_FALTERING",
                "title": "Growth Faltering / Velocity Deceleration",
                "simple_title": "Growth slowdown / weight trend needs attention",
                "severity_level": "Moderate Concern",
                "summary": f"Your child's weight has slowed down or decreased between recent visits ({vel_str}). Reviewing feeding and recent health is important to help growth get back on track.",
                "measurements_summary": f"Weight trend: {vel_str}"
            }

        # 4. Moderate Wasting (WHZ < -2.0 SD or MUAC < 12.5 cm)
        if (whz is not None and whz < -2.0) or (muac is not None and muac < 12.5) or "wasted" in pred_lower:
            meas = []
            if whz is not None and whz < -2.0: meas.append(f"weight-for-height ({whz:+.2f} SD)")
            if muac is not None and muac < 12.5: meas.append(f"arm circumference ({muac:.1f} cm)")
            meas_str = " and ".join(meas) if meas else "weight-for-height"
            return {
                "category": cls.CAT_MODERATE_CONCERN,
                "code": "MODERATE_WASTING",
                "title": "Moderate Acute Malnutrition (Wasting Concern)",
                "simple_title": "Moderate growth concern (weight is low for height)",
                "severity_level": "Moderate Concern",
                "summary": f"Your child's {meas_str} is lower than expected for their height. This is a growth concern that deserves attention, dietary review, and clinical follow-up.",
                "measurements_summary": f"WHZ: {whz:+.2f} SD, MUAC: {muac:.1f} cm" if (whz and muac) else f"WHZ: {whz} SD"
            }

        # 5. Stunting (HAZ < -2.0 SD)
        if (haz is not None and haz < -2.0) or "stunted" in pred_lower:
            return {
                "category": cls.CAT_MODERATE_CONCERN,
                "code": "STUNTING",
                "title": "Linear Growth Concern (Stunting)",
                "simple_title": "Height is lower than expected for age",
                "severity_level": "Moderate Concern",
                "summary": f"Your child's height ({haz:+.2f} SD) is lower than expected for their age. This reflects longer-term linear growth rather than recent weight loss.",
                "measurements_summary": f"HAZ: {haz:+.2f} SD (< -2 SD)"
            }

        # 6. Underweight (WAZ < -2.0 SD)
        if (waz is not None and waz < -2.0) or "underweight" in pred_lower:
            return {
                "category": cls.CAT_MODERATE_CONCERN,
                "code": "UNDERWEIGHT",
                "title": "Weight-for-Age Deficit (Underweight)",
                "simple_title": "Overall weight is low for age",
                "severity_level": "Moderate Concern",
                "summary": f"Your child's overall weight ({waz:+.2f} SD) is below the expected range for their age. Weight-for-age reflects both height and body fullness.",
                "measurements_summary": f"WAZ: {waz:+.2f} SD (< -2 SD)"
            }

        # 7. Normal physical growth
        return {
            "category": cls.CAT_NORMAL,
            "code": "NORMAL",
            "title": "Normal Physical Growth & Nutritional Status",
            "simple_title": "Measurements are within standard range",
            "severity_level": "Normal",
            "summary": "Today's screening does not show a clear nutrition-related growth concern. All recorded measurements fall within the assessed international growth curves.",
            "measurements_summary": "All measurements within expected standard range"
        }

    @classmethod
    def extract_contributing_factors(
        cls,
        medical_notes: Optional[str],
        longitudinal_data: Optional[Dict[str, Any]],
        shap_factors: Optional[List[Dict[str, Any]]],
        clinical_features: Optional[Dict[str, Any]] = None,
        feeding_features: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts verified contributing factors strictly from actual assessment inputs.
        Never infers poverty, neglect, or parenting faults. Uses non-causal phrasing.
        """
        factors = []
        notes = (medical_notes or "").lower()

        # 1. Illness events
        if "diarrhea" in notes or "diarrhoea" in notes or "loose stool" in notes:
            factors.append({
                "factor": "Recent Illness (Diarrhea)",
                "details": "A recent episode of diarrhea was reported. Diarrhea can temporarily affect fluid balance, nutrient absorption, and body weight.",
                "priority": "High",
                "data_source": "Caregiver medical notes"
            })
        if "fever" in notes or "febrile" in notes or "infection" in notes:
            factors.append({
                "factor": "Recent Illness (Fever / Infection)",
                "details": "A recent fever or infection was reported. Fevers increase metabolic demands and often temporarily reduce appetite.",
                "priority": "High",
                "data_source": "Caregiver medical notes"
            })
        if "cough" in notes or "respiratory" in notes or "pneumonia" in notes or "cold" in notes:
            factors.append({
                "factor": "Respiratory Symptoms",
                "details": "Respiratory symptoms or cough were noted, which can cause fatigue and make feeding more difficult.",
                "priority": "Moderate",
                "data_source": "Caregiver medical notes"
            })
        if "vomit" in notes or "emesis" in notes:
            factors.append({
                "factor": "Vomiting Episodes",
                "details": "Vomiting was reported, which can restrict food and fluid retention.",
                "priority": "High",
                "data_source": "Caregiver medical notes"
            })

        # 2. Feeding difficulties or appetite
        if "appetite" in notes and any(k in notes for k in ["poor", "loss", "reduced", "low", "refus"]):
            factors.append({
                "factor": "Reduced Appetite / Oral Intake",
                "details": "The notes indicate reduced appetite or difficulty finishing meals, which can lower overall energy intake.",
                "priority": "Moderate",
                "data_source": "Feeding observation"
            })

        # 3. Dietary diversity recall
        if feeding_features and feeding_features.get("dietary_diversity_score") is not None:
            dds = feeding_features.get("dietary_diversity_score")
            if dds < 5:
                factors.append({
                    "factor": "Limited Dietary Variety",
                    "details": f"The food recall recorded {dds} of the 8 assessed food groups, which falls below the WHO minimum dietary diversity standard.",
                    "priority": "Moderate",
                    "data_source": "Dietary diversity recall"
                })
        elif "diet" in notes and any(k in notes for k in ["poor", "limited", "low diversity", "inadequate"]):
            factors.append({
                "factor": "Limited Dietary Variety",
                "details": "Clinical notes indicate limited dietary variety across recent meals.",
                "priority": "Moderate",
                "data_source": "Caregiver medical notes"
            })

        # 4. Growth velocity deceleration or weight drop
        if longitudinal_data:
            vel = longitudinal_data.get("weight_velocity_g_day")
            if longitudinal_data.get("early_warning_alert") or (vel is not None and float(vel) < 0):
                vel_str = f"{float(vel):+.1f} g/day" if vel is not None else "downward"
                factors.append({
                    "factor": "Growth Velocity Deceleration",
                    "details": f"Recent visits show a downward weight trajectory ({vel_str}) rather than steady gain.",
                    "priority": "High",
                    "data_source": "Longitudinal growth records"
                })

        # 5. Statistical feature attributions from screening model (non-causal)
        if shap_factors:
            for item in shap_factors[:2]:
                impact = item.get("impact", "")
                if "Risk" in impact or item.get("shap_value", 0) > 0:
                    feat = item.get("display_name", item.get("feature", "Growth indicator"))
                    val = item.get("measured_value", item.get("value", ""))
                    factors.append({
                        "factor": f"Model Indicator: {feat}",
                        "details": f"Statistical model sensitivity: Recorded {feat} ({val}) influenced the screening model's classification pattern.",
                        "priority": "Moderate",
                        "data_source": "Model feature attribution (statistical pattern)"
                    })

        return factors

    @classmethod
    def evaluate_discrepancy(
        cls,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        muac: Optional[float],
        has_bilateral_edema: bool,
        prediction_label: str,
        triage_level: str
    ) -> Dict[str, Any]:
        """
        Analyzes consistency between WHO growth standards and AI prediction.
        Ensures differences are explained clearly and never hidden.
        """
        pred_lower = (prediction_label or "").lower()

        # Classify WHO concern
        who_concerns = []
        if has_bilateral_edema: who_concerns.append("Bilateral pedal edema")
        if whz is not None and whz < -2.0: who_concerns.append(f"Weight-for-height {whz:+.2f} SD")
        if haz is not None and haz < -2.0: who_concerns.append(f"Height-for-age {haz:+.2f} SD")
        if waz is not None and waz < -2.0: who_concerns.append(f"Weight-for-age {waz:+.2f} SD")
        if muac is not None and muac < 12.5: who_concerns.append(f"MUAC {muac:.1f} cm")

        who_has_concern = len(who_concerns) > 0
        ai_has_concern = any(k in pred_lower for k in ["wasted", "sam", "mam", "stunted", "underweight", "severe"])

        if who_has_concern and ai_has_concern:
            status = "CONCORDANT_CONCERN"
            summary = "Both the WHO growth standards and the AI screening model identified a growth or nutrition concern."
            action_rule = "Both layers agree. Follow the recommended clinical and feeding steps."
        elif (not who_has_concern) and (not ai_has_concern):
            status = "CONCORDANT_NORMAL"
            summary = "Both the WHO growth standards and the AI screening model show measurements within the standard assessed range."
            action_rule = "Both layers agree. Continue routine growth monitoring and age-appropriate nutrition."
        elif who_has_concern and not ai_has_concern:
            status = "DISCREPANCY_WHO_FLAG"
            summary = (
                f"The WHO growth assessment and AI screening result do not fully agree. The system is showing both results rather than replacing one with the other. "
                f"The WHO growth standards identified a concern ({', '.join(who_concerns)}), "
                f"while the AI screening model predicted '{prediction_label}'."
            )
            action_rule = (
                "Deterministic clinical safety rules and actual WHO measurements always take precedence over AI predictions. "
                "The child should be evaluated based on the specific WHO measurements rather than relying on the AI result alone."
            )
        else:
            status = "DISCREPANCY_AI_FLAG"
            summary = (
                f"The AI model flagged a potential pattern of concern ({prediction_label}), "
                "while current individual WHO Z-scores fall within standard reference bounds."
            )
            action_rule = (
                "The AI model considers multidimensional combinations of measurements. "
                "Because individual measurements are within standard ranges, close routine follow-up is recommended to watch growth progress."
            )

        return {
            "status": status,
            "has_discrepancy": "DISCREPANCY" in status,
            "summary": summary,
            "action_rule": action_rule,
            "who_perspective": f"WHO Standards: {', '.join(who_concerns) if who_concerns else 'Within reference limits'}",
            "ai_perspective": f"AI Model Prediction: {prediction_label}",
            "safety_priority": f"Clinical Safety Triage: {triage_level}"
        }
