"""
ChildNutri AI — Full Assessment Pipeline
Orchestrates all layers: validation → WHO engine → classifier → future risk → diet plan → explanation
"""
from __future__ import annotations
import math
from datetime import date, datetime
from typing import Optional, List

from backend.app.services.who_zscore import who_engine
from backend.app.services.classify import classifier
from backend.app.services.future_risk import compute_future_risk
from backend.app.services.diet_engine import get_diet_plan


# ── Input validation ──────────────────────────────────────────────────────────

WEIGHT_RANGE = (1.5, 30.0)     # kg
HEIGHT_RANGE = (40.0, 125.0)   # cm
MUAC_RANGE = (7.0, 25.0)       # cm
HEAD_RANGE = (25.0, 55.0)      # cm
AGE_MAX = 60                   # months


def validate_inputs(weight_kg: float, height_cm: float, muac_cm: Optional[float],
                    head_circ_cm: Optional[float], age_months: float) -> list[str]:
    warnings = []
    if not (WEIGHT_RANGE[0] <= weight_kg <= WEIGHT_RANGE[1]):
        warnings.append(f"Weight {weight_kg}kg is outside the expected range {WEIGHT_RANGE}. Please re-check.")
    if not (HEIGHT_RANGE[0] <= height_cm <= HEIGHT_RANGE[1]):
        warnings.append(f"Height {height_cm}cm is outside the expected range {HEIGHT_RANGE}. Please re-check.")
    if muac_cm is not None and not (MUAC_RANGE[0] <= muac_cm <= MUAC_RANGE[1]):
        warnings.append(f"MUAC {muac_cm}cm is outside the expected range. Please re-check.")
    if head_circ_cm is not None and not (HEAD_RANGE[0] <= head_circ_cm <= HEAD_RANGE[1]):
        warnings.append(f"Head circumference {head_circ_cm}cm is outside expected range.")
    if age_months > AGE_MAX:
        warnings.append(f"This tool is for children 0–60 months. Child is {age_months:.0f} months.")
    return warnings


def compute_age_months(dob: date, measurement_date: Optional[date] = None) -> float:
    ref = measurement_date or date.today()
    delta = ref - dob
    return round(delta.days / 30.4375, 2)


def apply_height_convention(height_cm: float, age_months: float, measured_lying: bool) -> float:
    """WHO convention: adjust 0.7 cm if measurement type doesn't match age."""
    if age_months >= 24 and measured_lying:
        return height_cm - 0.7
    if age_months < 24 and not measured_lying:
        return height_cm + 0.7
    return height_cm


def data_confidence(inputs: dict) -> str:
    """Assess confidence based on completeness of recommended fields."""
    rec_fields = ["muac_cm", "food_groups_yesterday", "diarrhoea_2w", "vaccination_status",
                  "mother_education", "wealth_score"]
    filled = sum(1 for f in rec_fields if inputs.get(f) is not None)
    if filled >= 5:
        return "High"
    if filled >= 2:
        return "Medium"
    return "Low"


# ── Map case → diet case code ─────────────────────────────────────────────────

