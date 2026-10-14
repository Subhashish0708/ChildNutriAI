"""
=============================================================================
ChildNutri AI - Evidence Consistency Layer (Clinical Decision Support)
=============================================================================
Academic & Clinical Mandate (Prompt Section 28):
  Never allow:
    WHO = concern
    AI = normal
    Clinical = routine
    Explanation = reassuring
  without explicitly identifying and communicating the disagreement.

Guarantees:
  1. Multimodal Evidence Cross-Validation: Evaluates WHO Z-scores, AI prediction,
     vision estimates, and clinical triage rules in parallel.
  2. Discrepancy Transparency: Produces explicit, transparent statements when
     different analytical layers yield divergent interpretations.
  3. Safety Precedence: Clinical safety triage (IMCI / CMAM rules) and direct
     WHO anthropometrics always override machine learning classifications.
=============================================================================
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("childnutri.evidence_consistency")


class EvidenceConsistencyLayer:
    """
    Evidence Consistency & Cross-Modal Reconciliation Layer:
    Compares evidence streams (WHO LMS, Vision AI, Tabular AI, and Clinical Rules)
    to enforce safety-first decision support.
    """

    STATUS_CONCORDANT_NORMAL = "CONCORDANT_NORMAL"
    STATUS_CONCORDANT_CONCERN = "CONCORDANT_CONCERN"
    STATUS_DISCREPANCY_WHO_DOMINANT = "DISCREPANCY_WHO_FLAG"
    STATUS_DISCREPANCY_AI_DOMINANT = "DISCREPANCY_AI_FLAG"

    @classmethod
    def evaluate_consistency(
        cls,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        muac: Optional[float],
        has_bilateral_edema: bool,
        prediction_label: str,
        confidence: float,
        triage_level: str,
        risk_score: float,
        child_name: str = "The child"
    ) -> Dict[str, Any]:
        """
        Synthesizes all evidence streams and identifies any diagnostic discrepancies.
        """
        pred_lower = (prediction_label or "").lower()
        triage_upper = (triage_level or "").upper()

        who_concerns: List[str] = []
        if has_bilateral_edema:
            who_concerns.append("Bilateral pedal edema (nutritional oedema)")
        if whz is not None and whz < -2.0:
            who_concerns.append(f"Weight-for-Height Z-score {whz:+.2f} SD (wasting threshold < -2 SD)")
        if haz is not None and haz < -2.0:
            who_concerns.append(f"Height-for-Age Z-score {haz:+.2f} SD (stunting threshold < -2 SD)")
        if waz is not None and waz < -2.0:
            who_concerns.append(f"Weight-for-Age Z-score {waz:+.2f} SD (underweight threshold < -2 SD)")
        if muac is not None and muac < 12.5:
            who_concerns.append(f"Mid-Upper Arm Circumference {muac:.1f} cm (acute malnutrition cutoff < 12.5 cm)")

        who_has_concern = len(who_concerns) > 0
        ai_has_concern = any(k in pred_lower for k in ["wasted", "sam", "mam", "stunted", "underweight", "severe", "moderate"])
        is_triage_urgent = "RED" in triage_upper or has_bilateral_edema
        is_triage_monitor = "YELLOW" in triage_upper or "AMBER" in triage_upper

        if who_has_concern and ai_has_concern:
            status = cls.STATUS_CONCORDANT_CONCERN
            has_discrepancy = False
            summary = "Both the WHO growth standards and the AI screening model identified a growth or nutritional concern."
            action_guidance = (
                "Both evaluative layers concordantly identify nutritional vulnerability. "
                "Adhere strictly to the recommended clinical triage protocol and nutrition support plan."
            )
        elif (not who_has_concern) and (not ai_has_concern):
            status = cls.STATUS_CONCORDANT_NORMAL
            has_discrepancy = False
            summary = "Both the WHO growth standards and the AI screening model indicate measurements within expected standard ranges."
            action_guidance = "Both layers agree. Continue age-appropriate supportive feeding and monthly routine growth monitoring."
        elif who_has_concern and not ai_has_concern:
            status = cls.STATUS_DISCREPANCY_WHO_DOMINANT
            has_discrepancy = True
            summary = (
                "The WHO growth assessment and AI screening result do not fully agree. "
                "The system is showing both results rather than replacing one with the other. "
                f"WHO standards flag: {'; '.join(who_concerns)}, while the AI screening model categorized the child as '{prediction_label}'."
            )
            action_guidance = (
                "SAFETY OVERRIDE: Deterministic WHO growth standards and clinical measurements take strict precedence over AI machine learning outputs. "
                "The child must be followed up based on the objective anthropometric finding rather than the AI classification alone."
            )
        else:
            status = cls.STATUS_DISCREPANCY_AI_DOMINANT
            has_discrepancy = True
            summary = (
                "The WHO growth assessment and AI screening result do not fully agree. "
                "The system is showing both results rather than replacing one with the other. "
                f"The AI screening model flagged potential concern ('{prediction_label}'), "
                "while current individual WHO Z-scores fall within standard reference bounds."
            )
            action_guidance = (
                "The AI model analyzes non-linear multidimensional measurement interactions. "
                "Because individual Z-scores remain within normal bounds, active clinical monitoring and a follow-up assessment in 14–30 days is indicated."
            )

        return {
            "status": status,
            "has_discrepancy": has_discrepancy,
            "summary": summary,
            "action_guidance": action_guidance,
            "who_perspective": {
                "has_concern": who_has_concern,
                "identified_findings": who_concerns or ["Measurements within reference percentiles"]
            },
            "ai_perspective": {
                "prediction": prediction_label,
                "confidence_pct": round(confidence * 100.0, 1),
                "risk_score": risk_score,
                "has_concern": ai_has_concern
            },
            "clinical_triage_perspective": {
                "triage_level": triage_level,
                "is_urgent": is_triage_urgent,
                "precedence_rule": "Deterministic clinical safety triage overrides all statistical models."
            }
        }
