"""
=============================================================================
ChildNutri AI - Central Human Explanation Engine
=============================================================================
Orchestrates clinical rules, safety guardrails, controlled templates, and evidence
citations into a comprehensive, multi-tiered human explanation system.

Supports:
  - Parent View (plain language, supportive, calm, respectful)
  - Detailed View (plain language + measurements + clinical interpretation)
  - Technical View (WHO z-scores, SHAP weights, Grad-CAM, risk score, model details)
  - Honest missing data handling (AVAILABLE, PARTIAL, NOT_ASSESSED, NOT_AVAILABLE, ERROR)
  - Full evidence citation and pediatric decision-support notices
=============================================================================
"""

import logging
from typing import Dict, Any, Optional, List

from ai.explanation.explanation_safety import (
    STATUS_AVAILABLE,
    STATUS_PARTIAL,
    STATUS_NOT_ASSESSED,
    STATUS_NOT_AVAILABLE,
    STATUS_ERROR,
    MEDICAL_DECISION_SUPPORT_NOTICE,
    DATA_LIMITATIONS,
    EVIDENCE_SOURCES,
    ExplanationSafetyValidator
)
from ai.explanation.explanation_rules import ExplanationRules
from ai.explanation.explanation_templates import ExplanationTemplates

logger = logging.getLogger(__name__)


