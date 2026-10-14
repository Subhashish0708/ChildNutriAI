"""
=============================================================================
India Pediatric Growth Standard Router & Canonical Assessment Service
=============================================================================
Mandate:
  Single authoritative source of truth for pediatric growth reference selection
  in India:
    • Age < 5 years (0 to 59.9 months):
        -> WHO Child Growth Standards (2006 MGRS) adopted for under-5 in India.
        -> Guideline: "Growth reference: WHO Child Growth Standards — adopted for under-5 assessment in India"
        -> Indicators: WAZ, HAZ, WHZ, BAZ (with honest availability flagging).
    • Age 5 to 18 years (60.0 to 216.0 months):
        -> Indian Academy of Pediatrics (IAP) 2015 Growth Charts.
        -> Guideline: "Growth reference: IAP 2015 Growth Charts — Indian children 5–18 years"
        -> Indicators: Height-for-age, Weight-for-age, BMI-for-age with Indian
           adult-equivalent cut-offs (23 kg/m² overweight, 27 kg/m² obesity).

Strict Rules:
  1. DO NOT mix WHO Z-scores with IAP cutoffs.
  2. Every calculated value carries complete metadata (indicator, reference_system, version, age_group, unit).
  3. Age boundaries are strictly enforced (months, exact calculation from DOB).
  4. MUAC is age-aware: Standard 11.5/12.5 cm cutoffs apply ONLY to 6–59 months;
     explicitly flagged as not calibrated for 5–18 years under IAP 2015.
  5. Zero fake defaults: Missing values map to explicit states:
     NOT_RECORDED, NOT_AVAILABLE, NOT_ASSESSED, UNABLE_TO_CALCULATE, REFERENCE_DATA_UNAVAILABLE.
=============================================================================
"""

import logging
from typing import Dict, Any, Optional, Tuple, Union
from datetime import date, datetime

from ai.clinical_algorithms.who_lms import WHOLMSEngine
from ai.clinical_algorithms.iap_growth import IAPGrowthEngine

logger = logging.getLogger("childnutri.growth_standard_router")