def _diet_case(headline: str, future_tier: str) -> str:
    mapping = {
        "Severe Acute Malnutrition (SAM)": "SAM",
        "Moderate Acute Malnutrition (MAM)": "MAM",
        "Severely Stunted": "STUNTED",
        "Stunted": "STUNTED",
        "Severely Underweight": "UNDERWEIGHT",
        "Underweight": "UNDERWEIGHT",
        "Obese": "OVERWEIGHT",
        "Overweight": "OVERWEIGHT",
    }
    if headline == "Healthy":
        if future_tier == "HIGH":
            return "FUTURE_HIGH"
        if future_tier == "WATCH":
            return "FUTURE_WATCH"
        return "HEALTHY"
    return mapping.get(headline, "HEALTHY")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_assessment_pipeline(
    # Child info
    sex: str,
    dob: date,
    measurement_date: date,
    # Measurements
    weight_kg: float,
    height_cm: float,
    muac_cm: Optional[float] = None,
    head_circ_cm: Optional[float] = None,
    bilateral_edema: bool = False,
    measured_lying: Optional[bool] = None,
    # Feeding
    food_groups_yesterday: Optional[int] = None,
    meals_per_day: Optional[int] = None,
    breastfed: Optional[bool] = None,
    appetite: Optional[str] = None,
    # Health
    diarrhoea_2w: Optional[bool] = None,
    fever_2w: Optional[bool] = None,
    vaccination_status: Optional[str] = None,
    known_illness: Optional[str] = None,
    food_allergy: Optional[str] = None,
    # Home
    mother_education: Optional[str] = None,
    mother_age: Optional[int] = None,
    wealth_score: Optional[int] = None,
    rural_urban: Optional[str] = None,
    water_source: Optional[str] = None,
    toilet_type: Optional[str] = None,
    # Preference
    veg_only: bool = False,
    # History for trend analysis
    growth_history: Optional[List[dict]] = None,
    # Optional image screening result for clinical reconciliation
    photo_screening_result: Optional[dict] = None,
) -> dict:
    """
    Run the full 8-layer assessment pipeline.
    Returns a comprehensive result dict stored as result_json.
    """

    # Layer 0 — Compute age
    age_months = compute_age_months(dob, measurement_date)

    # Layer 0 — Height convention
    if measured_lying is not None:
        height_cm = apply_height_convention(height_cm, age_months, measured_lying)

    # Layer 1 — Validate
    input_warnings = validate_inputs(weight_kg, height_cm, muac_cm, head_circ_cm, age_months)

    # Data confidence
    inputs_snapshot = {
        "muac_cm": muac_cm, "food_groups_yesterday": food_groups_yesterday,
        "diarrhoea_2w": diarrhoea_2w, "vaccination_status": vaccination_status,
        "mother_education": mother_education, "wealth_score": wealth_score,
    }
    confidence = data_confidence(inputs_snapshot)

    # Layer 2 — WHO z-scores
    zscores = who_engine.compute(sex, age_months, weight_kg, height_cm, muac_cm, head_circ_cm)

    # Layer 3 — Current status classification
    classification = classifier.classify(
        waz=zscores.get("waz"),
        haz=zscores.get("haz"),
        whz=zscores.get("whz"),
        muac_cm=muac_cm,
        bilateral_edema=bilateral_edema,
        age_months=age_months,
    )

    # Layer 4 — Future risk
    context_features = {
        "age_months": age_months,
        "sex": 1 if sex == "Male" else 0,
        "food_groups": food_groups_yesterday or 0,
        "meals_per_day": meals_per_day or 0,
        "breastfed": int(bool(breastfed)),
        "diarrhoea": int(bool(diarrhoea_2w)),
        "fever": int(bool(fever_2w)),
        "vaccination": {"full": 2, "partial": 1, "none": 0}.get(vaccination_status or "", 1),
        "mother_education": {"none": 0, "primary": 1, "secondary": 2, "higher": 3}.get(mother_education or "", 1),
        "wealth_score": wealth_score or 2,
        "rural": 1 if rural_urban == "Rural" else 0,
    }

    future = compute_future_risk(
        waz=zscores.get("waz"),
        haz=zscores.get("haz"),
        whz=zscores.get("whz"),
        history=growth_history,
        context_features=context_features,
    )

    # Layer 7 — Diet plan
    diet_case = _diet_case(classification["headline"], future["tier"])
    allergies = [food_allergy] if food_allergy else []

    diet_plan = get_diet_plan(
        case=diet_case,
        age_months=age_months,
        veg_only=veg_only,
        diarrhoea=bool(diarrhoea_2w),
        anaemia=False,       # filled from OCR haemoglobin if available
        poor_appetite=appetite == "refuses" or appetite == "poor",
        allergies=allergies,
    )

    # Compile full result JSON
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "age_months": age_months,
        "input_warnings": input_warnings,
        "data_confidence": confidence,
        "zscores": zscores,
        "status_now": {
            "headline": classification["headline"],
            "conditions": classification["conditions"],
            "severity": classification["severity"],
            "muac_category": classification["muac_category"],
            "edema": classification["edema"],
            "red_flag_hospital": classification["red_flag_hospital"],
            "explanation": classification["explanation"],
        },
        "future_risk": future,
        "diet_plan": diet_plan,
        "model_versions": {
            "who_engine": "WHO-LMS-2006",
            "classifier": "CMAM-rules-v1",
            "future_risk": "LightGBM+trend-v1",
            "diet_engine": "knowledge-base-v1",
        },
    }

    # Layer 8 — Reconcile photo screening with verified anthropometric diagnosis
    if photo_screening_result:
        photo_verdict = photo_screening_result.get("verdict", "")
        clinical_headline = classification["headline"]
        is_clinical_sam = "Severe" in clinical_headline or classification.get("red_flag_hospital", False)
        is_photo_concerning = "Severe" in photo_verdict or "Concern" in photo_verdict

        discrepancy = None
        if is_photo_concerning and not is_clinical_sam and classification["severity"] in ("normal", "healthy"):
            discrepancy = {
                "flagged": True,
                "type": "false_visual_alarm",
                "message": (
                    f"Screening Discrepancy: Preliminary image screening flagged possible wasting ({photo_verdict}), "
                    f"but verified clinical anthropometry confirms Normal Nutritional Status ({clinical_headline}, "
                    f"WHZ: {zscores.get('whz', 'N/A')}, MUAC: {muac_cm or 'N/A'} cm). "
                    "Clinical measurements take absolute medical precedence; image features were likely influenced by clothing or lighting."
                )
            }
        elif is_clinical_sam and not is_photo_concerning:
            discrepancy = {
                "flagged": True,
                "type": "masked_clinical_danger",
                "message": (
                    "CRITICAL: Verified clinical measurements indicate Severe Acute Malnutrition (SAM). "
                    "Reassuring image screening must NOT override clinical hospital referral."
                )
            }

        result["photo_screening_reconciliation"] = {
            "photo_screening_provided": True,
            "photo_verdict": photo_verdict,
            "clinical_precedence": "Anthropometric measurements govern the medical diagnosis.",
            "discrepancy": discrepancy
        }

    return result
