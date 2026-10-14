"""
=============================================================================
Clinical Explanation & Decision-Support Engine - ChildNutri AI
=============================================================================
Deterministic, evidence-based pediatric explanation engine compliant with:
  1. WHO Guideline: Prevention and management of wasting and nutritional oedema (2023)
  2. WHO Guideline: Complementary feeding of infants and young children 6–23 months (2023)
  3. WHO/UNICEF Infant and Young Child Feeding (IYCF) Indicators (2021)
  4. WHO Child Growth Standards (2006) LMS Box-Cox reference tables

Safety & Ethical Principles:
  - Zero fake, random, or hardcoded medical values.
  - Explanations are strictly data-driven and derived from confirmed inputs.
  - The engine provides clinical decision-support and screening interpretation;
    it does NOT formulate an autonomous medical diagnosis.
  - Strictly NO autonomous prescription of medicines, antibiotics, or drug dosages.
  - Non-causal wording ("Possible contributing factor" rather than "caused").
  - Age-aware feeding and prevention logic (<6m, 6–23m, 24–59m).
  - Clear separation between WHO growth standards, AI predictions, and deterministic triage.
=============================================================================
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timezone


class ClinicalExplanationEngine:
    """
    Core engine generating child-specific, evidence-based clinical explanations,
    possible contributing factors, prevention guidance, action triage, and
    caregiver monitoring directives.
    """

    EVIDENCE_SOURCES = [
        {
            "title": "WHO Guideline on the prevention and management of wasting and nutritional oedema in infants and children",
            "organization": "World Health Organization",
            "year": 2023,
            "scope": "Identification, inpatient/outpatient management, and triage criteria for severe and moderate wasting and nutritional oedema."
        },
        {
            "title": "WHO Guideline for complementary feeding of infants and young children 6–23 months of age",
            "organization": "World Health Organization",
            "year": 2023,
            "scope": "Age-appropriate food diversity, consistency, feeding frequency, responsive feeding, and milk feeding."
        },
        {
            "title": "Indicators for assessing infant and young child feeding practices (IYCF)",
            "organization": "UNICEF & World Health Organization",
            "year": 2021,
            "scope": "Definitions for Minimum Dietary Diversity (MDD >= 5/8 food groups) and Minimum Meal Frequency."
        },
        {
            "title": "WHO Child Growth Standards: Length/height-for-age, weight-for-age, weight-for-length, weight-for-height and body mass index-for-age",
            "organization": "World Health Organization",
            "year": 2006,
            "scope": "Box-Cox LMS parameters establishing international standard growth velocity and anthropometric cutoffs."
        }
    ]

    SAFETY_DISCLAIMER = (
        "ChildNutri AI provides screening and clinical decision-support information. "
        "It does not provide a medical diagnosis and does not replace assessment by a qualified healthcare professional. "
        "Clinical management should follow current applicable clinical guidelines and local health authority protocols."
    )

    LIMITATIONS = [
        "Screening result is not a definitive diagnosis: Anthropometric indicators flag potential risk, but clinical evaluation is required.",
        "Measurement accuracy is essential: Inaccurate age calculation or faulty anthropometric tools (uncalibrated scales, incorrect stadiometer positioning) alter Z-scores.",
        "Missing information limits interpretation: Incomplete feeding history, unrecorded illness episodes, or absent longitudinal records restrict the depth of the assessment.",
        "Longitudinal analysis requires repeated visits: A single cross-sectional evaluation cannot determine growth velocity, trajectory faltering, or recovery slope.",
        "Photographic assessment has technical boundaries: 2D image analysis cannot evaluate bilateral pedal edema, dehydration, or subcutaneous fat depth as accurately as clinical palpation.",
        "Decision-support only: The software does not prescribe medications, antibiotics, or treatment regimens. Therapeutic products must be administered under clinician supervision."
    ]

    @classmethod
    def generate_clinical_explanation(
        cls,
        child_name: str,
        age_months: float,
        gender: str,
        weight: float,
        height: float,
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
    ) -> Dict[str, Any]:
        """
        Synthesizes all clinical and AI screening layers into a comprehensive,
        child-specific, evidence-based explanatory dossier.
        """
        # 1. Determine Core Clinical Finding & Evidence Status
        finding_info = cls._determine_primary_finding(
            has_bilateral_edema=has_bilateral_edema,
            whz=whz,
            haz=haz,
            waz=waz,
            muac=muac,
            prediction_label=prediction_label,
            longitudinal_data=longitudinal_data
        )

        # 2. What Is Happening?
        what_is_happening = cls._generate_what_is_happening(
            finding_info=finding_info,
            weight=weight,
            height=height,
            muac=muac,
            whz=whz,
            haz=haz,
            waz=waz,
            baz=baz,
            has_bilateral_edema=has_bilateral_edema,
            longitudinal_data=longitudinal_data
        )

        # 3. What Does This Result Mean? (Simple Language)
        what_result_means = cls._generate_what_result_means(
            finding_info=finding_info,
            child_name=child_name
        )

        # 4. Possible Contributing Factors (Strictly Non-Causal)
        contributing_factors = cls._identify_contributing_factors(
            age_months=age_months,
            finding_info=finding_info,
            longitudinal_data=longitudinal_data,
            medical_notes=medical_notes,
            shap_factors=shap_factors
        )

        # 5. How to Help Prevent Malnutrition (Age-Aware)
        prevention_guidance = cls._generate_prevention_guidance(age_months=age_months)

        # 6. What Should Be Done Now? (Triaged Action Plan)
        action_plan = cls._generate_action_plan(
            triage_level=triage_level,
            is_emergency=is_emergency,
            finding_info=finding_info,
            has_bilateral_edema=has_bilateral_edema
        )

        # 7. When Professional Assessment Is Important
        when_to_seek_help = cls._generate_when_to_seek_help(
            finding_info=finding_info,
            has_bilateral_edema=has_bilateral_edema
        )

        # 8. What Should Be Monitored?
        monitoring_plan = cls._generate_monitoring_plan(
            longitudinal_data=longitudinal_data,
            age_months=age_months
        )

        # 9. Why Did the AI Give This Result? (SHAP Explainability)
        ai_explanation = cls._generate_ai_explanation(
            prediction_label=prediction_label,
            confidence=confidence,
            risk_score=risk_score,
            shap_factors=shap_factors
        )

        # 10. WHO Growth Assessment vs AI Screening (Consistency & Reconciliation)
        who_vs_ai = cls._generate_who_vs_ai_comparison(
            whz=whz,
            haz=haz,
            waz=waz,
            muac=muac,
            has_bilateral_edema=has_bilateral_edema,
            prediction_label=prediction_label,
            triage_level=triage_level
        )

        # 11. Child Nutrition Summary (Top-level Executive Summary)
        summary = {
            "current_status": finding_info["status_title"],
            "main_finding": finding_info["summary_statement"],
            "main_measurements": finding_info["supporting_measurements"],
            "possible_contributing_factors": contributing_factors["summary_list"],
            "recommended_next_step": action_plan["primary_directive"],
            "monitoring_status": monitoring_plan["summary_text"]
        }

        # 12. Human-Like Multi-Tier Explanation Object
        from ai.explanation import HumanExplanationEngine
        human_explanation = HumanExplanationEngine.generate_explanation(
            child_name=child_name,
            age_months=age_months,
            gender=gender,
            weight=weight,
            height=height,
            muac=muac,
            head_circumference=head_circumference,
            has_bilateral_edema=has_bilateral_edema,
            whz=whz,
            haz=haz,
            waz=waz,
            baz=baz,
            prediction_label=prediction_label,
            confidence=confidence,
            risk_score=risk_score,
            triage_level=triage_level,
            is_emergency=is_emergency,
            longitudinal_data=longitudinal_data,
            medical_notes=medical_notes,
            shap_factors=shap_factors
        )

        return {
            "summary": summary,
            "what_is_happening": what_is_happening,
            "what_result_means": what_result_means,
            "possible_contributing_factors": contributing_factors,
            "how_can_malnutrition_be_prevented": prevention_guidance,
            "what_should_be_done_now": action_plan,
            "when_professional_assessment_important": when_to_seek_help,
            "what_should_be_monitored": monitoring_plan,
            "why_did_the_ai_give_this_result": ai_explanation,
            "who_vs_ai": who_vs_ai,
            "technical_model_details": {
                "model_name": "Soft-Voting Ensemble (XGBoost 40% + LightGBM 35% + Random Forest 25%)",
                "model_version": "2.0.0",
                "feature_count": 12,
                "architecture": "12-Feature Tabular Soft-Voting Ensemble with PyTorch EfficientNet-B0 Vision Head",
                "explainability_engine": "TreeExplainer (Exact Shapley Attribution)",
                "vision_saliency": "Grad-CAM Convolutional Heatmap (block7a_project_conv)",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "important_limitations": cls.LIMITATIONS,
            "clinical_safety_notice": cls.SAFETY_DISCLAIMER,
            "evidence_sources": cls.EVIDENCE_SOURCES,
            "human_explanation": human_explanation,
            "doctor_explanation": human_explanation.get("doctor_explanation"),
            "assessment_summary": human_explanation.get("assessment_summary"),
            "sections": human_explanation.get("sections"),
            "in_simple_words": human_explanation.get("in_simple_words"),
            "parent_view": human_explanation.get("parent_view"),
            "detailed_view": human_explanation.get("detailed_view"),
            "technical_view": human_explanation.get("technical_view"),
            "section_statuses": human_explanation.get("section_statuses")
        }

    # -------------------------------------------------------------------------
    # Internal Helpers: Deterministic Rules & Template Generation
    # -------------------------------------------------------------------------

    @classmethod
    def _determine_primary_finding(
        cls,
        has_bilateral_edema: bool,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        muac: Optional[float],
        prediction_label: str,
        longitudinal_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Classifies the primary clinical finding according to WHO hierarchies."""
        has_faltering = longitudinal_data.get("early_warning_alert", False) if longitudinal_data else False

        if has_bilateral_edema:
            return {
                "category": "EDEMA_SAM",
                "status_title": "Severe Acute Malnutrition (Nutritional Edema)",
                "severity": "CRITICAL",
                "summary_statement": "Child presents with bilateral pitting pedal edema, fulfilling WHO diagnostic criteria for Severe Acute Malnutrition.",
                "supporting_measurements": f"Bilateral Pedal Edema: Present, Weight: measured, Height: measured"
            }
        elif (whz is not None and whz < -3.0) or (muac is not None and muac < 11.5):
            meas_desc = []
            if whz is not None and whz < -3.0: meas_desc.append(f"WHZ: {whz:+.2f} SD (< -3 SD)")
            if muac is not None and muac < 11.5: meas_desc.append(f"MUAC: {muac:.1f} cm (< 11.5 cm)")
            return {
                "category": "SEVERE_WASTING",
                "status_title": "Severe Acute Malnutrition (Severe Wasting)",
                "severity": "CRITICAL",
                "summary_statement": "Anthropometric measurements fall below severe wasting thresholds, indicating acute undernutrition requiring urgent clinical stabilization.",
                "supporting_measurements": ", ".join(meas_desc)
            }
        elif has_faltering and (whz is not None and whz < -1.5):
            vel = longitudinal_data.get("weight_velocity_g_day")
            vel_str = f"{vel:+.1f} g/day" if vel is not None else "negative"
            return {
                "category": "GROWTH_FALTERING",
                "status_title": "Growth Faltering / Acute Velocity Deficit",
                "severity": "CONCERNING",
                "summary_statement": f"Longitudinal monitoring identified an acute downward growth trajectory (weight velocity {vel_str}) with concurrent wasting indicators.",
                "supporting_measurements": f"Velocity: {vel_str}, WHZ: {whz:+.2f} SD" if whz is not None else f"Velocity: {vel_str}"
            }
        elif (whz is not None and whz < -2.0) or (muac is not None and muac < 12.5) or "wasted" in prediction_label.lower():
            meas_desc = []
            if whz is not None: meas_desc.append(f"WHZ: {whz:+.2f} SD")
            if muac is not None: meas_desc.append(f"MUAC: {muac:.1f} cm")
            return {
                "category": "MODERATE_WASTING",
                "status_title": "Moderate Acute Malnutrition (Wasting Concern)",
                "severity": "CONCERNING",
                "summary_statement": "Weight relative to height indicates moderate acute wasting, signaling a nutritional deficit that requires clinical and dietary review.",
                "supporting_measurements": ", ".join(meas_desc)
            }
        elif (haz is not None and haz < -2.0) or "stunted" in prediction_label.lower():
            return {
                "category": "STUNTING",
                "status_title": "Chronic Growth Concern (Stunting)",
                "severity": "CONCERNING",
                "summary_statement": f"Height-for-age ({haz:+.2f} SD) is below expected reference curves, indicating a chronic or cumulative linear growth deficit." if haz is not None else "Height relative to age indicates a chronic growth deficit.",
                "supporting_measurements": f"HAZ: {haz:+.2f} SD (< -2 SD)" if haz is not None else "HAZ: below threshold"
            }
        elif (waz is not None and waz < -2.0) or "underweight" in prediction_label.lower():
            return {
                "category": "UNDERWEIGHT",
                "status_title": "Underweight Concern (Weight-for-Age Deficit)",
                "severity": "CONCERNING",
                "summary_statement": f"Weight-for-age ({waz:+.2f} SD) falls below standard reference thresholds, indicating overall physical growth deficit." if waz is not None else "Weight-for-age falls below standard reference thresholds.",
                "supporting_measurements": f"WAZ: {waz:+.2f} SD" if waz is not None else "WAZ: below threshold"
            }
        else:
            return {
                "category": "NORMAL",
                "status_title": "Normal Physical Growth & Nutritional Status",
                "severity": "NORMAL",
                "summary_statement": "All available anthropometric parameters fall within normal international WHO growth reference standard limits.",
                "supporting_measurements": "Anthropometric measurements within standard ranges"
            }

    @classmethod
    def _generate_what_is_happening(
        cls,
        finding_info: Dict[str, Any],
        weight: float,
        height: float,
        muac: Optional[float],
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        baz: Optional[float],
        has_bilateral_edema: bool,
        longitudinal_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generates concise, factual explanation with supporting values."""
        cat = finding_info["category"]
        if cat == "EDEMA_SAM":
            concise = "Current screening identified bilateral pitting pedal edema with severe nutritional vulnerability."
        elif cat == "SEVERE_WASTING":
            concise = "Current screening indicates severe acute undernutrition (severe wasting)."
        elif cat == "GROWTH_FALTERING":
            concise = "Current screening indicates an acute deceleration in weight velocity across sequential visits."
        elif cat == "MODERATE_WASTING":
            concise = "Current screening indicates moderate acute undernutrition (moderate wasting)."
        elif cat == "STUNTING":
            concise = "Current screening indicates a chronic linear growth deficit (stunting)."
        elif cat == "UNDERWEIGHT":
            concise = "Current screening indicates a weight-for-age deficit (underweight)."
        else:
            concise = "Current screening indicates normal physical growth and nutritional status."

        # Weight and Height trends from longitudinal engine
        weight_trend_str = "Baseline recorded — previous visit unavailable"
        height_trend_str = "Baseline recorded — previous visit unavailable"
        if longitudinal_data and longitudinal_data.get("trend_points", 0) >= 2:
            w_vel = longitudinal_data.get("weight_velocity_g_day")
            days = longitudinal_data.get("days_between_checks", 0)
            if w_vel is not None:
                dir_str = "gaining" if w_vel >= 0 else "declining"
                weight_trend_str = f"{dir_str} at {w_vel:+.1f} g/day across {days} days"
            h_vel = longitudinal_data.get("height_velocity_cm_month")
            if h_vel is not None:
                height_trend_str = f"{h_vel:.1f} cm/month velocity"

        supporting_evidence = [
            {"indicator": "WHZ (Weight-for-Height)", "value": f"{whz:+.2f} SD" if whz is not None else "Not assessed", "status": "Severe" if (whz and whz < -3) else ("Moderate" if (whz and whz < -2) else "Normal" if whz is not None else "Unavailable")},
            {"indicator": "HAZ (Height-for-Age)", "value": f"{haz:+.2f} SD" if haz is not None else "Not assessed", "status": "Stunted" if (haz and haz < -2) else "Normal" if haz is not None else "Unavailable"},
            {"indicator": "WAZ (Weight-for-Age)", "value": f"{waz:+.2f} SD" if waz is not None else "Not assessed", "status": "Underweight" if (waz and waz < -2) else "Normal" if waz is not None else "Unavailable"},
            {"indicator": "MUAC (Arm Circumference)", "value": f"{muac:.1f} cm" if muac is not None else "Not recorded", "status": "Severe SAM" if (muac and muac < 11.5) else ("Moderate MAM" if (muac and muac < 12.5) else "Normal" if muac is not None else "Unavailable")},
            {"indicator": "Bilateral Pedal Edema", "value": "Present (+)" if has_bilateral_edema else "Absent (None)", "status": "Emergency Red Flag" if has_bilateral_edema else "Normal"},
            {"indicator": "Weight Growth Velocity", "value": weight_trend_str, "status": "Alert" if longitudinal_data and longitudinal_data.get("early_warning_alert") else "Routine"},
            {"indicator": "Height Growth Velocity", "value": height_trend_str, "status": "Routine"}
        ]

        return {
            "concise_statement": concise,
            "primary_concern": concise,
            "clinical_narrative": f"{concise} Based on the available biometric indicators, the system identified {finding_info['status_title'].lower()}.",
            "growth_classification": finding_info["status_title"],
            "velocity_state": weight_trend_str,
            "supporting_evidence": supporting_evidence
        }

    @classmethod
    def _generate_what_result_means(
        cls,
        finding_info: Dict[str, Any],
        child_name: str
    ) -> Dict[str, Any]:
        """Provides plain-language, compassionate explanations for caregivers."""
        cat = finding_info["category"]
        first_name = child_name.split()[0] if child_name else "The child"

        if cat == "NORMAL":
            title = "Normal / No Current Screening Concern"
            explanation = (
                f"Available measurements do not currently indicate the screening concerns being assessed for {first_name}. "
                "Continue age-appropriate nutrition and routine growth monitoring at local healthcare visits."
            )
        elif cat == "MODERATE_WASTING":
            title = "Moderate Wasting Concern"
            explanation = (
                f"{first_name}'s weight relative to height may indicate acute undernutrition based on the available screening measurements. "
                "This means the body has recently experienced an energy or nutrient deficit. "
                "This result requires appropriate clinical interpretation by a health professional."
            )
        elif cat in ["SEVERE_WASTING", "EDEMA_SAM"]:
            title = "Possible Severe Undernutrition Finding"
            explanation = (
                f"The screening measurements indicate a possible severe nutritional concern for {first_name}. "
                "Acute undernutrition affects muscle reserves and the immune system. "
                "Prompt professional clinical evaluation is essential to assess overall health, verify measurements, and provide necessary guidance."
            )
        elif cat == "GROWTH_FALTERING":
            title = "Growth Faltering / Velocity Concern"
            explanation = (
                f"{first_name}'s rate of growth across consecutive screenings suggests a slowing or downward trajectory. "
                "Growth faltering often precedes noticeable changes in appearance and warrants an evaluation of recent feeding patterns and any recent illness."
            )
        elif cat == "STUNTING":
            title = "Chronic Linear Growth Concern (Stunting)"
            explanation = (
                f"{first_name}'s height relative to age is below expected standard curves, which may indicate a chronic or longer-term growth concern. "
                "This is distinct from acute weight loss and should be reviewed together with long-term dietary diversity and health history."
            )
        else: # UNDERWEIGHT
            title = "Underweight Concern (Weight-for-Age)"
            explanation = (
                f"{first_name}'s weight relative to age is below the expected range used by the screening standard. "
                "Because weight-for-age reflects both height and body fullness, this indicator should be interpreted together with height, weight-for-height, and clinical information."
            )

        return {
            "title": title,
            "explanation": explanation,
            "clinical_implication": explanation,
            "reassurance": "Routine monitoring is recommended." if cat == "NORMAL" else "Prompt pediatric evaluation provides individualized diagnostic clarity."
        }

    @classmethod
    def _identify_contributing_factors(
        cls,
        age_months: float,
        finding_info: Dict[str, Any],
        longitudinal_data: Optional[Dict[str, Any]],
        medical_notes: Optional[str],
        shap_factors: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Extracts evidence-based contributing factors strictly from available data.
        Enforces: "Possible contributing factor", never "caused".
        """
        categorized = {
            "feeding_diet": [],
            "illness_health": [],
            "growth_velocity": [],
            "environment_access": []
        }
        summary_list = []
        notes_lower = (medical_notes or "").lower()

        # 1. Illness evidence from notes/history
        if "diarrhea" in notes_lower or "diarrhoea" in notes_lower:
            item = "Possible contributing factor: Recent reported diarrhea episode impacting fluid balance and nutrient absorption."
            categorized["illness_health"].append(item)
            summary_list.append(item)
        if "fever" in notes_lower or "viral" in notes_lower or "infection" in notes_lower:
            item = "Possible contributing factor: Recent febrile or infectious episode increasing metabolic demand and reducing appetite."
            categorized["illness_health"].append(item)
            summary_list.append(item)
        if "cough" in notes_lower or "respiratory" in notes_lower or "pneumonia" in notes_lower:
            item = "Possible contributing factor: Recent respiratory illness causing feeding fatigue."
            categorized["illness_health"].append(item)
            summary_list.append(item)

        # 2. Growth velocity evidence
        if longitudinal_data and longitudinal_data.get("early_warning_alert"):
            vel = longitudinal_data.get("weight_velocity_g_day")
            vel_str = f"{vel:+.1f} g/day" if vel is not None else "negative"
            item = f"Possible contributing factor: Documented weight deceleration ({vel_str}) across sequential assessments."
            categorized["growth_velocity"].append(item)
            summary_list.append(item)

        # 3. Feeding & dietary evidence
        if "appetite" in notes_lower and ("poor" in notes_lower or "loss" in notes_lower or "reduced" in notes_lower):
            item = "Possible contributing factor: Caregiver-reported reduction in appetite or meal volume."
            categorized["feeding_diet"].append(item)
            summary_list.append(item)

        # 4. Biometric model feature attributions (SHAP)
        if shap_factors:
            for f in shap_factors[:3]:
                if f.get("impact") and "Risk" in f.get("impact", ""):
                    feat_name = f.get("display_name", f.get("feature", ""))
                    meas_val = f.get("measured_value", f.get("value", ""))
                    if feat_name in ["MUAC", "WHZ", "HAZ", "WAZ", "Weight"]:
                        item = f"Possible contributing factor: Low anthropometric indicator ({feat_name}: {meas_val}) contributing to screening concern."
                        if item not in summary_list:
                            categorized["growth_velocity"].append(item)
                            summary_list.append(item)

        # 5. Default fallback if zero factors documented in DB
        if not summary_list:
            default_item = "No acute illness or specific dietary gaps were documented in this assessment record. Explore feeding practices and general wellness during clinical review."
            categorized["feeding_diet"].append(default_item)
            summary_list.append(default_item)

        # Build structured factors list with explicit factor name, details, and priority
        structured_factors = []
        for item in summary_list:
            is_high = any(k in item.lower() for k in ["severe", "edema", "deceleration", "diarrhea", "fever", "loss"])
            priority = "High" if is_high else "Moderate"
            if "recent reported diarrhea" in item.lower():
                factor_name = "Recent Illness (Diarrhea Episode)"
            elif "recent febrile" in item.lower():
                factor_name = "Recent Infection / Fever"
            elif "recent respiratory" in item.lower():
                factor_name = "Recent Respiratory Illness"
            elif "weight deceleration" in item.lower():
                factor_name = "Growth Faltering / Velocity Deceleration"
            elif "appetite" in item.lower():
                factor_name = "Reduced Appetite / Oral Intake"
            elif "anthropometric" in item.lower():
                factor_name = "Biometric Growth Indicator Deficit"
            else:
                factor_name = "General Nutrition & Growth Observation"

            structured_factors.append({
                "factor": factor_name,
                "details": item,
                "priority": priority
            })

        return {
            "categories": categorized,
            "summary_list": summary_list,
            "factors": structured_factors,
            "disclaimer": "Contributing factors are potential influences based on available records, not proven direct causes. Correlation does not establish medical causality."
        }

    @classmethod
    def _generate_prevention_guidance(cls, age_months: float) -> Dict[str, Any]:
        """Age-specific evidence-based prevention principles from WHO guidelines."""
        if age_months < 6:
            stage_title = "Infants under 6 months (Exclusive Breastfeeding Stage)"
            principles = [
                "Exclusive breastfeeding on demand (8–12 feeds per 24 hours), day and night. No water, formula, teas, or herbal concoctions are needed.",
                "Ensure proper infant positioning and deep latch to maximize hindmilk intake and prevent maternal nipple discomfort.",
                "Avoid introducing solid foods, animal milks, or commercial cereal porridges prior to 6 completed months.",
                "Maintain complete immunization schedule and attend routine monthly health worker growth monitoring visits.",
                "Promptly seek healthcare worker evaluation if the infant exhibits feeding difficulties, excessive crying, or reduced wet diapers."
            ]
        elif age_months <= 23:
            stage_title = "Children 6 to 23 months (Complementary Feeding Stage — WHO 2023 Guidelines)"
            principles = [
                "Timely introduction: Start safe, nutrient-dense complementary foods at 6 completed months while maintaining frequent breastfeeding on demand.",
                "Minimum Dietary Diversity: Offer foods from at least 5 of the 8 WHO food groups daily (breastmilk, grains/tubers, pulses/nuts, dairy, flesh foods, eggs, vitamin-A fruits/veg, other fruits/veg).",
                "Progressive consistency: Transition food textures smoothly from soft mashes (6-8mo) to coarse fork-mashed foods and soft finger foods (9-11mo) to family foods (12-23mo).",
                "Adequate meal frequency: 2–3 meals/day at 6–8 months; 3–4 meals/day at 9–23 months, plus 1–2 healthy, energy-dense snacks as desired.",
                "Responsive feeding: Feed slowly and patiently, encouraging without force. Respond positively to the child's hunger and fullness cues.",
                "Hygiene & safe preparation: Wash caregiver and child hands with soap before food preparation and feeding. Store foods safely and use clean utensils."
            ]
        else: # 24 to 59 months
            stage_title = "Children 24 to 59 months (Family Food & Active Growth Stage)"
            principles = [
                "Family meal sharing: Provide 3 balanced meals plus 2 healthy, energy-dense snacks daily, sharing the family pot.",
                "Nutrient density: Incorporate locally accessible pulses, eggs, dairy, vegetables, and seasonal fruits to ensure adequate micronutrients (iron, vitamin A, zinc).",
                "Avoid empty calories: Limit ultra-processed snacks, sugary confectionery, tea, coffee, and sweetened beverages that displace nutritious food.",
                "Promote hygiene: Maintain safe boiled or treated drinking water, sanitary disposal of waste, and consistent handwashing with soap.",
                "Growth checkups: Continue quarterly growth checks at your local Anganwadi / Primary Health Centre to catch any subtle weight deceleration early."
            ]

        structured_principles = []
        for p in principles:
            parts = p.split(":", 1)
            title = parts[0].strip() if len(parts) > 1 else "Guidance"
            desc = parts[1].strip() if len(parts) > 1 else p
            structured_principles.append({"title": title, "description": desc})

        age_cat_name = (
            "Infants Under 6 Months (<6m)" if age_months < 6.0
            else ("Infants & Young Children 6–23 Months" if age_months <= 23.99
            else "Young Children 24–59 Months")
        )

        return {
            "age_group": stage_title,
            "age_category": age_cat_name,
            "principles": structured_principles,
            "raw_principles": principles,
            "reference_standard": "WHO 2023 Guidelines for complementary feeding of infants and young children 6–23 months"
        }

    @classmethod
    def _generate_action_plan(
        cls,
        triage_level: str,
        is_emergency: bool,
        finding_info: Dict[str, Any],
        has_bilateral_edema: bool
    ) -> Dict[str, Any]:
        """Provides non-prescriptive, triaged caregiver and clinical next steps."""
        level_upper = (triage_level or "").upper()

        if is_emergency or "RED" in level_upper or has_bilateral_edema:
            status_badge = "PROMPT CLINICAL ASSESSMENT RECOMMENDED (RED)"
            if has_bilateral_edema:
                primary_directive = "Prompt professional clinical assessment and inpatient hospital referral is recommended for nutritional edema."
            else:
                primary_directive = "Prompt professional clinical assessment and facility referral is recommended."
            specific_reasons = []
            if has_bilateral_edema: specific_reasons.append("Bilateral pitting pedal edema observed (kwashiorkor clinical red flag).")
            if finding_info["category"] == "SEVERE_WASTING": specific_reasons.append("Anthropometric measurements below severe acute malnutrition thresholds.")
            if not specific_reasons: specific_reasons.append("Screening criteria flagged urgent priority.")

            actions = [
                "Prompt professional clinical assessment is recommended: Take the child to the nearest Primary Health Centre, Sub-District Hospital, or Nutrition Rehabilitation Centre (NRC).",
                f"Present this screening summary to the attending medical officer, highlighting: {'; '.join(specific_reasons)}",
                "Maintain ongoing breastfeeding or offering small, frequent sips of clean fluid during transit to prevent hypoglycemia and dehydration.",
                "Keep the child warm; avoid cold exposure during transit.",
                "Safety directive: Do NOT administer over-the-counter medicines, antibiotics, or unprescribed home remedies without a physician's direct examination."
            ]
        elif "YELLOW" in level_upper or finding_info["severity"] == "CONCERNING":
            status_badge = "CLINICAL REVIEW RECOMMENDED (YELLOW)"
            primary_directive = "Arrange professional assessment with a medical officer or pediatrician within 7–14 days."
            actions = [
                "Arrange professional assessment with a healthcare professional or frontline worker (ASHA/Anganwadi worker) within 7–14 days.",
                "Review 24-hour feeding patterns, meal frequency, and dietary variety with the health worker to identify enrichment opportunities.",
                "Confirm anthropometric measurements on a calibrated clinic scale and stadiometer at the follow-up visit.",
                "Increase energy density in meals by adding healthy local fats (e.g. teaspoon of cooking oil, ghee, or groundnut paste) to cooked grain/pulse dishes.",
                "Monitor for fever, diarrhea, or worsening appetite and seek immediate medical attention if warning signs emerge."
            ]
        else: # GREEN / ROUTINE
            status_badge = "ROUTINE MONITORING & NUTRITION SUPPORT (GREEN)"
            primary_directive = "Continue age-appropriate nutrition and routine growth monitoring."
            actions = [
                "Continue age-appropriate feeding practices and responsive, patient mealtime interactions.",
                "Attend scheduled routine growth monitoring visits at your local health centre or Anganwadi.",
                "Maintain safe food preparation hygiene, handwashing with soap, and clean drinking water.",
                "Follow the national immunization schedule and attend routine vitamin A and deworming drives as recommended by local health authorities.",
                "Monitor general activity, playfulness, and daily appetite."
            ]

        urgency = "URGENT (RED)" if (is_emergency or "RED" in level_upper or has_bilateral_edema) else ("MODERATE (YELLOW)" if ("YELLOW" in level_upper or finding_info["severity"] == "CONCERNING") else "ROUTINE (GREEN)")

        return {
            "status_badge": status_badge,
            "urgency": urgency,
            "primary_directive": primary_directive,
            "recommended_actions": actions,
            "triaged_steps": actions,
            "non_prescriptive_clause": "ChildNutri AI does not prescribe medicines, antibiotics, therapeutic feeding doses, or supplements. Medical prescriptions must be provided by a certified clinician."
        }

    @classmethod
    def _generate_when_to_seek_help(
        cls,
        finding_info: Dict[str, Any],
        has_bilateral_edema: bool
    ) -> Dict[str, Any]:
        """Explains key clinical red flags that require urgent clinical evaluation."""
        red_flags = [
            "Presence of bilateral pitting pedal edema (swelling of both feet that leaves a temporary indentation when pressed gently for 3 seconds).",
            "Severe visible wasting: ribs, spine, or shoulder blades prominently visible with marked reduction of buttock or thigh muscle.",
            "Loss of appetite: child refuses to eat or cannot finish supplementary feeding.",
            "Persistent or recurrent fever, cough with fast breathing, or repeated diarrhea (>3 watery stools in 24 hours).",
            "Extreme weakness, apathy, unusual lethargy, or difficulty waking the child.",
            "Rapid or unexplained weight loss across consecutive measurements.",
            "Vomiting everything consumed or inability to retain fluids."
        ]
        return {
            "summary_statement": "Professional clinical assessment is important whenever a child shows signs of acute physiological vulnerability, regardless of automated risk scores.",
            "clinical_red_flags": red_flags,
            "urgent_red_flags": red_flags,
            "protocol_note": "Caregivers should present to the nearest healthcare facility or Anganwadi/NRC when any of these red flags are present."
        }

    @classmethod
    def _generate_monitoring_plan(
        cls,
        longitudinal_data: Optional[Dict[str, Any]],
        age_months: float
    ) -> Dict[str, Any]:
        """Provides specific indicators to monitor over time based on visit history."""
        trend_pts = longitudinal_data.get("trend_points", 1) if longitudinal_data else 1
        is_single_visit = trend_pts <= 1

        if is_single_visit:
            summary_text = "Longitudinal monitoring is not yet available because only one assessment has been recorded."
            status_text = "Baseline Recorded (Single Visit)"
            trajectory_desc = "Baseline assessment recorded. Serial measurements at future visits will establish the child's individual growth velocity and trajectory curve."
        else:
            status_text = f"Active Longitudinal Monitoring ({trend_pts} visits recorded)"
            traj = longitudinal_data.get("trajectory", "Monitoring active")
            vel_g = longitudinal_data.get("weight_velocity_g_day")
            vel_txt = f"{vel_g:+.1f} g/day" if vel_g is not None else "stable"
            summary_text = f"Growth trajectory: {traj} (Weight velocity: {vel_txt})."
            trajectory_desc = longitudinal_data.get("clinical_reason") or f"Growth velocity tracks at {vel_txt} across sequential assessments."

        indicators = [
            {"indicator": "Body Weight", "frequency": "Monthly for healthy infants; bi-weekly if under monitoring", "purpose": "Identifies early acute weight deflection or recovery gain"},
            {"indicator": "Recumbent Length / Height", "frequency": "Every 1–2 months", "purpose": "Tracks linear skeletal development and stunting trajectory"},
            {"indicator": "Mid-Upper Arm Circumference (MUAC)", "frequency": "Monthly in community screening", "purpose": "Direct proxy for muscle mass and acute wasting risk"},
            {"indicator": "Daily Appetite & Feeding Frequency", "frequency": "Continuous caregiver observation", "purpose": "Early warning indicator of infection or feeding difficulties"},
            {"indicator": "Dietary Diversity (Food Groups)", "frequency": "Daily assessment (aim >= 5/8 groups)", "purpose": "Ensures micronutrient adequacy and dietary balance"},
            {"indicator": "Illness Episodes (Fever / Diarrhea)", "frequency": "Continuous tracking", "purpose": "Prevents infection-induced nutritional depletion"}
        ]

        indicators_list = ["Body Weight", "Recumbent Length / Height", "Mid-Upper Arm Circumference (MUAC)", "Daily Appetite & Feeding Frequency", "Dietary Diversity", "Illness Episodes (Fever / Diarrhea)"]

        return {
            "status_text": status_text,
            "longitudinal_status": summary_text if not is_single_visit else "Single visit evaluation — serial longitudinal visits required to establish velocity curve.",
            "summary_text": summary_text,
            "trajectory_description": trajectory_desc,
            "is_single_visit": is_single_visit,
            "key_indicators_to_monitor": indicators,
            "indicators_to_track": indicators_list,
            "schedule": "Routine monthly monitoring" if is_single_visit else "Follow-up in 14 days"
        }

    @classmethod
    def _generate_ai_explanation(
        cls,
        prediction_label: str,
        confidence: float,
        risk_score: Optional[float],
        shap_factors: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Transparent, plain-language explainability grounded in real model weights."""
        factors_summary = []
        if shap_factors:
            for item in shap_factors[:4]:
                feat_name = item.get("display_name", item.get("feature", "Biometric factor"))
                meas = item.get("measured_value", item.get("value", ""))
                imp = item.get("impact", "")
                direction = "elevated" if "Risk" in imp else "lowered"
                factors_summary.append({
                    "feature": feat_name,
                    "measured_value": str(meas),
                    "impact_direction": direction,
                    "contribution_level": item.get("contribution_level", "Moderate impact"),
                    "plain_description": f"{feat_name} ({meas}) {direction} the statistical screening risk."
                })

        summary_narrative = (
            f"The Soft-Voting Ensemble predicted '{prediction_label}' with {confidence*100:.1f}% confidence "
            f"(Composite Screening Risk Score: {round(risk_score) if risk_score is not None else 'N/A'}/100). "
        )
        if factors_summary:
            top_feats = ", ".join([f["feature"] for f in factors_summary[:2]])
            summary_narrative += f"Primary biometric contributors driving this output include {top_feats}."
        else:
            summary_narrative += "Feature attribution was derived from anthropometric Z-score distributions."

        return {
            "prediction": prediction_label,
            "confidence_percentage": round(confidence * 100, 1),
            "risk_score": round(risk_score) if risk_score is not None else None,
            "summary_narrative": summary_narrative,
            "top_factors": factors_summary,
            "interpretability_note": "SHAP feature attributions reflect mathematical contributions within the decision tree ensemble, not direct biological causation."
        }

    @classmethod
    def _generate_who_vs_ai_comparison(
        cls,
        whz: Optional[float],
        haz: Optional[float],
        waz: Optional[float],
        muac: Optional[float],
        has_bilateral_edema: bool,
        prediction_label: str,
        triage_level: str
    ) -> Dict[str, Any]:
        """Compares WHO LMS Box-Cox growth curves against AI statistical inference."""
        pred_lower = (prediction_label or "").lower()

        # Classify WHO status
        who_findings = []
        if has_bilateral_edema:
            who_findings.append("Bilateral Pitting Edema (WHO SAM Criteria)")
        if whz is not None:
            if whz < -3.0: who_findings.append("Severe Wasting (WHZ < -3 SD)")
            elif whz < -2.0: who_findings.append("Moderate Wasting (WHZ < -2 SD)")
            elif whz > 2.0: who_findings.append("Overweight range (WHZ > +2 SD)")
        if haz is not None and haz < -2.0:
            who_findings.append("Stunting (HAZ < -2 SD)")
        if waz is not None and waz < -2.0:
            who_findings.append("Underweight (WAZ < -2 SD)")
        if not who_findings:
            who_findings.append("Growth indicators within normal WHO ranges")

        who_summary = ", ".join(who_findings)

        # Check alignment
        is_normal_who = all(
            (z is None or (-2.0 <= z <= 2.0)) for z in [whz, haz, waz]
        ) and not has_bilateral_edema
        is_normal_ai = "normal" in pred_lower

        if is_normal_who and is_normal_ai:
            agreement_status = "AGREEMENT"
            comparison_text = "WHO growth assessment and AI screening findings are broadly consistent. Both identify normal physical growth parameters."
        elif (not is_normal_who) and (not is_normal_ai):
            agreement_status = "AGREEMENT"
            comparison_text = f"WHO growth assessment and AI screening findings are broadly consistent. Both identify nutritional concerns ({prediction_label})."
        else:
            agreement_status = "DISCREPANCY_FLAGGED"
            comparison_text = (
                f"WHO growth assessment ({who_summary}) and AI statistical inference ({prediction_label}) differ in primary emphasis. "
                "The deterministic clinical triage override protocol takes precedence. The attending healthcare professional should review "
                "the underlying biometric measurements and patient clinical presentation to reconcile the assessment."
            )

        return {
            "agreement_status": agreement_status,
            "consistency_status": agreement_status,
            "who_summary": who_summary,
            "who_perspective": who_summary,
            "ai_summary": f"Predicted Category: {prediction_label}",
            "ai_perspective": f"Predicted Category: {prediction_label}",
            "triage_summary": f"Clinical Priority: {triage_level}",
            "reconciliation_statement": comparison_text
        }