class IndianGrowthStandardRouter:
    """
    Canonical router determining the correct pediatric growth standard for Indian children.
    """

    SYSTEM_WHO = "WHO"
    VERSION_WHO = "WHO-2006"
    SYSTEM_IAP = "IAP"
    VERSION_IAP = "IAP-2015"

    AGE_CUTOFF_MONTHS = 60.0  # Exactly 5 years (0 to 59.9 months -> WHO; 60.0 to 216.0 -> IAP)
    MAX_AGE_MONTHS = 216.0    # 18.0 years

    @classmethod
    def get_reference_metadata(cls, age_months: float) -> Dict[str, Any]:
        """
        Determines the official growth reference metadata for a given age in months.
        """
        if age_months is None or age_months < 0:
            return {
                "system": "UNKNOWN",
                "version": "UNKNOWN",
                "age_group": "invalid",
                "guideline_title": "Invalid age specification",
                "is_valid": False,
                "error": "Age cannot be negative or None."
            }

        if age_months < cls.AGE_CUTOFF_MONTHS:
            return {
                "system": cls.SYSTEM_WHO,
                "version": cls.VERSION_WHO,
                "age_group": "under_5",
                "guideline_title": "Growth reference: WHO Child Growth Standards — adopted for under-5 assessment in India",
                "target_population": "Children below 5 years in India (0–59 months)",
                "academic_citation": "WHO Child Growth Standards (2006) Multicentre Growth Reference Study",
                "calculation_version": "2.0-IN",
                "is_valid": True
            }
        elif age_months <= cls.MAX_AGE_MONTHS:
            return {
                "system": cls.SYSTEM_IAP,
                "version": cls.VERSION_IAP,
                "age_group": "5_to_18",
                "guideline_title": "Growth reference: IAP 2015 Growth Charts — Indian children 5–18 years",
                "target_population": "Indian children and adolescents (5–18 years / 60–216 months)",
                "academic_citation": "Khadilkar V, et al. Revised IAP Growth Charts. Indian Pediatr. 2015;52:47–55",
                "calculation_version": "2.0-IN",
                "is_valid": True
            }
        else:
            return {
                "system": "ADULT",
                "version": "NOT_PEDIATRIC",
                "age_group": "above_18",
                "guideline_title": "Age exceeds pediatric screening scope (>18 years)",
                "is_valid": False,
                "error": f"Age ({age_months:.1f} months / {age_months/12.0:.1f} years) exceeds pediatric upper limit of 18 years."
            }

    @classmethod
    def validate_anthropometric_inputs(
        cls,
        age_months: float,
        gender: Union[str, int, float, bool],
        weight: float,
        height: float,
        muac: Optional[float] = None,
        head_circumference: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Age-aware validation of physiological boundaries for Indian pediatric screening (0-18 years).
        """
        # 1. Gender check
        try:
            IAPGrowthEngine.normalize_gender(gender)
        except ValueError as e:
            return False, str(e)

        # 2. Age check
        if age_months is None or not isinstance(age_months, (int, float)):
            return False, "Age in months is required and must be numeric."
        if age_months < 0.0:
            return False, f"Age cannot be negative ({age_months} months provided)."
        if age_months > cls.MAX_AGE_MONTHS:
            return False, f"Age ({age_months:.1f} months / {age_months/12.0:.1f} years) exceeds pediatric screening range (max 18 years / 216 months)."

        # 3. Weight check
        if weight is None or not isinstance(weight, (int, float)):
            return False, "Weight in kg is required and must be numeric."
        if weight <= 0.0:
            return False, f"Weight must be greater than zero ({weight} kg provided)."

        # 4. Height check
        if height is None or not isinstance(height, (int, float)):
            return False, "Height/length in cm is required and must be numeric."
        if height <= 0.0:
            return False, f"Height must be greater than zero ({height} cm provided)."

        # Age-stratified physical bounds
        if age_months < cls.AGE_CUTOFF_MONTHS:
            # Under 5 boundaries
            if weight > 35.0:
                return False, f"Weight ({weight} kg) exceeds plausible under-5 screening range (max 35 kg)."
            if height < 35.0 or height > 130.0:
                return False, f"Height ({height} cm) is outside plausible under-5 screening range (35–130 cm)."
        else:
            # 5 to 18 boundaries
            if weight > 120.0:
                return False, f"Weight ({weight} kg) exceeds plausible pediatric screening range (max 120 kg)."
            if height < 75.0 or height > 210.0:
                return False, f"Height ({height} cm) is outside plausible pediatric screening range (75–210 cm)."

        # 5. MUAC check
        if muac is not None:
            if not isinstance(muac, (int, float)) or muac <= 0.0:
                return False, f"MUAC must be a positive number ({muac} provided)."
            if muac < 5.0 or muac > 45.0:
                return False, f"MUAC ({muac} cm) is outside plausible pediatric range (5–45 cm)."

        # 6. Head Circumference check
        if head_circumference is not None:
            if not isinstance(head_circumference, (int, float)) or head_circumference <= 0.0:
                return False, f"Head circumference must be a positive number ({head_circumference} provided)."
            if head_circumference < 20.0 or head_circumference > 65.0:
                return False, f"Head circumference ({head_circumference} cm) is outside plausible pediatric range (20–65 cm)."

        return True, None


class GrowthAssessmentService:
    """
    Authoritative pediatric growth assessment service executing the routed growth evaluation.
    Single point of truth consumed across backend, frontend, PDF, and explanation layers.
    """

    @classmethod
    def assess_growth(
        cls,
        age_months: float,
        gender: Union[str, int, float, bool],
        weight: float,
        height: float,
        muac: Optional[float] = None,
        head_circumference: Optional[float] = None,
        has_bilateral_edema: bool = False,
        gestational_age_weeks: Optional[float] = None,
        birth_weight_g: Optional[float] = None,
        predicted_anthropometrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes routed growth assessment adhering to age-appropriate Indian guidelines.
        Supports gestational-age aware neonatal evaluation and strict separation of
        physically measured vs AI-predicted anthropometric attributes.
        """
        # Validate inputs
        is_valid, err_msg = IndianGrowthStandardRouter.validate_anthropometric_inputs(
            age_months=age_months,
            gender=gender,
            weight=weight,
            height=height,
            muac=muac,
            head_circumference=head_circumference
        )
        if not is_valid:
            raise ValueError(f"Growth assessment validation failed: {err_msg}")

        ref_meta = IndianGrowthStandardRouter.get_reference_metadata(age_months)
        norm_gender = IAPGrowthEngine.normalize_gender(gender)
        bmi = round(float(weight) / ((float(height) / 100.0) ** 2), 2) if (weight and height and height > 0) else None

        # Build base canonical result
        result: Dict[str, Any] = {
            "reference_standard": ref_meta,
            "age_months": round(float(age_months), 1),
            "age_years": round(float(age_months) / 12.0, 2),
            "gender": norm_gender,
            "anthropometry": {
                "weight_kg": round(float(weight), 2) if weight is not None else None,
                "height_cm": round(float(height), 1) if height is not None else None,
                "muac_cm": round(float(muac), 1) if muac is not None else None,
                "head_circumference_cm": round(float(head_circumference), 1) if head_circumference is not None else None,
                "bmi": bmi,
                "has_bilateral_edema": bool(has_bilateral_edema)
            },
            "growth_indices": {},
            "nutrition_screening": {},
            "muac_evaluation": {},
            "primary_concern": "No current screening concern",
            "clinical_status": "NORMAL"
        }

        # Neonatal Assessment (0-28 days or whenever gestational age is recorded)
        is_neonate = bool(age_months <= 1.0 or gestational_age_weeks is not None)
        if is_neonate:
            eff_weight_g = float(birth_weight_g) if birth_weight_g is not None else (float(weight) * 1000.0 if weight is not None else None)
            if gestational_age_weeks is not None:
                ga = float(gestational_age_weeks)
                is_preterm = ga < 37.0
                if ga < 28.0:
                    ga_cat, ga_label = "EXTREMELY_PRETERM", "Extremely Preterm (< 28 weeks)"
                elif ga < 32.0:
                    ga_cat, ga_label = "VERY_PRETERM", "Very Preterm (28 to < 32 weeks)"
                elif ga < 37.0:
                    ga_cat, ga_label = "MODERATE_LATE_PRETERM", "Moderate to Late Preterm (32 to < 37 weeks)"
                else:
                    ga_cat, ga_label = "TERM", "Full Term (≥ 37 weeks)"
            else:
                ga, is_preterm = None, None
                ga_cat, ga_label = "NOT_RECORDED", "Gestational age not recorded"

            if eff_weight_g is not None:
                if eff_weight_g < 1000.0:
                    bw_cat, bw_label, triage_pri = "ELBW", "Extremely Low Birth Weight (< 1000g)", "URGENT_NICU_REFERRAL"
                elif eff_weight_g < 1500.0:
                    bw_cat, bw_label, triage_pri = "VLBW", "Very Low Birth Weight (1000–1499g)", "SNCU_NICU_ADMISSION"
                elif eff_weight_g < 2500.0:
                    bw_cat, bw_label, triage_pri = "LBW", "Low Birth Weight (1500–2499g)", "KANGAROO_MOTHER_CARE_AND_FEEDING_SUPPORT"
                elif eff_weight_g <= 4000.0:
                    bw_cat, bw_label, triage_pri = "NORMAL", "Normal Birth Weight (2500–4000g)", "ROUTINE_ESSENTIAL_NEWBORN_CARE"
                else:
                    bw_cat, bw_label, triage_pri = "MACROSOMIA", "High Birth Weight / Macrosomia (> 4000g)", "MATERNAL_DIABETES_SCREENING"
            else:
                bw_cat, bw_label, triage_pri = "NOT_RECORDED", "Birth weight not recorded", "ROUTINE_MONITORING"

            weeks_preterm = round(40.0 - ga, 1) if (ga is not None and is_preterm) else 0.0
            corrected_age_m = round(float(age_months) - (weeks_preterm * (7.0 / 30.4375)), 2) if is_preterm else round(float(age_months), 2)

            if is_preterm:
                if corrected_age_m < 0:
                    guidance = (
                        "Preterm infant (< 37 weeks GA). Corrected age should be applied before interpreting post-term growth. "
                        f"Chronological age is prior to 40 weeks conceptional term (corrected age: {corrected_age_m:+.2f}m). "
                        "Standard post-term WHO references are not calibrated for post-conceptional growth; specialized preterm monitoring and NICU feeding protocols apply."
                    )
                else:
                    guidance = (
                        "Preterm infant (< 37 weeks GA). Corrected age should be applied before interpreting post-term growth "
                        f"(corrected age: {corrected_age_m:.2f} months vs chronological age: {age_months:.1f} months)."
                    )
            elif is_preterm is False:
                guidance = "Full term infant. Evaluate using WHO 2006 neonatal/infant reference standards."
            else:
                guidance = "Gestational age not recorded; standard postnatal age applied."

            result["neonatal_assessment"] = {
                "is_neonate": True,
                "gestational_age_weeks": ga,
                "gestational_category": ga_cat,
                "gestational_label": ga_label,
                "is_preterm": is_preterm,
                "weeks_preterm": weeks_preterm,
                "corrected_age_months": corrected_age_m,
                "birth_weight_g": eff_weight_g,
                "birth_weight_category": bw_cat,
                "birth_weight_label": bw_label,
                "neonatal_triage_action": triage_pri,
                "clinical_guidance": guidance
            }

        # Track measured vs predicted anthropometry
        result["measured_anthropometry"] = dict(result["anthropometry"])
        if predicted_anthropometrics:
            result["predicted_anthropometry"] = {
                "predicted_weight_g": predicted_anthropometrics.get("predicted_weight_g"),
                "predicted_body_length_cm": predicted_anthropometrics.get("predicted_body_length_cm"),
                "predicted_head_circumference_cm": predicted_anthropometrics.get("predicted_head_circumference_cm"),
                "predicted_chest_girth_cm": predicted_anthropometrics.get("predicted_chest_girth_cm"),
                "predicted_birth_weight_category": predicted_anthropometrics.get("predicted_birth_weight_category"),
                "source": "EfficientNet-B0 Indian Neonatal Computer Vision Pipeline"
            }

        # ---------------------------------------------------------------------
        # ROUTE A: UNDER 5 YEARS -> WHO CHILD GROWTH STANDARDS
        # ---------------------------------------------------------------------
        if ref_meta["system"] == IndianGrowthStandardRouter.SYSTEM_WHO:
            who_calc = WHOLMSEngine.calculate_all_zscores(
                age_months=age_months,
                gender=norm_gender,
                weight=weight,
                height=height,
                muac=muac,
                head_circumference=head_circumference
            )

            whz = who_calc.get("whz")
            haz = who_calc.get("haz")
            waz = who_calc.get("waz")
            baz = who_calc.get("baz")

            result["growth_indices"] = {
                "whz": whz,
                "haz": haz,
                "waz": waz,
                "baz": baz,
                "bmi": bmi,
                "indicators": {
                    "whz": {
                        "indicator": "Weight-for-height (WHZ)",
                        "value": whz,
                        "unit": "SD",
                        "status": "AVAILABLE" if whz is not None else "UNABLE_TO_CALCULATE",
                        "interpretation": who_calc.get("interpretations", {}).get("whz", "Unable to calculate"),
                        "reference_system": "WHO",
                        "reference_version": "WHO-2006",
                        "age_group": "under_5"
                    },
                    "haz": {
                        "indicator": "Height-for-age (HAZ)",
                        "value": haz,
                        "unit": "SD",
                        "status": "AVAILABLE" if haz is not None else "UNABLE_TO_CALCULATE",
                        "interpretation": who_calc.get("interpretations", {}).get("haz", "Unable to calculate"),
                        "reference_system": "WHO",
                        "reference_version": "WHO-2006",
                        "age_group": "under_5"
                    },
                    "waz": {
                        "indicator": "Weight-for-age (WAZ)",
                        "value": waz,
                        "unit": "SD",
                        "status": "AVAILABLE" if waz is not None else "UNABLE_TO_CALCULATE",
                        "interpretation": who_calc.get("interpretations", {}).get("waz", "Unable to calculate"),
                        "reference_system": "WHO",
                        "reference_version": "WHO-2006",
                        "age_group": "under_5"
                    },
                    "baz": {
                        "indicator": "BMI-for-age (BAZ)",
                        "value": baz,
                        "unit": "SD",
                        "status": "REFERENCE_DATA_UNAVAILABLE" if baz is None else "AVAILABLE",
                        "interpretation": "Not available — WHO BMI-for-age reference table not loaded" if baz is None else who_calc.get("interpretations", {}).get("baz"),
                        "reference_system": "WHO",
                        "reference_version": "WHO-2006",
                        "age_group": "under_5"
                    }
                }
            }

            # MUAC evaluation for under 5
            if muac is not None:
                if age_months < 6.0:
                    muac_status = "RECORDED_NOT_VALIDATED_UNDER_6M"
                    muac_note = f"MUAC recorded ({muac:.1f} cm). Standard 11.5/12.5 cm cutoffs apply to 6–59 months; clinical evaluation priority under 6 months."
                else:
                    if muac < 11.5:
                        muac_status = "CRITICAL_RED_FLAG_SAM"
                        muac_note = f"MUAC critically low ({muac:.1f} cm < 11.5 cm) — Severe Acute Malnutrition indicator."
                    elif muac < 12.5:
                        muac_status = "MODERATE_CONCERN_MAM"
                        muac_note = f"MUAC moderately low ({muac:.1f} cm in 11.5–12.4 cm range) — Moderate Acute Malnutrition indicator."
                    else:
                        muac_status = "NORMAL_RANGE"
                        muac_note = f"MUAC within normal range ({muac:.1f} cm >= 12.5 cm)."
            else:
                muac_status = "NOT_RECORDED"
                muac_note = "MUAC was not recorded."

            result["muac_evaluation"] = {
                "status": muac_status,
                "note": muac_note,
                "value_cm": muac,
                "age_appropriate": age_months >= 6.0
            }

            # Categorize nutrition screening for under-5
            is_sam = has_bilateral_edema or (whz is not None and whz < -3.0) or (age_months >= 6.0 and muac is not None and muac < 11.5)
            is_mam = (whz is not None and whz < -2.0) or (age_months >= 6.0 and muac is not None and muac < 12.5)
            is_stunted = haz is not None and haz < -2.0
            is_underweight = waz is not None and waz < -2.0

            if is_sam:
                primary = "Severe Acute Malnutrition (SAM)"
                status_cat = "EMERGENCY_SAM"
            elif is_mam:
                primary = "Moderate Acute Malnutrition (MAM)"
                status_cat = "CONCERN_MAM"
            elif is_stunted and is_underweight:
                primary = "Chronic Stunting with Underweight"
                status_cat = "CONCERN_STUNTING_UNDERWEIGHT"
            elif is_stunted:
                primary = "Stunting / Linear Growth Faltering (HAZ < -2 SD)"
                status_cat = "CONCERN_STUNTING"
            elif is_underweight:
                primary = "Underweight / Composite Deficit (WAZ < -2 SD)"
                status_cat = "CONCERN_UNDERWEIGHT"
            elif haz is None and waz is None and whz is None:
                primary = "Unable to assess growth (reference unavailable for measurements)"
                status_cat = "UNABLE_TO_ASSESS"
            else:
                primary = "No current screening concern (WHO Standards)"
                status_cat = "NORMAL"

            result["nutrition_screening"] = {
                "category": primary,
                "is_sam": is_sam,
                "is_mam": is_mam,
                "is_stunted": is_stunted,
                "is_underweight": is_underweight,
                "has_bilateral_edema": has_bilateral_edema
            }
            result["primary_concern"] = primary
            result["clinical_status"] = status_cat
            result["who"] = who_calc

        # ---------------------------------------------------------------------
        # ROUTE B: 5 TO 18 YEARS -> IAP 2015 GROWTH CHARTS
        # ---------------------------------------------------------------------
        elif ref_meta["system"] == IndianGrowthStandardRouter.SYSTEM_IAP:
            iap_calc = IAPGrowthEngine.calculate_growth_assessment(
                age_months=age_months,
                gender=norm_gender,
                weight=weight,
                height=height
            )

            h_ass = iap_calc.get("height_assessment")
            w_ass = iap_calc.get("weight_assessment")
            b_ass = iap_calc.get("bmi_assessment")

            h_z = h_ass.get("z_score") if h_ass else None
            w_z = w_ass.get("z_score") if w_ass else None
            b_z = b_ass.get("z_score") if b_ass else None
            calc_bmi = b_ass.get("value") if b_ass else (bmi if bmi is not None else None)

            iap_indicators = {
                "hfa": {
                    "indicator": "Height-for-age (HFA)",
                    "value": h_ass.get("value") if h_ass else None,
                    "unit": "cm",
                    "z_score": h_z,
                    "median_reference": h_ass.get("median_reference") if h_ass else None,
                    "status": "AVAILABLE" if h_ass else "UNABLE_TO_CALCULATE",
                    "interpretation": h_ass.get("interpretation") if h_ass else "Unable to calculate",
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18"
                },
                "wfa": {
                    "indicator": "Weight-for-age (WFA)",
                    "value": w_ass.get("value") if w_ass else None,
                    "unit": "kg",
                    "z_score": w_z,
                    "median_reference": w_ass.get("median_reference") if w_ass else None,
                    "status": "AVAILABLE" if w_ass else "UNABLE_TO_CALCULATE",
                    "interpretation": w_ass.get("interpretation") if w_ass else "Unable to calculate",
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18"
                },
                "bmi_iap": {
                    "indicator": "BMI-for-age (IAP 2015)",
                    "value": calc_bmi,
                    "unit": "kg/m2",
                    "z_score": b_z,
                    "cutoff_23_overweight": b_ass.get("cutoff_23_overweight") if b_ass else None,
                    "cutoff_27_obese": b_ass.get("cutoff_27_obese") if b_ass else None,
                    "status": "AVAILABLE" if b_ass else "UNABLE_TO_CALCULATE",
                    "interpretation": b_ass.get("interpretation") if b_ass else "Unable to calculate",
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18"
                },
                "whz": {
                    "indicator": "Weight-for-height (WHZ)",
                    "value": None,
                    "unit": "SD",
                    "status": "NOT_APPLICABLE_FOR_AGE_GROUP",
                    "interpretation": "Weight-for-height standard is defined only for children < 5 years (under 60 months). BMI-for-age is the authoritative IAP indicator for children aged 5–18 years.",
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18"
                }
            }

            result["growth_indices"] = {
                "whz": None,
                "haz": h_z,
                "waz": w_z,
                "baz": b_z,
                "bmi": calc_bmi,
                "indicators": iap_indicators,
                "hfa": iap_indicators["hfa"],
                "wfa": iap_indicators["wfa"],
                "bmi_iap": iap_indicators["bmi_iap"]
            }

            # MUAC evaluation for 5-18 years (age-aware: not calibrated for 5-18)
            if muac is not None:
                muac_status = "RECORDED_NOT_CALIBRATED_FOR_AGE"
                muac_note = f"MUAC recorded ({muac:.1f} cm). Note: Standard 11.5/12.5 cm cutoffs apply to 6–59 months; not clinically calibrated for 5–18 years under IAP 2015."
            else:
                muac_status = "NOT_RECORDED"
                muac_note = "MUAC was not recorded."

            result["muac_evaluation"] = {
                "status": muac_status,
                "note": muac_note,
                "value_cm": muac,
                "age_appropriate": False
            }

            # Nutrition screening categorization for 5-18
            primary = iap_calc.get("primary_concern", "No current screening concern")
            is_obese = iap_calc.get("is_obese", False)
            is_overweight = iap_calc.get("is_overweight", False)
            is_stunted = iap_calc.get("is_stunted", False)
            is_underweight = iap_calc.get("is_underweight", False)

            if has_bilateral_edema:
                primary = "Bilateral Pitting Edema (Clinical Urgent Priority)"
                status_cat = "EMERGENCY_EDEMA"
            elif iap_calc.get("clinical_status") == "UNABLE_TO_ASSESS":
                status_cat = "UNABLE_TO_ASSESS"
            elif is_obese:
                status_cat = "CONCERN_OBESITY"
            elif is_overweight:
                status_cat = "CONCERN_OVERWEIGHT"
            elif is_stunted:
                status_cat = "CONCERN_STUNTING"
            elif is_underweight:
                status_cat = "CONCERN_UNDERWEIGHT"
            elif "thinness" in primary.lower():
                status_cat = "CONCERN_THINNESS"
            elif h_ass is None and w_ass is None and b_ass is None:
                status_cat = "UNABLE_TO_ASSESS"
            else:
                status_cat = "NORMAL"

            result["nutrition_screening"] = {
                "category": primary,
                "is_obese": is_obese,
                "is_overweight": is_overweight,
                "is_stunted": is_stunted,
                "is_underweight": is_underweight,
                "has_bilateral_edema": has_bilateral_edema
            }
            result["primary_concern"] = primary
            result["clinical_status"] = status_cat
            result["iap"] = iap_calc

        return result
