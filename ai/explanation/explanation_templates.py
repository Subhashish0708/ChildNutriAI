"""
=============================================================================
ChildNutri AI - Explanation Templates & Narrative Generators
=============================================================================
Provides human-like, evidence-based narrative generators across three audience
tiers (Parent View, Detailed View, Technical View).

Design Principles:
  1. Reassurance without false promises; calmness without minimizing genuine risk.
  2. Non-causal phrasing strictly: "Possible contributing factor, not confirmed cause".
  3. Strictly age-aware nutrition (<6m: exclusive breastfeeding only; 6-23m: complementary).
  4. Honest lifecycle statuses: AVAILABLE, PARTIAL, NOT_ASSESSED, NOT_AVAILABLE, ERROR.
  5. Zero autonomous pharmaceutical prescriptions or rigid therapeutic food commands.
=============================================================================
"""

from typing import Dict, Any, List, Optional
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


class ExplanationTemplates:
    """
    Controlled narrative generator translating clinical rules and assessment metrics
    into empathetic, structured, and clinically valid human explanations.
    """

    # -------------------------------------------------------------------------
    # 1. IN SIMPLE WORDS (2-4 Sentences)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_in_simple_words(
        cls,
        clinical_finding: Dict[str, Any],
        age_bracket: str,
        child_name: Optional[str] = None,
        factors: Optional[List[Dict[str, Any]]] = None,
        has_discrepancy: bool = False
    ) -> Dict[str, Any]:
        name_str = child_name.strip() if child_name and child_name.strip() else "Your child"
        possessive = f"{name_str}'s" if name_str != "Your child" else "Your child's"
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        factors = factors or []
        factor_mentions = []
        for f in factors:
            fname = f.get("factor", "").lower()
            if "diarrhea" in fname or "illness" in fname or "fever" in fname:
                factor_mentions.append("recent illness")
            elif "appetite" in fname or "diet" in fname:
                factor_mentions.append("feeding intake")
        factor_mentions = list(dict.fromkeys(factor_mentions))

        if category == ExplanationRules.CAT_NORMAL:
            sentences = [
                f"{possessive} current growth measurements are within the standard expected range for their age and height.",
                "This is reassuring based on the information recorded today.",
                "Healthy development continues to rely on age-appropriate feeding, routine wellness visits, and regular growth tracking."
            ]
        elif category == ExplanationRules.CAT_HIGHER_CONCERN:
            if code == "EDEMA_SAM":
                sentences = [
                    f"{possessive} assessment identified fluid swelling in both feet, which is an important physical sign.",
                    "This indicates a significant nutritional concern that requires prompt medical evaluation by a healthcare professional.",
                    "Please have your child seen at a clinic or healthcare facility today so a doctor can evaluate them thoroughly."
                ]
            else:
                sentences = [
                    f"{possessive} current growth measurements show a significant weight-for-height concern that needs prompt clinical attention.",
                    "Weight is considerably lower than expected for current height, indicating acute nutritional vulnerability.",
                    "Having a healthcare professional assess your child in person is the most important next step to guide recovery safely."
                ]
        elif category == ExplanationRules.CAT_MODERATE_CONCERN:
            if code == "GROWTH_FALTERING":
                sentences = [
                    f"{possessive} recent growth trend shows that weight gain has slowed down or dropped between visits.",
                    "While overall measurements may still be near acceptable ranges, this slowdown warrants closer attention.",
                    "Reviewing daily feeding and having a routine clinical check-up will help ensure growth gets back on track."
                ]
            elif code == "STUNTING":
                sentences = [
                    f"{possessive} height is lower than expected for their age, reflecting longer-term linear growth progress.",
                    "Current body weight is relatively balanced with height, indicating this relates to longer-term growth rather than sudden weight loss.",
                    "A varied, nutrient-dense diet and routine developmental checks support ongoing height gain over time."
                ]
                if factor_mentions:
                    sentences.append(f"Recorded notes mention {' and '.join(factor_mentions)}, which may be contributing.")
            elif code == "UNDERWEIGHT":
                sentences = [
                    f"{possessive} overall weight is lower than expected for their age.",
                    "Weight-for-age reflects both height and body fullness and suggests that energy intake needs review.",
                    "A discussion with a healthcare provider can help tailor feeding strategies to support steady weight gain."
                ]
            else:  # MODERATE_WASTING
                sentences = [
                    f"{possessive} current weight is lower than expected for their height, showing a growth concern that deserves attention.",
                    "This means the body has recently had less nutritional reserve than ideal for healthy growth.",
                    "Discussing these results with a healthcare professional and reviewing daily nutrition will help guide supportive care."
                ]
                if factor_mentions:
                    sentences.append(f"Recent {factor_mentions[0]} was noted and may be a contributing factor, though screening alone cannot confirm the direct cause.")
        else:
            sentences = [
                f"Some information needed to fully evaluate {possessive.lower()} growth status is currently unavailable.",
                "Complete anthropometric measurements and feeding details are recommended for a full assessment."
            ]

        text = " ".join(sentences)
        text = ExplanationSafetyValidator.sanitize_explanation_text(text)
        return {
            "status": STATUS_AVAILABLE,
            "text": text,
            "category": category,
            "severity_level": clinical_finding.get("severity_level", "Normal")
        }

    # -------------------------------------------------------------------------
    # 2. WHAT IS HAPPENING?
    # -------------------------------------------------------------------------
    @classmethod
    def generate_what_is_happening(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        name_str = child_name.strip() if child_name and child_name.strip() else "The child"
        possessive = f"{name_str}'s" if name_str != "The child" else "The child's"
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        if category == ExplanationRules.CAT_NORMAL:
            text = (
                f"{possessive} physical growth measurements are currently tracking along standard international reference curves. "
                "There is no indication of acute wasting, severe underweight, or significant linear growth faltering at this screening."
            )
        elif category == ExplanationRules.CAT_HIGHER_CONCERN:
            if code == "EDEMA_SAM":
                text = (
                    f"Physical evaluation identified bilateral pedal edema (fluid retention in both feet). "
                    "In pediatric nutrition, swelling of both feet without other obvious medical explanation is a serious clinical sign "
                    "that reflects altered protein and fluid metabolism requiring immediate medical management."
                )
            else:
                text = (
                    f"{possessive} weight is significantly below the expected range for their height. "
                    "When a child's weight is very low relative to length, it means body tissue and fat reserves have been rapidly depleted, "
                    "which places extra demand on the immune system and daily energy levels."
                )
        elif category == ExplanationRules.CAT_MODERATE_CONCERN:
            if code == "GROWTH_FALTERING":
                text = (
                    f"{possessive} weight trajectory between recent visits shows a flattening or downward curve rather than the expected steady gain. "
                    "Even if absolute weight has not fallen below critical thresholds, a deceleration in growth velocity indicates "
                    "that nutritional intake or recent health events have temporarily interrupted expected growth."
                )
            elif code == "STUNTING":
                text = (
                    f"{possessive} height is below the expected range for their age. "
                    "Height (linear growth) develops gradually over months and years, so this indicates a longer-term growth trend "
                    "rather than an immediate, acute nutritional crisis."
                )
            elif code == "UNDERWEIGHT":
                text = (
                    f"{possessive} weight is lower than standard percentiles for age. "
                    "This composite measurement reflects both skeletal frame and current body mass, indicating that overall energy intake "
                    "and nutrient absorption have not kept pace with developmental milestones."
                )
            else:
                text = (
                    f"{possessive} weight is currently low relative to height. "
                    "This indicates moderate nutritional strain, where the child's body is receiving or absorbing less energy than needed "
                    "to maintain healthy muscle and tissue development."
                )
        else:
            text = "There is insufficient measurement data to determine what is currently happening with the child's growth."

        return {
            "status": STATUS_AVAILABLE,
            "text": ExplanationSafetyValidator.sanitize_explanation_text(text)
        }

    # -------------------------------------------------------------------------
    # 3. WHAT DOES THIS MEAN?
    # -------------------------------------------------------------------------
    @classmethod
    def generate_what_this_means(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        if category == ExplanationRules.CAT_NORMAL:
            text = (
                "This result is positive and reassuring. It indicates that current feeding and care practices are supporting healthy physical growth. "
                "However, growth is continuous, so regular monitoring and age-appropriate nutrition remain essential as the child grows."
            )
        elif category == ExplanationRules.CAT_HIGHER_CONCERN:
            text = (
                "This result means the child requires professional medical assessment without delay. "
                "Children with acute nutritional vulnerability have lowered resistance to infections and need specialized clinical care "
                "to stabilize their metabolism, evaluate for underlying illnesses, and initiate supervised nutritional recovery."
            )
        elif category == ExplanationRules.CAT_MODERATE_CONCERN:
            text = (
                "This screening is a helpful early signal that growth needs supportive attention before more severe concerns develop. "
                "With age-appropriate nutritional adjustments, prompt treatment of any minor illnesses, and routine healthcare follow-up, "
                "most children in this category show steady catch-up growth."
            )
        else:
            text = "This means a full clinical evaluation with complete anthropometric measurements is needed to understand the child's growth status."

        return {
            "status": STATUS_AVAILABLE,
            "text": ExplanationSafetyValidator.sanitize_explanation_text(text)
        }

    # -------------------------------------------------------------------------
    # 4. WHY IS THE SYSTEM CONCERNED? (Contributing Factors)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_why_system_concerned(
        cls,
        clinical_finding: Dict[str, Any],
        factors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)

        if category == ExplanationRules.CAT_NORMAL:
            return {
                "status": STATUS_AVAILABLE,
                "summary": "The system did not identify reasons for acute growth concern at this screening.",
                "factors": [],
                "note": "All recorded measurements fall within standard reference ranges."
            }

        if not factors:
            summary = (
                f"The primary reason for concern is the child's recorded {clinical_finding.get('simple_title', 'growth measurement')}. "
                "No additional illness or feeding factors were documented in the assessment record."
            )
            return {
                "status": STATUS_AVAILABLE,
                "summary": summary,
                "factors": [],
                "note": "Possible contributing factors cannot be determined without recorded feeding or medical history."
            }

        summary = (
            f"The system flagged concern based primarily on {clinical_finding.get('simple_title', 'current growth measurements')}. "
            "In addition, the following observations were noted as possible contributing factors (not confirmed causes):"
        )
        return {
            "status": STATUS_AVAILABLE,
            "summary": summary,
            "factors": factors,
            "note": "Screening flags identify areas for clinical review; only an in-person medical evaluation can establish direct causes."
        }

    # -------------------------------------------------------------------------
    # 5. WHAT CAN THE CAREGIVER DO NOW? (Action Plan)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_caregiver_actions(
        cls,
        clinical_finding: Dict[str, Any],
        triage_level: str,
        age_bracket: str,
        child_name: Optional[str] = None
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        triage_upper = (triage_level or "").upper()
        actions = []

        # Tiered by urgency and category
        if "RED" in triage_upper or "EMERGENCY" in triage_upper or category == ExplanationRules.CAT_HIGHER_CONCERN:
            actions.append("Seek immediate medical evaluation at the nearest pediatric clinic, hospital, or nutrition rehabilitation centre.")
            actions.append("Keep the child warm, offer frequent sips of fluid or breastmilk if conscious, and do not force large boluses of solid food.")
            actions.append("Do not administer over-the-counter medicines or antibiotics without explicit prescription from an attending medical doctor.")
            actions.append("Inform the clinical team immediately if the child develops vomiting, high fever, extreme lethargy, or fast breathing.")
        elif "YELLOW" in triage_upper or category == ExplanationRules.CAT_MODERATE_CONCERN:
            actions.append("Schedule a comprehensive growth assessment with a pediatrician, nurse, or community healthcare worker within the next 3 to 5 days.")
            if age_bracket == ExplanationRules.AGE_UNDER_6M:
                actions.append("Practice exclusive breastfeeding on demand, ensuring 8 to 12 effective nursing sessions daily without giving water, formula, or solids.")
            elif age_bracket == ExplanationRules.AGE_6_TO_23M:
                actions.append("Continue frequent breastfeeding alongside energy-dense, diverse complementary meals (incorporating pulses, eggs, dairy, or locally available nutrient-rich foods).")
            else:
                actions.append("Provide 3 balanced family meals and 2 nutritious snacks daily, emphasizing protein and micronutrient variety.")
            actions.append("Ensure any ongoing symptoms such as diarrhea, fever, or reduced appetite are evaluated by a clinical provider.")
            actions.append("Plan a follow-up weight check in 2 to 4 weeks to evaluate growth trajectory.")
        else:  # Normal / Routine
            actions.append("Continue routine preventive care, adhering to the national immunization schedule and routine pediatric check-ups.")
            if age_bracket == ExplanationRules.AGE_UNDER_6M:
                actions.append("Maintain exclusive breastfeeding on demand day and night; no water, teas, or other liquids are needed before 6 months.")
            elif age_bracket == ExplanationRules.AGE_6_TO_23M:
                actions.append("Continue diverse complementary feeding offering at least 5 of the 8 WHO food groups daily while sustaining breastfeeding.")
            else:
                actions.append("Provide balanced, colorful family meals rich in legumes, vegetables, fruits, and quality protein sources.")
            actions.append("Keep regular monthly growth tracking at your local health centre or anganwadi.")

        validated_actions = ExplanationSafetyValidator.validate_action_plan(actions)
        return {
            "status": STATUS_AVAILABLE,
            "triage_guidance": triage_level,
            "actions": validated_actions
        }

    # -------------------------------------------------------------------------
    # 6. HOW CAN THIS BE PREVENTED? (Age-Aware Prevention)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_prevention_guidance(cls, age_bracket: str) -> Dict[str, Any]:
        if age_bracket == ExplanationRules.AGE_UNDER_6M:
            return {
                "status": STATUS_AVAILABLE,
                "age_category": "Infants Under 6 Months (<6m)",
                "guidance_summary": "Exclusive breastfeeding is the single most effective protection against malnutrition and infections in early infancy.",
                "principles": [
                    {
                        "principle": "Exclusive Breastfeeding Only",
                        "description": "Provide only breastmilk. Do not introduce water, sugar water, tea, animal milks, or baby cereals before 6 months of age."
                    },
                    {
                        "principle": "Frequent On-Demand Feeding",
                        "description": "Feed whenever the infant shows early hunger cues (rooting, hand-to-mouth), typically 8 to 12 times in 24 hours."
                    },
                    {
                        "principle": "Effective Latch & Positioning",
                        "description": "Ensure a comfortable, deep latch to maximize milk transfer and maintain robust maternal milk production."
                    },
                    {
                        "principle": "Timely Immunization & Growth Tracking",
                        "description": "Adhere strictly to the national childhood immunization schedule and monthly weight monitoring."
                    }
                ]
            }
        elif age_bracket == ExplanationRules.AGE_6_TO_23M:
            return {
                "status": STATUS_AVAILABLE,
                "age_category": "Infants & Young Children 6–23 Months",
                "guidance_summary": "Appropriate complementary feeding starting at 6 months while continuing breastfeeding protects growth and micronutrient sufficiency.",
                "principles": [
                    {
                        "principle": "Timely Complementary Feeding",
                        "description": "Introduce thick, energy-dense foods at exactly 6 completed months while continuing on-demand breastfeeding."
                    },
                    {
                        "principle": "Dietary Diversity (Minimum 5 of 8 Groups)",
                        "description": "Aim to include at least 5 of the 8 WHO food groups daily: grains/roots, pulses/nuts, dairy, flesh foods, eggs, vitamin A-rich produce, other fruits/vegetables, breastmilk."
                    },
                    {
                        "principle": "Age-Appropriate Texture & Meal Frequency",
                        "description": "Progress from smooth purées to mashed foods and soft finger foods (2-3 meals/day for 6-8m; 3-4 meals/day plus snacks for 9-23m)."
                    },
                    {
                        "principle": "Hygiene & Responsive Feeding",
                        "description": "Wash hands with soap before food preparation and feeding; feed patiently, encouraging the child without force."
                    }
                ]
            }
        elif age_bracket == ExplanationRules.AGE_24_TO_59M:
            return {
                "status": STATUS_AVAILABLE,
                "age_category": "Young Children 24–59 Months",
                "guidance_summary": "A balanced, nutrient-rich family diet with regular meal structure and active health monitoring supports sustained growth.",
                "principles": [
                    {
                        "principle": "Balanced Family Meals",
                        "description": "Provide 3 wholesome family meals and 2 healthy snacks daily, minimizing ultra-processed and sugary snacks."
                    },
                    {
                        "principle": "Protein & Micronutrient Density",
                        "description": "Incorporate legumes, pulses, eggs, dairy, green leafy vegetables, and seasonal fruits regularly."
                    },
                    {
                        "principle": "WASH (Water, Sanitation & Hygiene)",
                        "description": "Safe drinking water, hygienic food storage, and supervised handwashing prevent recurrent diarrheal illness."
                    },
                    {
                        "principle": "Periodic Deworming & Health Checks",
                        "description": "Participate in bi-annual deworming programs and regular anthropometric monitoring at preschool or health centres."
                    }
                ]
            }
        else:
            return {
                "status": STATUS_AVAILABLE,
                "age_category": "Children 5 Years and Older",
                "guidance_summary": "Nutritional adequacy, regular physical activity, and varied diet support continuous adolescent development.",
                "principles": [
                    {"principle": "Varied Nutrition", "description": "Ensure balanced food groups across regular daily meals."},
                    {"principle": "Hydration & Activity", "description": "Encourage adequate water intake and daily active play."}
                ]
            }

    # -------------------------------------------------------------------------
    # 7. WHAT SHOULD BE MONITORED?
    # -------------------------------------------------------------------------
    @classmethod
    def generate_monitoring_guidance(
        cls,
        clinical_finding: Dict[str, Any],
        longitudinal_data: Optional[Dict[str, Any]] = None,
        is_single_visit: bool = True
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)

        if category == ExplanationRules.CAT_HIGHER_CONCERN:
            frequency = "Daily monitoring under direct clinical guidance; immediate review if danger signs appear."
        elif category == ExplanationRules.CAT_MODERATE_CONCERN:
            frequency = "Weekly weight tracking for the first month, followed by bi-weekly checks until growth velocity stabilizes."
        else:
            frequency = "Routine monthly growth and developmental monitoring at your local pediatric health centre."

        danger_signs = [
            "Loss of appetite or inability to feed or drink",
            "Persistent vomiting (unable to keep any liquids down)",
            "Lethargy, extreme drowsiness, or unresponsiveness",
            "Fast or difficult breathing",
            "High fever that does not respond to standard measures",
            "Sudden development of swelling in feet, legs, or face",
            "Watery diarrhea lasting more than 24 hours"
        ]

        parameters = [
            "Body weight trend measured on the same calibrated scale",
            "Appetite and enthusiasm during feeding times",
            "Daily activity, playfulness, and energy levels",
            "Fluid intake and frequency of wet diapers (urination)"
        ]

        return {
            "status": STATUS_AVAILABLE,
            "recommended_frequency": frequency,
            "parameters_to_track": parameters,
            "clinical_danger_signs": danger_signs,
            "is_single_visit": is_single_visit
        }

    # -------------------------------------------------------------------------
    # 8. WHEN IS PROFESSIONAL ASSESSMENT IMPORTANT?
    # -------------------------------------------------------------------------
    @classmethod
    def generate_professional_assessment(
        cls,
        triage_level: str,
        is_emergency: bool,
        clinical_finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        triage_upper = (triage_level or "").upper()

        if is_emergency or "RED" in triage_upper or category == ExplanationRules.CAT_HIGHER_CONCERN:
            urgency = "Immediate In-Person Emergency Evaluation"
            narrative = (
                "Professional medical assessment is indicated urgently today. "
                "The identified growth measurements or physical signs reflect severe nutritional vulnerability, "
                "which carries risk of metabolic instability and infection if not evaluated promptly by qualified pediatric staff."
            )
        elif "YELLOW" in triage_upper or category == ExplanationRules.CAT_MODERATE_CONCERN:
            urgency = "Prompt Outpatient Medical Review (Within 3–5 Days)"
            narrative = (
                "A formal pediatric consultation is recommended in the coming days. "
                "A doctor or trained community health worker can examine the child in person, check for underlying health conditions, "
                "review feeding patterns in detail, and provide individualized nutritional guidance."
            )
        else:
            urgency = "Routine Preventive Health Follow-Up"
            narrative = (
                "Professional assessment is appropriate at your next scheduled routine well-child or immunization visit. "
                "However, if the child develops fever, persistent vomiting, diarrhea, or difficulty feeding at any time, "
                "consult a healthcare provider promptly regardless of routine scheduling."
            )

        return {
            "status": STATUS_AVAILABLE,
            "urgency": urgency,
            "narrative": ExplanationSafetyValidator.sanitize_explanation_text(narrative)
        }

    # -------------------------------------------------------------------------
    # 9. IMPORTANT NOTE (Replaces previous 'What should I not worry about')
    # -------------------------------------------------------------------------
    @classmethod
    def generate_important_note(cls, clinical_finding: Dict[str, Any]) -> Dict[str, Any]:
        text = (
            "This screening result is not a diagnosis. The findings should be interpreted "
            "together with the child's complete growth history, dietary intake, and professional "
            "clinical assessment where indicated."
        )
        return {
            "status": STATUS_AVAILABLE,
            "title": "IMPORTANT NOTE",
            "text": ExplanationSafetyValidator.sanitize_explanation_text(text)
        }

    # Backward compatibility alias
    generate_what_not_to_worry_about = generate_important_note

    # -------------------------------------------------------------------------
    # 10. WHY DID THE AI GIVE THIS RESULT? (SHAP & Model Attribution)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_shap_explanation(
        cls,
        shap_factors: Optional[List[Dict[str, Any]]],
        prediction_label: str = "Normal"
    ) -> Dict[str, Any]:
        if not shap_factors:
            return {
                "status": STATUS_NOT_AVAILABLE,
                "summary": "Detailed feature attribution is not available for this assessment.",
                "features": [],
                "interpretation": "The screening model completed the assessment, but detailed individual feature weights could not be extracted."
            }

        high_impact = []
        for item in shap_factors[:4]:
            feat = item.get("display_name", item.get("feature", "Measurement"))
            val = item.get("measured_value", item.get("value", ""))
            impact = item.get("impact", "Neutral")
            high_impact.append(f"{feat} ({val}) with {impact.lower()} attribution")

        interpretation = (
            f"The AI model gave greatest weight to the child's recorded physical measurements in evaluating the classification ({prediction_label}). "
            f"Specifically, {', '.join(high_impact)} contributed most significantly to the screening calculation."
        )

        return {
            "status": STATUS_AVAILABLE,
            "summary": "Feature attribution shows how specific measurements influenced the AI screening output.",
            "features": shap_factors,
            "interpretation": ExplanationSafetyValidator.sanitize_explanation_text(interpretation)
        }

    # -------------------------------------------------------------------------
    # 11. GRAD-CAM / VISION EXPLANATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_gradcam_explanation(
        cls,
        vision_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not vision_data or not vision_data.get("has_image"):
            return {
                "status": STATUS_NOT_AVAILABLE,
                "summary": "Vision assessment: Not available",
                "narrative": "No photograph was uploaded, so the image-based assessment was not used for this screening."
            }

        features_observed = vision_data.get("features_observed", "body composition and posture")
        narrative = (
            f"The visual analysis model reviewed the uploaded photograph, focusing attention on {features_observed}. "
            "Visual screening assists clinical screening but cannot assess bilateral pedal edema, hydration, or subcutaneous skinfold depth with clinical certainty."
        )

        return {
            "status": STATUS_AVAILABLE,
            "summary": "Image-based visual feature analysis",
            "narrative": ExplanationSafetyValidator.sanitize_explanation_text(narrative),
            "heatmap_available": bool(vision_data.get("heatmap_url"))
        }

    # -------------------------------------------------------------------------
    # 12. DIETARY DIVERSITY (MDD) EXPLANATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_dietary_diversity_explanation(
        cls,
        dietary_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not dietary_data or not dietary_data.get("assessed"):
            return {
                "status": STATUS_NOT_ASSESSED,
                "summary": "Dietary diversity: Not assessed",
                "narrative": "A 24-hour food recall has not been completed, so dietary diversity cannot be assessed yet.",
                "score": None,
                "target": "5 of 8 food groups (WHO/UNICEF IYCF standard)"
            }

        score = dietary_data.get("score", 0)
        total = dietary_data.get("total", 8)
        groups = dietary_data.get("groups_consumed", [])

        if score >= 5:
            narrative = (
                f"The 24-hour food recall recorded foods from {score} of the 8 assessed food groups ({', '.join(groups) if groups else ''}). "
                "This meets the WHO/UNICEF Minimum Dietary Diversity threshold, indicating diverse micronutrient intake."
            )
        else:
            narrative = (
                f"The food recall recorded foods from {score} of the 8 assessed food groups. "
                "This falls below the WHO recommendation of at least 5 food groups daily, suggesting that expanding meal variety would benefit nutritional adequacy."
            )

        return {
            "status": STATUS_AVAILABLE,
            "summary": f"Dietary Diversity Score: {score}/{total}",
            "narrative": ExplanationSafetyValidator.sanitize_explanation_text(narrative),
            "score": score,
            "target": "5 of 8 food groups (WHO/UNICEF IYCF standard)"
        }

    # -------------------------------------------------------------------------
    # 13. LONGITUDINAL GROWTH OVER TIME
    # -------------------------------------------------------------------------
    @classmethod
    def generate_longitudinal_explanation(
        cls,
        longitudinal_data: Optional[Dict[str, Any]] = None,
        visits_count: int = 1
    ) -> Dict[str, Any]:
        if visits_count <= 1 or not longitudinal_data or not longitudinal_data.get("has_history"):
            return {
                "status": STATUS_NOT_ASSESSED,
                "summary": "Longitudinal trend: Insufficient history",
                "narrative": "There is only one recorded assessment, so a growth trend cannot be calculated yet. Sequential visits are required to assess growth velocity.",
                "velocity": None
            }

        vel = longitudinal_data.get("weight_velocity_g_day")
        vel_text = f"{vel:+.1f} g/day" if vel is not None else "undetermined"
        faltering = bool(longitudinal_data.get("early_warning_alert"))

        if faltering:
            narrative = (
                f"Growth analysis across {visits_count} visits shows a downward weight trajectory ({vel_text}). "
                "This slowdown in growth velocity highlights an early warning signal before acute physical deficits become severe."
            )
        else:
            narrative = (
                f"Sequential tracking across {visits_count} visits demonstrates a positive growth trajectory with a weight gain velocity of {vel_text}. "
                "This indicates that the child is steadily gaining mass over time."
            )

        return {
            "status": STATUS_AVAILABLE,
            "summary": f"Longitudinal Velocity: {vel_text}",
            "narrative": ExplanationSafetyValidator.sanitize_explanation_text(narrative),
            "velocity_g_day": vel,
            "visits_count": visits_count
        }

    # -------------------------------------------------------------------------
    # 14. RISK SCORE EXPLANATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_risk_score_explanation(
        cls,
        risk_score: Optional[float] = None
    ) -> Dict[str, Any]:
        if risk_score is None:
            return {
                "status": STATUS_NOT_AVAILABLE,
                "title": "Composite Screening Risk Score",
                "score": None,
                "narrative": "A composite risk score was not computed for this assessment record."
            }

        score_val = round(float(risk_score), 1)
        if score_val < 30.0:
            level = "Low"
            desc = "indicates that current growth and health indicators fall largely within standard reference bounds."
        elif score_val < 65.0:
            level = "Moderate"
            desc = "indicates that the assessment deserves closer attention, particularly because of the child's recorded growth measurements or feeding history."
        else:
            level = "High"
            desc = "indicates elevated nutritional vulnerability that warrants prompt clinical and dietary evaluation."

        narrative = (
            f"Composite Screening Risk Score: {score_val}/100 ({level} Priority). "
            f"This score summarizes several assessment factors used by the screening system. "
            "It is not a diagnosis or a probability that the child has a disease; rather, it " + desc
        )

        return {
            "status": STATUS_AVAILABLE,
            "title": "Composite Screening Risk Score",
            "score": score_val,
            "level": level,
            "narrative": ExplanationSafetyValidator.sanitize_explanation_text(narrative)
        }

    # -------------------------------------------------------------------------
    # 15. THREE AUDIENCE TIERS
    # -------------------------------------------------------------------------
    @classmethod
    def build_parent_view(cls, narratives: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "in_simple_words": narratives.get("in_simple_words", {}).get("text", ""),
            "what_is_happening": narratives.get("what_is_happening", {}).get("text", ""),
            "what_this_means": narratives.get("what_this_means", {}).get("text", ""),
            "why_is_system_concerned": narratives.get("why_system_concerned", {}).get("summary", ""),
            "contributing_factors": [
                f.get("factor") for f in narratives.get("why_system_concerned", {}).get("factors", [])
            ],
            "what_to_do_now": narratives.get("caregiver_actions", {}).get("actions", []),
            "prevention_guidance": narratives.get("prevention", {}).get("guidance_summary", ""),
            "monitoring_guidance": narratives.get("monitoring", {}).get("recommended_frequency", ""),
            "what_not_to_worry_about": narratives.get("what_not_to_worry_about", {}).get("text", ""),
            "professional_assessment": narratives.get("professional_assessment", {}).get("narrative", "")
        }

    @classmethod
    def build_detailed_view(
        cls,
        narratives: Dict[str, Any],
        measurements: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "summary_finding": narratives.get("in_simple_words", {}).get("text", ""),
            "clinical_status": narratives.get("what_is_happening", {}).get("text", ""),
            "interpretation": narratives.get("what_this_means", {}).get("text", ""),
            "measurements_evaluated": measurements,
            "contributing_factors": narratives.get("why_system_concerned", {}).get("factors", []),
            "discrepancy_explanation": narratives.get("discrepancy", {}).get("summary", ""),
            "action_plan": narratives.get("caregiver_actions", {}).get("actions", []),
            "prevention_principles": narratives.get("prevention", {}).get("principles", []),
            "monitoring_parameters": narratives.get("monitoring", {}).get("parameters_to_track", []),
            "clinical_danger_signs": narratives.get("monitoring", {}).get("clinical_danger_signs", []),
            "dietary_diversity": narratives.get("dietary_diversity", {}).get("narrative", ""),
            "growth_trajectory": narratives.get("longitudinal", {}).get("narrative", "")
        }

    @classmethod
    def build_technical_view(
        cls,
        tech_data: Dict[str, Any],
        narratives: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "who_z_scores": tech_data.get("who_z_scores", {}),
            "ai_prediction": tech_data.get("ai_prediction", {}),
            "clinical_triage": tech_data.get("clinical_triage", {}),
            "risk_score_raw": tech_data.get("risk_score"),
            "risk_score_explanation": narratives.get("risk_score", {}),
            "feature_attribution_shap": narratives.get("shap", {}),
            "vision_gradcam": narratives.get("gradcam", {}),
            "model_metadata": tech_data.get("model_metadata", {
                "algorithm": "CatBoostClassifier (Multimodal Anthropometric)",
                "who_standard": "WHO 2006 LMS Box-Cox reference tables",
                "decision_support_version": "ChildNutri AI v2.4-Review4"
            }),
            "discrepancy_analysis": narratives.get("discrepancy", {})
        }

    # =========================================================================
    # DOCTOR-LIKE 12-SECTION CLINICAL EXPLANATION GENERATORS
    # =========================================================================

    @classmethod
    def generate_doctor_assessment_summary(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None,
        factors: Optional[List[Dict[str, Any]]] = None,
        longitudinal_data: Optional[Dict[str, Any]] = None,
        whz: Optional[float] = None,
        muac: Optional[float] = None,
        has_bilateral_edema: bool = False,
        triage_level: str = "ROUTINE (GREEN)"
    ) -> str:
        name_str = child_name.strip() if child_name and child_name.strip() else "your child"
        possessive = f"{name_str}'s" if name_str != "your child" else "your child's"
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        # Downward weight trend check
        has_downward_trend = False
        if longitudinal_data:
            if longitudinal_data.get("early_warning_alert"):
                has_downward_trend = True
            elif longitudinal_data.get("weight_velocity_g_day") is not None:
                if float(longitudinal_data.get("weight_velocity_g_day", 0)) < 0:
                    has_downward_trend = True

        # Factor names
        factor_items = []
        for f in (factors or []):
            fn = f.get("factor", "").lower()
            if "diarrhea" in fn or "illness" in fn or "fever" in fn or "vomit" in fn:
                factor_items.append("recent illness")
            elif "appetite" in fn or "diet" in fn or "intake" in fn or "variety" in fn:
                factor_items.append("limited dietary variety")
        factor_items = list(dict.fromkeys(factor_items))

        if category == ExplanationRules.CAT_NORMAL:
            return (
                f"Your child's current growth measurements do not show a clear nutrition-related concern in this screening. "
                "The recorded measurements are within the assessed range and no major growth warning was identified by the current screening rules. "
                "Healthy growth depends on regular age-appropriate feeding, routine health checks, and continued growth monitoring."
            )

        if code == "EDEMA_SAM" or has_bilateral_edema:
            return (
                f"The primary concern in this assessment is the presence of fluid retention (bilateral pedal edema) in {possessive} feet, "
                "which is a serious clinical sign requiring prompt in-person medical evaluation. "
                "The screening indicates severe acute nutritional vulnerability that should be assessed by a healthcare professional immediately."
            )

        # Growth concern summary
        parts = []
        if code in ["SEVERE_WASTING", "MODERATE_WASTING"] or (whz is not None and whz < -2.0):
            parts.append(f"The main concern in this assessment is that {possessive} current weight is lower than expected for their height. The recorded measurements suggest that growth needs closer attention.")
        elif code == "GROWTH_FALTERING":
            parts.append(f"The main concern in this assessment is a slowing or decrease in {possessive} weight between recent visits, indicating that growth needs closer attention.")
        elif code == "STUNTING":
            parts.append(f"The main concern in this assessment is that {possessive} height is lower than expected for their age, reflecting longer-term linear growth progress.")
        elif code == "UNDERWEIGHT":
            parts.append(f"The main concern in this assessment is that {possessive} overall weight is lower than expected for their age.")
        else:
            parts.append("The assessment has identified growth measurements that deserve closer clinical attention.")

        if has_downward_trend:
            parts.append("The child's weight has also decreased compared with the previous recorded visit, which makes the growth pattern more important to follow.")

        if factor_items:
            parts.append(f"{' and '.join(factor_items).capitalize()} may be contributing factors, but the screening cannot confirm the exact cause.")
        else:
            parts.append("The available measurements show a growth concern, but they do not tell us exactly why it is happening.")

        if "RED" in triage_level.upper() or category == ExplanationRules.CAT_HIGHER_CONCERN:
            parts.append("Prompt professional medical evaluation is recommended.")
        else:
            parts.append("Professional assessment and continued growth monitoring are recommended.")

        return " ".join(parts)

    @classmethod
    def generate_section_1_what_we_found(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None,
        age_months: Optional[float] = None
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")
        name_str = child_name.strip() if child_name and child_name.strip() else "Your child"
        possessive = f"{name_str}'s" if name_str != "Your child" else "Your child's"

        if category == ExplanationRules.CAT_NORMAL:
            statement = f"{possessive} current growth measurements do not show a clear nutrition-related concern in this screening."
        elif code == "EDEMA_SAM":
            statement = f"{possessive} assessment identified fluid swelling in both feet (bilateral pedal edema), which is an important clinical sign requiring prompt medical care."
        elif code in ["SEVERE_WASTING", "MODERATE_WASTING"]:
            statement = f"{possessive} current weight is lower than expected for their height according to the growth assessment."
        elif code == "GROWTH_FALTERING":
            statement = f"{possessive} recent growth trend shows that weight gain has slowed down or dropped between visits."
        elif code == "STUNTING":
            statement = f"{possessive} current height is lower than expected for their age according to the growth assessment."
        elif code == "UNDERWEIGHT":
            statement = f"{possessive} current weight is lower than expected for their age according to the growth assessment."
        else:
            statement = f"{possessive} current measurements indicate an anthropometric growth concern that needs closer attention."

        meas = measurements or {}
        wt = meas.get("weight_kg")
        ht = meas.get("height_cm")
        whz = meas.get("whz")
        haz = meas.get("haz")
        waz = meas.get("waz")
        muac = meas.get("muac_cm")
        edema = meas.get("has_bilateral_edema", False)

        evidence_lines = []
        if wt is not None: evidence_lines.append(f"Weight: {wt} kg")
        if ht is not None: evidence_lines.append(f"Height: {ht} cm")
        if whz is not None: evidence_lines.append(f"WHZ: {whz:+.2f} SD")
        if haz is not None: evidence_lines.append(f"HAZ: {haz:+.2f} SD")
        if waz is not None: evidence_lines.append(f"WAZ: {waz:+.2f} SD")
        if muac is not None: evidence_lines.append(f"MUAC: {muac:.1f} cm")
        if age_months is not None:
            age_display = int(age_months) if float(age_months).is_integer() else age_months
            evidence_lines.append(f"Age: {age_display} months")
        evidence_lines.append(f"Bilateral Pedal Edema: {'Present (+)' if edema else 'Absent'}")

        formatted_evidence = "\n".join(evidence_lines)

        return {
            "title": "What we found",
            "statement": ExplanationSafetyValidator.sanitize_explanation_text(statement),
            "empathic_statement": ExplanationSafetyValidator.sanitize_explanation_text(statement),
            "evidence": {
                "weight_kg": wt,
                "height_cm": ht,
                "whz": f"{whz:+.2f} SD" if whz is not None else None,
                "haz": f"{haz:+.2f} SD" if haz is not None else None,
                "waz": f"{waz:+.2f} SD" if waz is not None else None,
                "muac_cm": f"{muac:.1f} cm" if muac is not None else None,
                "age_months": age_months,
                "bilateral_edema": "Present (+)" if edema else "Absent"
            },
            "measurements_table": meas,
            "formatted_evidence": formatted_evidence
        }

    @classmethod
    def generate_section_2_reason(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None,
        longitudinal_data: Optional[Dict[str, Any]] = None,
        whz: Optional[float] = None,
        muac: Optional[float] = None,
        has_bilateral_edema: bool = False,
        has_history_or_factors: bool = True
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        if category == ExplanationRules.CAT_NORMAL:
            reason = "The recorded measurements are within the assessed range and no major growth warning was identified by the current screening rules."
            return {
                "title": "Reason",
                "text": reason,
                "primary_driver": reason,
                "trajectory_note": "",
                "underlying_evidence": "All measurements within standard reference limits.",
                "contributing_reasons": ["All measurements within standard reference limits."]
            }

        reasons_list = []
        if code == "EDEMA_SAM" or has_bilateral_edema:
            reasons_list.append("The presence of bilateral pedal edema is an important physical reason for acute clinical concern.")
        elif code in ["SEVERE_WASTING", "MODERATE_WASTING"] or (whz is not None and whz < -2.0):
            reasons_list.append("The main reason for concern is that your child's weight is lower than expected for their current height. The recorded growth measurements therefore need closer attention.")
        elif code == "GROWTH_FALTERING":
            reasons_list.append("The main reason for concern is that your child's weight has slowed down or decreased between recent visits rather than steadily gaining.")
        elif code == "STUNTING":
            reasons_list.append("The main reason for concern is that your child's height is lower than expected for their age, showing longer-term linear growth deficit.")
        elif code == "UNDERWEIGHT":
            reasons_list.append("The main reason for concern is that your child's overall weight is below expected standard percentiles for their age.")
        else:
            reasons_list.append("The recorded growth measurements show a pattern that warrants closer attention.")

        # Check longitudinal decrease
        if longitudinal_data and (longitudinal_data.get("early_warning_alert") or (longitudinal_data.get("weight_velocity_g_day") is not None and float(longitudinal_data.get("weight_velocity_g_day", 0)) < 0)):
            reasons_list.append("The recent decrease in weight also contributes to the concern.")

        # Check MUAC
        if muac is not None and muac < 12.5:
            reasons_list.append("The child's MUAC measurement was also considered when assessing the nutritional risk.")

        # Never invent a reason rule (Section 4):
        if len(reasons_list) == 1 and not has_history_or_factors and category != ExplanationRules.CAT_NORMAL:
            reasons_list.append("The available measurements show a growth concern, but they do not tell us exactly why it is happening.")

        reason_text = " ".join(reasons_list)
        return {
            "title": "Reason",
            "text": ExplanationSafetyValidator.sanitize_explanation_text(reason_text),
            "primary_driver": ExplanationSafetyValidator.sanitize_explanation_text(reasons_list[0] if reasons_list else reason_text),
            "trajectory_note": reasons_list[1] if len(reasons_list) > 1 else "",
            "underlying_evidence": "Anthropometric Z-score thresholds or growth velocity drop.",
            "contributing_reasons": reasons_list
        }

    @classmethod
    def generate_section_3_why_this_may_be_happening(
        cls,
        factors: List[Dict[str, Any]],
        clinical_finding: Dict[str, Any],
        has_history: bool = True
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)

        if category == ExplanationRules.CAT_NORMAL:
            return {
                "title": "Why this may be happening",
                "text": "Current feeding practices and general wellness appear to support healthy physical growth. Continued variety in daily meals supports ongoing health.",
                "disclaimer": "Possible contributing factor, not confirmed cause.",
                "factors": [],
                "factors_list": [],
                "is_history_complete": has_history
            }

        if not has_history or not factors:
            return {
                "title": "Why this may be happening",
                "text": "The feeding and illness history is incomplete, so we cannot determine whether dietary factors or recent health events are contributing to the current growth concern.",
                "disclaimer": "Possible contributing factor, not confirmed cause.",
                "factors": [],
                "factors_list": [],
                "is_history_complete": False
            }

        factor_names = [f.get("factor") for f in factors if f.get("factor")]
        narrative = (
            f"The assessment shows that your child has had {' and '.join(factor_names).lower()}. "
            "These factors can affect nutrition and growth, so they may be contributing to the current concern. "
            "However, the screening cannot confirm that either factor is the direct cause."
        )

        return {
            "title": "Why this may be happening",
            "text": ExplanationSafetyValidator.sanitize_explanation_text(narrative),
            "disclaimer": "Possible contributing factor, not confirmed cause.",
            "factors": factors,
            "factors_list": factors,
            "is_history_complete": True
        }

    @classmethod
    def generate_section_4_what_this_means(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        code = clinical_finding.get("code", "NORMAL")

        if category == ExplanationRules.CAT_NORMAL:
            text = (
                "This is reassuring based on the information available today. It does not mean that future growth problems are impossible, "
                "so routine feeding and growth monitoring should continue."
            )
        elif code == "EDEMA_SAM":
            text = (
                "This result means that your child's body is retaining fluid and experiencing acute nutritional strain. "
                "It requires in-person medical evaluation without delay so a doctor can evaluate fluid balance, check for underlying infections, and guide safe nutritional care."
            )
        else:
            text = (
                "This does not simply mean that your child needs to eat more. The growth measurement suggests that the child's current weight is lower than expected for their height, "
                "so the child's feeding, recent health, and growth pattern should be reviewed together. "
                "One measurement cannot tell us the complete story. Looking at previous measurements, feeding history, and recent illness can help us understand whether this is a temporary change or an ongoing growth concern."
            )

        return {
            "title": "What this means for your child",
            "text": ExplanationSafetyValidator.sanitize_explanation_text(text),
            "explanation": ExplanationSafetyValidator.sanitize_explanation_text(text),
            "practical_implication": "Routine feeding and growth monitoring should continue." if category == ExplanationRules.CAT_NORMAL else "Review feeding, health, and growth trajectory with a healthcare professional."
        }

    @classmethod
    def generate_section_5_what_you_should_do_now(
        cls,
        clinical_finding: Dict[str, Any],
        triage_level: str,
        age_bracket: str
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        triage_upper = (triage_level or "").upper()

        actions = []
        if "RED" in triage_upper or "EMERGENCY" in triage_upper or category == ExplanationRules.CAT_HIGHER_CONCERN:
            directive = "Seek prompt in-person medical evaluation at a pediatric facility."
            actions.append("Seek immediate medical evaluation at the nearest pediatric clinic, hospital, or nutrition centre.")
            actions.append("Keep the child warm, offer frequent sips of fluid or breastmilk if conscious, and do not force large boluses of solid food.")
            actions.append("Do not administer over-the-counter medicines or antibiotics without explicit prescription from a medical doctor.")
            actions.append("Inform the clinical team immediately if the child develops vomiting, high fever, extreme lethargy, or fast breathing.")
        elif "YELLOW" in triage_upper or category == ExplanationRules.CAT_MODERATE_CONCERN:
            directive = "Continue appropriate feeding and arrange professional assessment."
            actions.append("Continue regular age-appropriate feeding and pay attention to your child's appetite and feeding difficulties.")
            actions.append("Because the screening shows a growth concern, discuss these measurements with a healthcare professional who can assess your child in person.")
            actions.append("Schedule a growth review with a healthcare professional within 3 to 5 days.")
            actions.append("Plan a follow-up weight check in 2 to 4 weeks to evaluate growth trajectory.")
        else:
            directive = "Continue age-appropriate nutrition and routine growth checks."
            actions.append("Continue age-appropriate feeding, a varied diet, safe food and water practices, and routine health checks.")
            actions.append("Maintain routine monthly growth tracking at your local health centre or clinic.")
            actions.append("Ensure all routine childhood immunizations remain up to date.")

        return {
            "title": "What you should do now",
            "directive": directive,
            "primary_directive": directive,
            "actions": actions,
            "action_steps": actions
        }

    @classmethod
    def generate_section_6_how_to_protect_and_support(cls, age_bracket: str) -> Dict[str, Any]:
        if age_bracket == ExplanationRules.AGE_UNDER_6M:
            summary = (
                "For infants under 6 months, exclusive breastfeeding is the single most effective protection against malnutrition and infections. "
                "Provide only breastmilk on demand day and night (8 to 12 nursing sessions daily). Do not give water, teas, animal milk, or infant food before 6 months."
            )
            principles = [
                "Exclusive breastfeeding on demand (no water, animal milk, or infant food before 6 months).",
                "Effective latch and frequent nursing (8 to 12 times in 24 hours).",
                "Timely childhood immunizations and monthly weight checks."
            ]
        elif age_bracket == ExplanationRules.AGE_6_TO_23M:
            summary = (
                "For continued healthy growth, focus on age-appropriate feeding, a varied diet, safe food and water, good hygiene, and regular growth monitoring. "
                "If your child has repeated illness or feeding difficulties, discuss these concerns early with a healthcare professional."
            )
            principles = [
                "Timely, nutrient-dense complementary feeding offering at least 5 of the 8 WHO food groups daily alongside breastfeeding.",
                "Clean drinking water, handwashing before meals, and hygienic food storage to prevent gastrointestinal infections.",
                "Early clinical consultation whenever the child develops fever, cough, diarrhea, or feeding refusal."
            ]
        else:
            summary = (
                "For young children 2 to 5 years, providing 3 wholesome family meals and 2 nutritious snacks daily, emphasizing protein and micronutrient variety, supports healthy growth. "
                "Maintain clean water, good hygiene, and seek early medical attention during illness."
            )
            principles = [
                "Balanced family diet incorporating pulses, eggs, dairy, vegetables, and seasonal fruits.",
                "Safe drinking water, supervised handwashing, and bi-annual deworming.",
                "Prompt evaluation of persistent coughing, diarrhea, or low appetite."
            ]

        return {
            "title": "How to protect and support the child",
            "summary": summary,
            "principles": principles,
            "protection_principles": principles,
            "age_group": age_bracket
        }

    @classmethod
    def generate_section_7_what_to_monitor(
        cls,
        clinical_finding: Dict[str, Any],
        longitudinal_data: Optional[Dict[str, Any]] = None,
        visits_count: int = 1
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        has_history = (visits_count > 1) and bool(longitudinal_data and longitudinal_data.get("has_history"))
        vel = longitudinal_data.get("weight_velocity_g_day") if longitudinal_data else None

        if has_history:
            if vel is not None and vel < 0:
                trend_note = f"The child's weight has decreased across the recorded assessments ({vel:+.1f} g/day). This downward pattern is more important than looking at today's weight alone and should be reviewed during follow-up."
            elif vel is not None and vel > 0:
                trend_note = f"The child's weight shows positive gain ({vel:+.1f} g/day). Ongoing tracking will verify that growth velocity continues steadily."
            else:
                trend_note = "Growth tracking shows stable weight between recent visits. Continued monitoring is recommended."
        else:
            trend_note = "Only one assessment is currently available, so we cannot yet determine whether your child's growth is improving or declining over time."

        intro = "Pay particular attention to weight changes, appetite, feeding difficulties, and any further illness. Future measurements will help determine whether the growth pattern is improving or continuing downward."

        danger_signs = [
            "Loss of appetite or inability to feed or drink",
            "Persistent vomiting (unable to keep any liquids down)",
            "Lethargy, extreme drowsiness, or unresponsiveness",
            "Fast or difficult breathing",
            "High fever that does not respond to standard measures",
            "Sudden development of swelling in feet, legs, or face",
            "Watery diarrhea lasting more than 24 hours"
        ]

        parameters = [
            "Body weight trend measured on the same calibrated scale",
            "Appetite, feeding enthusiasm, and portion completion",
            "Daily activity, playfulness, and alertness",
            "Hydration status and frequency of urination"
        ]

        return {
            "title": "What to monitor",
            "intro": intro,
            "trend_note": trend_note,
            "trajectory_note": trend_note,
            "parameters": parameters,
            "tracking_parameters": parameters,
            "danger_signs": danger_signs,
            "frequency": "Routine well-child schedule" if category == ExplanationRules.CAT_NORMAL else "Follow-up in 2-4 weeks"
        }

    @classmethod
    def generate_section_8_when_professional_assessment(
        cls,
        triage_level: str,
        clinical_finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        triage_upper = (triage_level or "").upper()

        if "RED" in triage_upper or category == ExplanationRules.CAT_HIGHER_CONCERN:
            urgency = "Immediate"
            text = "The screening has identified findings that require prompt professional attention. The AI system cannot determine the final diagnosis or treatment on its own."
        elif "YELLOW" in triage_upper or category == ExplanationRules.CAT_MODERATE_CONCERN:
            urgency = "Prompt Outpatient (3–5 Days)"
            text = "Because the screening has identified a growth concern, professional assessment is recommended so the child's measurements, feeding history, recent illness, and overall health can be reviewed together."
        else:
            urgency = "Routine"
            text = "Professional assessment is appropriate at your next scheduled routine well-child or immunization visit. However, if the child develops fever, persistent vomiting, diarrhea, or difficulty feeding at any time, consult a healthcare provider promptly."

        return {
            "title": "When professional assessment is important",
            "urgency": urgency,
            "urgency_level": urgency,
            "text": ExplanationSafetyValidator.sanitize_explanation_text(text),
            "calm_guidance": ExplanationSafetyValidator.sanitize_explanation_text(text),
            "triggers": [
                "Fever lasting > 48 hours or not responding to care",
                "Repeated vomiting or inability to keep fluids down",
                "Marked lethargy, unresponsiveness, or rapid breathing",
                "Sudden development of bilateral pedal swelling"
            ] if category != ExplanationRules.CAT_NORMAL else [
                "Unusual feeding refusal or dehydration",
                "High persistent fever or difficulty breathing"
            ]
        }

    @classmethod
    def generate_section_9_why_the_ai_gave_this_result(
        cls,
        shap_factors: Optional[List[Dict[str, Any]]],
        prediction_label: str = "Normal",
        risk_score: Optional[float] = None,
        vision_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        top_feats = []
        if not shap_factors:
            feature_narrative = "The detailed feature explanation is not available for this assessment."
            features_list = []
        else:
            for item in shap_factors[:3]:
                feat_name = item.get("display_name", item.get("feature", "Measurement"))
                top_feats.append(feat_name)

            feat_str = " and ".join(top_feats) if top_feats else "physical measurements"
            feature_narrative = (
                f"The AI model gave the greatest importance to the child's {feat_str} when producing this result. "
                "These measurements formed an important part of the pattern that the model associated with increased nutritional risk."
            )
            features_list = shap_factors

        if risk_score is not None:
            risk_narrative = (
                f"Composite Screening Risk Score: {round(float(risk_score), 1)}/100. "
                "This score combines several assessment factors to summarize the level of concern identified by the screening system. "
                "It is not a diagnosis and should not be interpreted as the probability that a child has a disease."
            )
        else:
            risk_narrative = "A composite screening risk score was not computed for this assessment."

        if vision_data and vision_data.get("has_image"):
            vision_narrative = (
                "The highlighted regions show where the vision model focused when producing its screening result. "
                "This helps explain the model's attention but does not prove that a highlighted area represents a medical problem."
            )
        else:
            vision_narrative = "No photograph was provided, so the image-based AI assessment was not used."

        return {
            "title": "Why the AI gave this result",
            "feature_narrative": ExplanationSafetyValidator.sanitize_explanation_text(feature_narrative),
            "parent_translation": ExplanationSafetyValidator.sanitize_explanation_text(feature_narrative),
            "features_list": features_list,
            "strongest_features": top_feats,
            "risk_score_narrative": risk_narrative,
            "risk_score": round(float(risk_score), 1) if risk_score is not None else None,
            "vision_narrative": vision_narrative,
            "gradcam_note": vision_narrative
        }

    @classmethod
    def generate_section_10_who_assessment(
        cls,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        baz: Optional[float],
        muac: Optional[float],
        clinical_finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)

        if category == ExplanationRules.CAT_NORMAL:
            narrative = "According to the WHO growth reference used by the system, your child's growth measurements fall within standard expected reference limits."
        elif whz is not None and whz < -2.0:
            narrative = "According to the WHO growth reference used by the system, your child's weight-for-height measurement is below the expected range. This is why the growth assessment has been flagged for attention."
        elif haz is not None and haz < -2.0:
            narrative = "According to the WHO growth reference used by the system, your child's height-for-age measurement is below the expected range, reflecting longer-term linear growth."
        elif waz is not None and waz < -2.0:
            narrative = "According to the WHO growth reference used by the system, your child's weight-for-age measurement is below expected reference percentiles."
        else:
            narrative = "The WHO growth reference was used to calculate standard Z-scores for height, weight, and arm circumference."

        z_scores = {
            "whz": f"{whz:+.2f} SD" if whz is not None else "Not recorded",
            "haz": f"{haz:+.2f} SD" if haz is not None else "Not recorded",
            "waz": f"{waz:+.2f} SD" if waz is not None else "Not recorded",
            "baz": f"{baz:+.2f} SD" if baz is not None else "Not available",
            "muac": f"{muac:.1f} cm" if muac is not None else "Not recorded"
        }

        return {
            "title": "WHO growth assessment",
            "narrative": narrative,
            "z_scores": z_scores,
            "scores": z_scores
        }

    @classmethod
    def generate_section_11_clinical_triage(
        cls,
        triage_level: str,
        discrepancy_info: Dict[str, Any],
        clinical_finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        category = clinical_finding.get("category", ExplanationRules.CAT_NORMAL)
        triage_upper = (triage_level or "").upper()

        if "RED" in triage_upper or category == ExplanationRules.CAT_HIGHER_CONCERN:
            triage_text = "The clinical safety rules have identified findings that require prompt professional assessment."
        elif "YELLOW" in triage_upper or category == ExplanationRules.CAT_MODERATE_CONCERN:
            triage_text = "The clinical safety rules place the child in a monitoring category, meaning the findings should be followed up rather than treated as a final diagnosis."
        else:
            triage_text = "The clinical safety rules classify this assessment in the routine monitoring category."

        has_conflict = discrepancy_info.get("has_discrepancy", False)
        if has_conflict:
            conflict_text = (
                "The assessment layers do not completely agree. The WHO growth measurement shows a concern, while the AI model classified the overall pattern differently. "
                "Because of this difference, the result should be reviewed using the child's complete health and growth information rather than relying on the AI prediction alone. "
                "Clinical safety rules and actual WHO measurements always take precedence over AI predictions."
            )
        else:
            conflict_text = "The three assessment layers point toward a concordant evaluation of the child's growth and nutritional status."

        overall_synthesis = (
            "Overall: The WHO measurement, AI pattern analysis, and clinical safety triage provide distinct perspectives. "
            "Deterministic clinical rules and confirmed anthropometric measurements guide clinical decision-making."
        )

        return {
            "title": "Clinical assessment",
            "triage_text": triage_text,
            "safety_priority": triage_text,
            "triage_level": triage_level,
            "conflict_text": conflict_text,
            "discrepancy_reconciliation": conflict_text,
            "has_conflict": has_conflict,
            "overall_synthesis": overall_synthesis
        }

    @classmethod
    def generate_section_12_limitations(cls) -> Dict[str, Any]:
        notice = "This screening system helps identify children who may need closer attention. It cannot determine the exact cause of a growth problem or replace an examination by a healthcare professional."
        return {
            "title": "Important note & limitations",
            "notice": notice,
            "limitations": DATA_LIMITATIONS,
            "boundaries": DATA_LIMITATIONS
        }

    @classmethod
    def build_doctor_explanation(
        cls,
        clinical_finding: Dict[str, Any],
        child_name: Optional[str] = None,
        age_months: Optional[float] = None,
        measurements: Optional[Dict[str, Any]] = None,
        factors: Optional[List[Dict[str, Any]]] = None,
        longitudinal_data: Optional[Dict[str, Any]] = None,
        whz: Optional[float] = None,
        haz: Optional[float] = None,
        waz: Optional[float] = None,
        baz: Optional[float] = None,
        muac: Optional[float] = None,
        has_bilateral_edema: bool = False,
        prediction_label: str = "Normal",
        risk_score: Optional[float] = None,
        triage_level: str = "ROUTINE (GREEN)",
        discrepancy_info: Optional[Dict[str, Any]] = None,
        shap_factors: Optional[List[Dict[str, Any]]] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        visits_count: int = 1,
        age_bracket: str = ExplanationRules.AGE_6_TO_23M
    ) -> Dict[str, Any]:
        """
        Assembles the authoritative 12-section Doctor-Like Explanation Structure
        along with the top-level Assessment Summary.
        """
        discrepancy_info = discrepancy_info or {}
        factors = factors or []
        has_hist = (visits_count > 1) or bool(factors)

        summary = cls.generate_doctor_assessment_summary(
            clinical_finding=clinical_finding,
            child_name=child_name,
            factors=factors,
            longitudinal_data=longitudinal_data,
            whz=whz,
            muac=muac,
            has_bilateral_edema=has_bilateral_edema,
            triage_level=triage_level
        )

        sec1 = cls.generate_section_1_what_we_found(
            clinical_finding=clinical_finding,
            child_name=child_name,
            measurements=measurements,
            age_months=age_months
        )

        sec2 = cls.generate_section_2_reason(
            clinical_finding=clinical_finding,
            child_name=child_name,
            longitudinal_data=longitudinal_data,
            whz=whz,
            muac=muac,
            has_bilateral_edema=has_bilateral_edema,
            has_history_or_factors=has_hist
        )

        sec3 = cls.generate_section_3_why_this_may_be_happening(
            factors=factors,
            clinical_finding=clinical_finding,
            has_history=has_hist
        )

        sec4 = cls.generate_section_4_what_this_means(
            clinical_finding=clinical_finding,
            child_name=child_name
        )

        sec5 = cls.generate_section_5_what_you_should_do_now(
            clinical_finding=clinical_finding,
            triage_level=triage_level,
            age_bracket=age_bracket
        )

        sec6 = cls.generate_section_6_how_to_protect_and_support(
            age_bracket=age_bracket
        )

        sec7 = cls.generate_section_7_what_to_monitor(
            clinical_finding=clinical_finding,
            longitudinal_data=longitudinal_data,
            visits_count=visits_count
        )

        sec8 = cls.generate_section_8_when_professional_assessment(
            triage_level=triage_level,
            clinical_finding=clinical_finding
        )

        sec9 = cls.generate_section_9_why_the_ai_gave_this_result(
            shap_factors=shap_factors,
            prediction_label=prediction_label,
            risk_score=risk_score,
            vision_data=vision_data
        )

        sec10 = cls.generate_section_10_who_assessment(
            whz=whz,
            haz=haz,
            waz=waz,
            baz=baz,
            muac=muac,
            clinical_finding=clinical_finding
        )

        sec11 = cls.generate_section_11_clinical_triage(
            triage_level=triage_level,
            discrepancy_info=discrepancy_info,
            clinical_finding=clinical_finding
        )

        sec12 = cls.generate_section_12_limitations()

        ordered_sections = [
            {"number": 1, "id": "what_we_found", "title": "WHAT WE FOUND", "data": sec1},
            {"number": 2, "id": "reason", "title": "REASON", "data": sec2},
            {"number": 3, "id": "why_this_may_be_happening", "title": "WHY THIS MAY BE HAPPENING", "data": sec3},
            {"number": 4, "id": "what_this_means", "title": "WHAT THIS MEANS FOR YOUR CHILD", "data": sec4},
            {"number": 5, "id": "what_you_should_do_now", "title": "WHAT YOU SHOULD DO NOW", "data": sec5},
            {"number": 6, "id": "how_to_protect_and_support", "title": "HOW TO PROTECT / SUPPORT THE CHILD", "data": sec6},
            {"number": 7, "id": "what_to_monitor", "title": "WHAT TO MONITOR", "data": sec7},
            {"number": 8, "id": "when_professional_assessment_important", "title": "WHEN PROFESSIONAL ASSESSMENT IS IMPORTANT", "data": sec8},
            {"number": 9, "id": "why_the_ai_gave_this_result", "title": "WHY THE AI GAVE THIS RESULT", "data": sec9},
            {"number": 10, "id": "who_assessment", "title": "WHO ASSESSMENT", "data": sec10},
            {"number": 11, "id": "clinical_triage", "title": "CLINICAL TRIAGE", "data": sec11},
            {"number": 12, "id": "limitations", "title": "LIMITATIONS", "data": sec12}
        ]

        return {
            "assessment_summary": summary,
            "what_we_found": sec1,
            "reason": sec2,
            "why_this_may_be_happening": sec3,
            "what_this_means": sec4,
            "what_you_should_do_now": sec5,
            "how_to_protect_and_support": sec6,
            "what_to_monitor": sec7,
            "when_professional_assessment_important": sec8,
            "why_the_ai_gave_this_result": sec9,
            "who_assessment": sec10,
            "clinical_triage": sec11,
            "limitations": sec12,
            "sections": ordered_sections
        }