class HumanExplanationEngine:
    """
    Central orchestration engine for human-like, evidence-based pediatric explanations.
    """

    @classmethod
    def generate_explanation(
        cls,
        child_name: Optional[str] = None,
        age_months: Optional[float] = None,
        gender: Optional[str] = "Unknown",
        weight: Optional[float] = None,
        height: Optional[float] = None,
        muac: Optional[float] = None,
        head_circumference: Optional[float] = None,
        has_bilateral_edema: bool = False,
        whz: Optional[float] = None,
        haz: Optional[float] = None,
        waz: Optional[float] = None,
        baz: Optional[float] = None,
        prediction_label: str = "Normal",
        confidence: float = 0.5,
        risk_score: Optional[float] = None,
        triage_level: str = "ROUTINE (GREEN)",
        is_emergency: bool = False,
        longitudinal_data: Optional[Dict[str, Any]] = None,
        medical_notes: Optional[str] = None,
        shap_factors: Optional[List[Dict[str, Any]]] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        dietary_data: Optional[Dict[str, Any]] = None,
        visits_count: int = 1
    ) -> Dict[str, Any]:
        """
        Generates a complete, multi-tiered human-like explanation dictionary.
        Gracefully handles missing or partial data without raising exceptions or
        inventing medical facts.
        """
        try:
            # 1. Age bracket resolution
            age_val = float(age_months) if age_months is not None else 12.0
            age_bracket, age_label = ExplanationRules.determine_age_bracket(age_val)

            # 2. Primary clinical finding
            primary_finding = ExplanationRules.evaluate_primary_clinical_status(
                has_bilateral_edema=has_bilateral_edema,
                whz=whz,
                haz=haz,
                waz=waz,
                muac=muac,
                prediction_label=prediction_label,
                longitudinal_data=longitudinal_data
            )

            # 3. Contributing factor extraction (non-causal, strictly from real inputs)
            factors = ExplanationRules.extract_contributing_factors(
                medical_notes=medical_notes,
                longitudinal_data=longitudinal_data,
                shap_factors=shap_factors
            )

            # 4. Discrepancy analysis
            discrepancy = ExplanationRules.evaluate_discrepancy(
                whz=whz,
                haz=haz,
                waz=waz,
                muac=muac,
                has_bilateral_edema=has_bilateral_edema,
                prediction_label=prediction_label,
                triage_level=triage_level
            )

            # 5. Core Narrative Sections
            in_simple_words = ExplanationTemplates.generate_in_simple_words(
                clinical_finding=primary_finding,
                age_bracket=age_bracket,
                child_name=child_name,
                factors=factors,
                has_discrepancy=discrepancy.get("has_discrepancy", False)
            )

            what_is_happening = ExplanationTemplates.generate_what_is_happening(
                clinical_finding=primary_finding,
                child_name=child_name,
                measurements={
                    "weight_kg": weight,
                    "height_cm": height,
                    "muac_cm": muac,
                    "whz": whz,
                    "haz": haz,
                    "waz": waz
                }
            )

            what_this_means = ExplanationTemplates.generate_what_this_means(
                clinical_finding=primary_finding,
                child_name=child_name
            )

            why_system_concerned = ExplanationTemplates.generate_why_system_concerned(
                clinical_finding=primary_finding,
                factors=factors
            )

            caregiver_actions = ExplanationTemplates.generate_caregiver_actions(
                clinical_finding=primary_finding,
                triage_level=triage_level,
                age_bracket=age_bracket,
                child_name=child_name
            )

            prevention = ExplanationTemplates.generate_prevention_guidance(age_bracket)

            is_single = (visits_count <= 1) and (not longitudinal_data or not longitudinal_data.get("has_history"))
            monitoring = ExplanationTemplates.generate_monitoring_guidance(
                clinical_finding=primary_finding,
                longitudinal_data=longitudinal_data,
                is_single_visit=is_single
            )

            prof_assessment = ExplanationTemplates.generate_professional_assessment(
                triage_level=triage_level,
                is_emergency=is_emergency,
                clinical_finding=primary_finding
            )

            what_not_to_worry_about = ExplanationTemplates.generate_what_not_to_worry_about(
                clinical_finding=primary_finding
            )

            # 6. Technical & Model Attribution Explanations
            shap_exp = ExplanationTemplates.generate_shap_explanation(
                shap_factors=shap_factors,
                prediction_label=prediction_label
            )

            gradcam_exp = ExplanationTemplates.generate_gradcam_explanation(
                vision_data=vision_data
            )

            dietary_exp = ExplanationTemplates.generate_dietary_diversity_explanation(
                dietary_data=dietary_data
            )

            longitudinal_exp = ExplanationTemplates.generate_longitudinal_explanation(
                longitudinal_data=longitudinal_data,
                visits_count=visits_count
            )

            risk_exp = ExplanationTemplates.generate_risk_score_explanation(
                risk_score=risk_score
            )

            # 7. Assembling Section Statuses
            section_statuses = {
                "in_simple_words": in_simple_words.get("status", STATUS_AVAILABLE),
                "what_is_happening": what_is_happening.get("status", STATUS_AVAILABLE),
                "what_this_means": what_this_means.get("status", STATUS_AVAILABLE),
                "why_is_system_concerned": why_system_concerned.get("status", STATUS_AVAILABLE),
                "caregiver_actions": caregiver_actions.get("status", STATUS_AVAILABLE),
                "prevention": prevention.get("status", STATUS_AVAILABLE),
                "monitoring": monitoring.get("status", STATUS_AVAILABLE),
                "professional_assessment": prof_assessment.get("status", STATUS_AVAILABLE),
                "what_not_to_worry_about": what_not_to_worry_about.get("status", STATUS_AVAILABLE),
                "shap_attribution": shap_exp.get("status", STATUS_NOT_AVAILABLE),
                "vision_gradcam": gradcam_exp.get("status", STATUS_NOT_AVAILABLE),
                "dietary_diversity": dietary_exp.get("status", STATUS_NOT_ASSESSED),
                "growth_over_time": longitudinal_exp.get("status", STATUS_NOT_ASSESSED),
                "risk_score": risk_exp.get("status", STATUS_AVAILABLE if risk_score is not None else STATUS_NOT_AVAILABLE)
            }

            # 8. Intermediate dict for views
            narratives = {
                "in_simple_words": in_simple_words,
                "what_is_happening": what_is_happening,
                "what_this_means": what_this_means,
                "why_system_concerned": why_system_concerned,
                "caregiver_actions": caregiver_actions,
                "prevention": prevention,
                "monitoring": monitoring,
                "professional_assessment": prof_assessment,
                "what_not_to_worry_about": what_not_to_worry_about,
                "shap": shap_exp,
                "gradcam": gradcam_exp,
                "dietary_diversity": dietary_exp,
                "longitudinal": longitudinal_exp,
                "risk_score": risk_exp,
                "discrepancy": discrepancy
            }

            measurements_dict = {
                "weight_kg": weight,
                "height_cm": height,
                "muac_cm": muac,
                "head_circumference_cm": head_circumference,
                "whz": whz,
                "haz": haz,
                "waz": waz,
                "baz": baz,
                "has_bilateral_edema": has_bilateral_edema
            }

            tech_data = {
                "who_z_scores": {
                    "whz": whz, "haz": haz, "waz": waz, "baz": baz,
                    "edema": has_bilateral_edema
                },
                "ai_prediction": {
                    "label": prediction_label,
                    "confidence": confidence
                },
                "clinical_triage": {
                    "level": triage_level,
                    "is_emergency": is_emergency
                },
                "risk_score": risk_score
            }

            # 9. Doctor-Like 12-Section Clinical Explanation
            doctor_exp = ExplanationTemplates.build_doctor_explanation(
                clinical_finding=primary_finding,
                child_name=child_name,
                age_bracket=age_bracket,
                age_months=age_val if age_months is not None else None,
                measurements=measurements_dict,
                factors=factors,
                longitudinal_data=longitudinal_data,
                visits_count=visits_count,
                whz=whz,
                haz=haz,
                waz=waz,
                baz=baz,
                muac=muac,
                has_bilateral_edema=has_bilateral_edema,
                triage_level=triage_level,
                prediction_label=prediction_label,
                risk_score=risk_score,
                shap_factors=shap_factors,
                vision_data=vision_data,
                discrepancy_info=discrepancy
            )

            # 10. Three Audience Tiers
            parent_view = ExplanationTemplates.build_parent_view(narratives)
            detailed_view = ExplanationTemplates.build_detailed_view(narratives, measurements_dict)
            technical_view = ExplanationTemplates.build_technical_view(tech_data, narratives)

            # 11. Complete Structured Output
            return {
                "status": STATUS_AVAILABLE,
                "summary": in_simple_words.get("text", ""),
                "assessment_summary": doctor_exp.get("assessment_summary", in_simple_words.get("text", "")),
                "doctor_explanation": doctor_exp,
                "sections": doctor_exp.get("sections", []),
                "in_simple_words": in_simple_words.get("text", ""),
                "what_is_happening": what_is_happening.get("text", ""),
                "what_this_means": what_this_means.get("text", ""),
                "why_is_system_concerned": why_system_concerned,
                "possible_contributing_factors": factors,
                "why_ai_gave_this_result": shap_exp.get("interpretation", ""),
                "what_caregiver_can_do": caregiver_actions.get("actions", []),
                "prevention": prevention,
                "monitoring": monitoring,
                "professional_assessment": prof_assessment.get("narrative", ""),
                "what_should_i_not_worry_about": what_not_to_worry_about.get("text", ""),
                "who_explanation": discrepancy.get("who_perspective", ""),
                "ai_explanation": discrepancy.get("ai_perspective", ""),
                "clinical_explanation": discrepancy.get("safety_priority", ""),
                "discrepancy_explanation": discrepancy,
                "dietary_diversity": dietary_exp,
                "growth_over_time": longitudinal_exp,
                "risk_score_explanation": risk_exp,
                "data_limitations": DATA_LIMITATIONS,
                "medical_decision_support_notice": MEDICAL_DECISION_SUPPORT_NOTICE,
                "sources": EVIDENCE_SOURCES,
                "parent_view": parent_view,
                "detailed_view": detailed_view,
                "technical_view": technical_view,
                "section_statuses": section_statuses
            }

        except Exception as e:
            logger.error(f"HumanExplanationEngine failed: {e}", exc_info=True)
            fallback_summary = "We couldn't load the complete assessment explanation right now. Please try again."
            return {
                "status": STATUS_ERROR,
                "summary": fallback_summary,
                "assessment_summary": fallback_summary,
                "doctor_explanation": {
                    "assessment_summary": fallback_summary,
                    "sections": []
                },
                "sections": [],
                "in_simple_words": fallback_summary,
                "what_is_happening": "Assessment data could not be processed completely.",
                "what_this_means": "Please check your network connection or retry the assessment.",
                "why_is_system_concerned": {"summary": "Unable to calculate explanation.", "factors": []},
                "possible_contributing_factors": [],
                "why_ai_gave_this_result": "Detailed feature attribution is not available for this assessment.",
                "what_caregiver_can_do": ["Retry the assessment.", "Consult a healthcare professional if there are clinical concerns."],
                "prevention": {"principles": []},
                "monitoring": {"recommended_frequency": "Consult healthcare worker."},
                "professional_assessment": "If the child shows any illness or concerning symptoms, consult a qualified healthcare provider immediately.",
                "what_should_i_not_worry_about": "Technical calculation error does not indicate an adverse health diagnosis.",
                "who_explanation": "Not available",
                "ai_explanation": "Not available",
                "clinical_explanation": "Not available",
                "discrepancy_explanation": {},
                "dietary_diversity": {"status": STATUS_ERROR, "summary": "Not available"},
                "growth_over_time": {"status": STATUS_ERROR, "summary": "Not available"},
                "risk_score_explanation": {"status": STATUS_ERROR, "summary": "Not available"},
                "data_limitations": DATA_LIMITATIONS,
                "medical_decision_support_notice": MEDICAL_DECISION_SUPPORT_NOTICE,
                "sources": EVIDENCE_SOURCES,
                "parent_view": {
                    "in_simple_words": "We couldn't load the assessment right now. Please try again.",
                    "what_is_happening": "Assessment unavailable.",
                    "what_this_means": "Retry requested.",
                    "what_to_do_now": ["Please try again."]
                },
                "detailed_view": {},
                "technical_view": {},
                "section_statuses": {
                    "in_simple_words": STATUS_ERROR,
                    "what_is_happening": STATUS_ERROR,
                    "what_this_means": STATUS_ERROR,
                    "why_is_system_concerned": STATUS_ERROR,
                    "caregiver_actions": STATUS_ERROR,
                    "prevention": STATUS_ERROR,
                    "monitoring": STATUS_ERROR,
                    "professional_assessment": STATUS_ERROR,
                    "what_not_to_worry_about": STATUS_ERROR,
                    "shap_attribution": STATUS_ERROR,
                    "vision_gradcam": STATUS_ERROR,
                    "dietary_diversity": STATUS_ERROR,
                    "growth_over_time": STATUS_ERROR,
                    "risk_score": STATUS_ERROR
                }
            }
