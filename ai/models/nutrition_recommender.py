"""
=============================================================================
Nutrition Decision-Support Engine - ChildNutri AI
=============================================================================
Algorithm: Deterministic Rule-Based Clinical Nutrition Engine
Clinical Reference: WHO 2023 Complementary Feeding Guidelines + UNICEF IYCF

Architecture Pipeline:
  1. Child Clinical Data (Age, Sex, Weight, Height, MUAC, WHZ, HAZ, WAZ)
  2. Clinical Triage Check (SAM / Moderate / Normal)
  3. Nutrition Mode Selection:
       - BREASTFEEDING_SUPPORT (<6 months)
       - CLINICAL_REVIEW (SAM / Urgent Medical Referral)
       - COMPLEMENTARY_FEEDING (6–23 months)
       - CHILD_NUTRITION (24+ months)
  4. WHO 8 Food Groups Evaluation & Minimum Dietary Diversity (MDD >= 5/8)
  5. Age-Appropriate Meal Frequency Guidance vs. Reported Intake
  6. Dietary Preference & Allergy Filtering (Veg, Egg-Veg, Non-Veg, Allergens)
  7. Household Budget Optimization (Budget-Conscious, Standard, Flexible)
  8. Caloric & Protein Targets (WHO CMAM formula when therapeutic)
  9. Safe Texture & Choking Prevention Guidance
 10. Multi-Point Explainable Clinical Rationale

Used by: ai/predict.py -> backend/routers/ai.py -> /api/ai/nutrition-plan -> PDF Reports
=============================================================================
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# RUTF Dosage: 200 kcal / kg / day (WHO CMAM Protocol)
# 1 RUTF sachet (92g) = ~500 kcal
# ---------------------------------------------------------------------------
KCAL_PER_KG_PER_DAY_SAM = 200
KCAL_PER_RUTF_SACHET = 500

# ---------------------------------------------------------------------------
# WHO 8 Food Groups (UNICEF / WHO IYCF Indicator)
# ---------------------------------------------------------------------------
WHO_8_FOOD_GROUPS = [
    {"id": 1, "code": "breastmilk", "name": "Breast milk", "desc": "Continued on demand up to 2 years or beyond"},
    {"id": 2, "code": "grains", "name": "Grains, roots, tubers and plantains", "desc": "Rice, wheat, ragi, suji, poha, potato"},
    {"id": 3, "code": "pulses", "name": "Pulses, nuts and seeds", "desc": "Yellow moong, masoor dal, chana, sattu, roasted groundnut paste"},
    {"id": 4, "code": "dairy", "name": "Dairy products", "desc": "Curd/yogurt, pasteurized milk, fresh paneer"},
    {"id": 5, "code": "flesh", "name": "Flesh foods", "desc": "Finely minced chicken, fish, tender meat"},
    {"id": 6, "code": "eggs", "name": "Eggs", "desc": "Hard-boiled mashed egg yolk, whole boiled egg"},
    {"id": 7, "code": "vita", "name": "Vitamin-A-rich fruits and vegetables", "desc": "Carrot, pumpkin, papaya, mango, dark leafy greens/spinach"},
    {"id": 8, "code": "other", "name": "Other fruits and vegetables", "desc": "Banana, apple, chikoo, green beans, bottle gourd"},
]

# ---------------------------------------------------------------------------
# Age-Appropriate Feeding Frequency Rules (WHO 2023)
# ---------------------------------------------------------------------------
def get_age_appropriate_frequency(age_months: float) -> Dict[str, Any]:
    if age_months < 6:
        return {
            "mode": "BREASTFEEDING_SUPPORT",
            "min_meals": 8,
            "max_meals": 12,
            "snacks": 0,
            "guidance": "Exclusive breastfeeding on demand (8–12 times per 24 hours). No water or complementary foods."
        }
    elif age_months < 9:
        return {
            "mode": "COMPLEMENTARY_FEEDING",
            "min_meals": 2,
            "max_meals": 3,
            "snacks": 1,
            "guidance": "2–3 meals/day plus frequent breastfeeding (1–2 nutritious snacks if child expresses hunger)."
        }
    elif age_months < 12:
        return {
            "mode": "COMPLEMENTARY_FEEDING",
            "min_meals": 3,
            "max_meals": 4,
            "snacks": 2,
            "guidance": "3–4 meals/day plus continued breastfeeding (1–2 nutritious snacks as desired)."
        }
    elif age_months < 24:
        return {
            "mode": "COMPLEMENTARY_FEEDING",
            "min_meals": 3,
            "max_meals": 4,
            "snacks": 2,
            "guidance": "3–4 meals/day plus 1–2 healthy snacks, encouraging responsive self-feeding alongside breastmilk."
        }
    else:
        return {
            "mode": "CHILD_NUTRITION",
            "min_meals": 3,
            "max_meals": 3,
            "snacks": 2,
            "guidance": "3 family meals plus 2 nutritious snacks per day, emphasizing dietary diversity and active self-feeding."
        }


# ---------------------------------------------------------------------------
# Clinical Food Catalog (Tagged with Food Groups, Diet Pattern, Cost, Textures)
# ---------------------------------------------------------------------------
STRUCTURED_FOOD_CATALOG = {
    "breakfast": [
        {
            "id": "b_poha_egg",
            "title": "Soft Vegetable Poha with Boiled Egg",
            "desc": "Steamed flattened rice cooked soft with cumin, turmeric, grated carrots, and mashed boiled egg yolk.",
            "groups": [2, 6, 7],
            "diet": "egg_vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Soft moist mash / Finger food",
            "min_age": 6,
            "allergens": ["egg"]
        },
        {
            "id": "b_ragi_porridge",
            "title": "Ragi (Finger Millet) Porridge with Milk",
            "desc": "Traditional calcium-rich ragi flour cooked tender with boiled milk, mashed ripe banana, and cooking oil or ghee.",
            "groups": [2, 4, 8],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Smooth semi-thick porridge",
            "min_age": 6,
            "allergens": ["dairy"]
        },
        {
            "id": "b_idli_dal",
            "title": "Steamed Idli with Moong Dal",
            "desc": "Fermented steamed rice-lentil cake thoroughly crumbled and soaked in warm yellow moong dal stew.",
            "groups": [2, 3],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Soft soaked mash",
            "min_age": 6,
            "allergens": []
        },
        {
            "id": "b_suji_upma",
            "title": "Soft Semolina (Suji) Vegetable Porridge",
            "desc": "Roasted semolina cooked soft with finely grated carrots and vegetable oil or ghee for sustained morning calories.",
            "groups": [2, 7],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Soft moist grain porridge",
            "min_age": 7,
            "allergens": ["gluten"]
        },
        {
            "id": "b_roti_paneer",
            "title": "Soft Whole Wheat Roti with Fresh Paneer",
            "desc": "Whole wheat chapati soaked soft in warm boiled milk or thin dal and blended with fresh crumbled cottage cheese.",
            "groups": [2, 4],
            "diet": "vegetarian",
            "cost": "₹₹",
            "tier": "standard",
            "texture": "Soft soaked shreds",
            "min_age": 9,
            "allergens": ["gluten", "dairy"]
        }
    ],
    "lunch": [
        {
            "id": "l_dal_khichdi",
            "title": "Yellow Moong Dal Khichdi with Carrots",
            "desc": "Balanced grain-legume combination of soft rice and split yellow moong dal cooked with tender carrots and cumin.",
            "groups": [2, 3, 7],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Thick moist porridge",
            "min_age": 6,
            "allergens": []
        },
        {
            "id": "l_curd_rice",
            "title": "Soft Rice with Fresh Curd",
            "desc": "Cooked white rice mashed soft with fresh unsweetened curd and a pinch of roasted cumin for gentle digestion.",
            "groups": [2, 4],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Cool soft mash",
            "min_age": 7,
            "allergens": ["dairy"]
        },
        {
            "id": "l_chana_rice",
            "title": "Mashed Bengal Gram (Chana) with Rice",
            "desc": "Bengal gram cooked soft, mashed with rice and seasoned with cumin for plant protein and iron.",
            "groups": [2, 3],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Coarse soft mash",
            "min_age": 9,
            "allergens": []
        },
        {
            "id": "l_chicken_khichdi",
            "title": "Soft Minced Chicken & Rice Khichdi",
            "desc": "Finely minced chicken simmered tender with rice, yellow dal, and pumpkin for bioavailable iron and zinc.",
            "groups": [2, 3, 5, 7],
            "diet": "non_vegetarian",
            "cost": "₹₹",
            "tier": "standard",
            "texture": "Soft savoury porridge",
            "min_age": 9,
            "allergens": []
        }
    ],
    "snack": [
        {
            "id": "s_banana_curd",
            "title": "Ripe Banana with Plain Curd",
            "desc": "Naturally sweet ripe banana mashed smoothly with fresh curd for dietary potassium and probiotics.",
            "groups": [4, 8],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Smooth spoonable puree",
            "min_age": 6,
            "allergens": ["dairy"]
        },
        {
            "id": "s_papaya_puree",
            "title": "Mashed Ripe Papaya",
            "desc": "Fresh ripe papaya peeled, seeded, and fork-mashed for vitamin A and gentle dietary fiber.",
            "groups": [7],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Silky fruit mash",
            "min_age": 6,
            "allergens": []
        },
        {
            "id": "s_boiled_egg",
            "title": "Mashed Hard-Boiled Egg Yolk",
            "desc": "Hard-boiled egg yolk mashed with a spoonful of warm milk or broth for choline and essential fatty acids.",
            "groups": [6, 4],
            "diet": "egg_vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Soft crumbly mash",
            "min_age": 7,
            "allergens": ["egg", "dairy"]
        },
        {
            "id": "s_sattu_drink",
            "title": "Roasted Bengal Gram (Sattu) Drink",
            "desc": "Roasted gram flour whisked with boiled clean water or milk for quick plant-based protein.",
            "groups": [3, 4],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Smooth liquid / cup feeding",
            "min_age": 8,
            "allergens": ["dairy"]
        }
    ],
    "dinner": [
        {
            "id": "d_masoor_rice",
            "title": "Red Lentil (Masoor Dal) with Soft Rice & Spinach",
            "desc": "Quick-cooking red lentils and rice simmered with tender spinach leaves and a teaspoon of cooking oil or ghee.",
            "groups": [2, 3, 7],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Gentle warm mash",
            "min_age": 7,
            "allergens": []
        },
        {
            "id": "d_roti_dal",
            "title": "Soaked Soft Chapati in Dal Stew",
            "desc": "Fresh chapati softened in warm moong dal with cumin and cooked pumpkin.",
            "groups": [2, 3],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Soft soaked pieces",
            "min_age": 8,
            "allergens": ["gluten"]
        },
        {
            "id": "d_potato_dal",
            "title": "Mashed Potato & Moong Dal Stew",
            "desc": "Boiled potato cubes mashed with warm dal soup and a drop of healthy cooking oil for evening satiety.",
            "groups": [2, 3],
            "diet": "vegetarian",
            "cost": "₹",
            "tier": "budget_conscious",
            "texture": "Comforting smooth mash",
            "min_age": 7,
            "allergens": []
        },
        {
            "id": "d_chicken_rice",
            "title": "Soft Rice in Chicken Broth",
            "desc": "Warm rice soaked in tender shredded chicken broth with soft cooked carrots.",
            "groups": [2, 5, 7],
            "diet": "non_vegetarian",
            "cost": "₹₹",
            "tier": "standard",
            "texture": "Warm stew",
            "min_age": 10,
            "allergens": []
        }
    ]
}

# ---------------------------------------------------------------------------
# Micronutrient & Clinical Review Topics (Decision-Support Only — Non-Prescriptive)
# ---------------------------------------------------------------------------
SUPPLEMENTS_SAM = [
    {"name": "Therapeutic Nutrition Evaluation (RUTF / Inpatient F-75/F-100)", "dose": "To be evaluated by attending medical officer/NRC", "frequency": "Under direct clinical supervision (No auto-prescription)"},
    {"name": "Clinical Evaluation for Underlying Infections", "dose": "Comprehensive clinical workup by pediatrician", "frequency": "As determined by medical practitioner"},
    {"name": "National Micronutrient Protocol Review", "dose": "As per national inpatient/outpatient SAM guidelines", "frequency": "Under healthcare provider direction"},
]

SUPPLEMENTS_MAM = [
    {"name": "Supplementary Feeding Evaluation (SFP / Poshan)", "dose": "Assessment at Anganwadi / Primary Health Centre", "frequency": "Targeted supplementary food support"},
    {"name": "Micronutrient Adequacy & Dietary Counseling", "dose": "Counseling on locally available nutrient-dense foods", "frequency": "Bi-weekly health worker review"},
]

SUPPLEMENTS_MILD = [
    {"name": "Dietary Diversity & Energy Density Enhancement", "dose": "Incorporate pulses, vegetables, eggs, and healthy fats", "frequency": "Daily home meal planning"},
    {"name": "Growth Velocity Tracking", "dose": "Standard growth monitoring", "frequency": "Monthly health centre check"},
]

SUPPLEMENTS_NORMAL = [
    {"name": "Routine Pediatric Preventive Care", "dose": "Age-appropriate complementary feeding", "frequency": "Regular health checks"},
    {"name": "Nutritional Diversity Maintenance", "dose": "Balanced family diet across >= 5 WHO food groups", "frequency": "Daily"},
]

# ---------------------------------------------------------------------------
# Clinical Counselling Messages
# ---------------------------------------------------------------------------
COUNSELLING = {
    "SAM": [
        "IMMEDIATE PRIORITY: Comprehensive evaluation by a pediatrician or Nutrition Rehabilitation Centre (NRC).",
        "Therapeutic feeds (RUTF) must NOT be shared with other family members.",
        "Ensure safe, clean boiled drinking water at all times.",
        "Do NOT give sugary drinks, packaged juices, or adult spicy food during acute recovery.",
        "Follow clinical review schedule closely as prescribed by the health worker.",
    ],
    "MAM": [
        "Offer 3–4 energy-dense meals daily plus 1–2 healthy snacks.",
        "Add a teaspoon of healthy fat (cooking oil, mustard oil, butter, or ghee) to cooked porridges.",
        "Avoid watery, dilute porridges; prepare foods thick enough to stay on a spoon.",
        "Maintain monthly growth monitoring at your local health centre / Anganwadi.",
        "Enroll in Supplementary Feeding Programme (SFP / Poshan) at Anganwadi.",
    ],
    "Mild": [
        "Include foods from at least 5 different food groups daily to meet Minimum Dietary Diversity.",
        "Offer bioavailable iron and protein through pulses, eggs, dairy, or soft-cooked flesh foods.",
        "Practice responsive feeding: encourage the child patiently without force-feeding.",
        "Routine growth monitoring every 2–3 months.",
    ],
    "Normal": [
        "Maintain balanced complementary feeding with diverse seasonal foods.",
        "Continue breastfeeding on demand up to 2 years or beyond.",
        "Practice good food hygiene and responsive, self-paced feeding.",
        "Regular growth monitoring and milestone checks.",
    ]
}


def _classify_severity(prediction: str, muac: Optional[float], waz: Optional[float] = None, whz: Optional[float] = None) -> str:
    """Map prediction label + MUAC + Z-scores to SAM / MAM / Mild / Normal."""
    pred_lower = prediction.lower() if prediction else ""
    if "sam" in pred_lower or "severe" in pred_lower:
        return "SAM"
    if muac is not None and muac < 11.5:
        return "SAM"
    if (whz is not None and whz < -3.0) or (waz is not None and waz < -3.0):
        return "SAM"
    if muac is not None and muac < 12.5:
        return "MAM"
    if "mam" in pred_lower or "moderate" in pred_lower or "wast" in pred_lower:
        return "MAM"
    if (whz is not None and whz < -2.0) or (waz is not None and waz < -2.0):
        return "MAM"
    if "underweight" in pred_lower or "stunt" in pred_lower:
        return "Mild"
    if (whz is not None and whz < -1.0) or (waz is not None and waz < -1.0):
        return "Mild"
    return "Normal"


class NutritionRecommender:
    """
    WHO 2023 Complementary Feeding & CMAM/IMAM Rule-Based Decision-Support Engine.

    Features:
    - Pure rule-based architecture (no unnecessary black-box ML or LLM in clinical path)
    - WHO 8 Food Groups evaluation & MDD score tracking
    - Clinical triage priority override for acute malnutrition
    - Dietary preference (veg, egg-veg, non-veg) and allergy filtering
    - Household food access constraints (budget-conscious, standard, flexible)
    - Age-appropriate feeding frequency vs. reported eating occasions
    - Multi-point explainability rationale
    """

    @staticmethod
    def generate_plan(
        child_name: str,
        age_months: float,
        gender: str,
        weight_kg: float,
        prediction: str,
        muac: Optional[float] = None,
        waz: Optional[float] = None,
        haz: Optional[float] = None,
        whz: Optional[float] = None,
        cohort_name: str = "General",
        doctor_name: str = "Dr. Meena Rao",
        budget_tier: str = "budget_conscious",
        diet_pattern: str = "vegetarian",
        recall_groups: Optional[List[int]] = None,
        reported_occasions: Optional[int] = None,
        allergies: Optional[List[str]] = None,
        food_recall: Optional[Dict[str, Any]] = None,
        available_foods: Optional[List[str]] = None,
        has_bilateral_edema: bool = False,
        growth_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete evidence-based nutrition decision-support plan.
        """
        from ai.models.conversational_nutrition_engine import ConversationalNutritionEngine

        allergies_set = set(a.lower().strip() for a in (allergies or []))
        severity = _classify_severity(prediction, muac, waz, whz)
        if has_bilateral_edema:
            severity = "SAM"

        # If food_recall dictionary provided and recall_groups is None, analyze recall
        recall_eval = None
        if food_recall:
            recall_eval = ConversationalNutritionEngine.analyze_food_recall(food_recall, age_months)
            if recall_groups is None and recall_eval["status"] == "ASSESSED":
                recall_groups = recall_eval["groups_consumed"]


        # -----------------------------------------------------------------------
        # 1. Nutrition Mode Determination (WHO 2023)
        # -----------------------------------------------------------------------
        if age_months < 6:
            nutrition_mode = "BREASTFEEDING_SUPPORT"
        elif severity == "SAM" or (whz < -3.0) or (muac is not None and muac < 11.5):
            nutrition_mode = "CLINICAL_REVIEW"
        elif age_months <= 23:
            nutrition_mode = "COMPLEMENTARY_FEEDING"
        else:
            nutrition_mode = "CHILD_NUTRITION"

        # -----------------------------------------------------------------------
        # 2. Feeding Frequency Assessment
        # -----------------------------------------------------------------------
        freq_info = get_age_appropriate_frequency(age_months)
        frequency_gap_identified = False
        if reported_occasions is not None and reported_occasions > 0:
            if reported_occasions < freq_info["min_meals"]:
                frequency_gap_identified = True

        # -----------------------------------------------------------------------
        # 3. Dietary Diversity (MDD) Scorecard
        # -----------------------------------------------------------------------
        active_group_ids = set(recall_groups or [])
        mdd_score = len(active_group_ids)
        mdd_achieved = (mdd_score >= 5) if recall_groups is not None else None

        # -----------------------------------------------------------------------
        # 4. Caloric Targets & Therapeutic Dosage
        # -----------------------------------------------------------------------
        if severity == "SAM":
            kcal_per_kg = KCAL_PER_KG_PER_DAY_SAM
        elif severity == "MAM":
            kcal_per_kg = 130
        elif severity == "Mild":
            kcal_per_kg = 110
        else:
            kcal_per_kg = 90  # maintenance

        total_kcal_day = round(weight_kg * kcal_per_kg)
        rutf_sachets = 0.0
        rutf_guidance = None
        if severity == "SAM":
            # Reference Caloric Support for Medical Officer Evaluation only; NOT a caregiver prescription
            rutf_sachets = round(total_kcal_day / KCAL_PER_RUTF_SACHET, 1)
            rutf_guidance = (
                "Reference Caloric Need (WHO 200 kcal/kg guideline) — "
                "Strictly for Attending Medical Officer Dosing & Evaluation; "
                "Not an Autonomous Caregiver Prescription."
            )
        elif severity == "MAM":
            # For MAM, RUTF sachets are not indicated. Focus on energy-dense family food and dietary diversity.
            rutf_sachets = 0.0
            rutf_guidance = (
                "RUTF sachets are not indicated for moderate acute malnutrition (MAM). "
                "Guidance focuses on age-appropriate dietary diversity and energy-dense complementary foods."
            )
        else:
            rutf_sachets = 0.0
            rutf_guidance = "RUTF not indicated."

        # -----------------------------------------------------------------------
        # 5. Filter Meals by Age, Diet Pattern, Allergies & Budget Tier
        # -----------------------------------------------------------------------
        selected_meals = []
        slot_names = [
            ("Morning (Breakfast)", "breakfast", round(total_kcal_day * 0.25)),
            ("Mid-Day Meal (Lunch)", "lunch",     round(total_kcal_day * 0.35)),
            ("Afternoon Snack",      "snack",     round(total_kcal_day * 0.15)),
            ("Evening (Dinner)",     "dinner",    round(total_kcal_day * 0.25)),
        ]

        for display_name, slot_key, slot_kcal in slot_names:
            candidates = list(STRUCTURED_FOOD_CATALOG.get(slot_key, []))

            # Filter by age
            candidates = [m for m in candidates if m["min_age"] <= age_months]

            # Filter by allergies
            if allergies_set:
                candidates = [m for m in candidates if not any(a in allergies_set for a in m.get("allergens", []))]

            # Filter by diet pattern
            if diet_pattern == "vegetarian":
                candidates = [m for m in candidates if m["diet"] == "vegetarian"]
            elif diet_pattern == "egg_vegetarian":
                candidates = [m for m in candidates if m["diet"] in ["vegetarian", "egg_vegetarian"]]
            # non_vegetarian allows all

            # Filter by budget tier
            if budget_tier == "budget_conscious":
                tier_candidates = [m for m in candidates if m["tier"] == "budget_conscious"]
                if tier_candidates:
                    candidates = tier_candidates
            elif budget_tier == "standard":
                tier_candidates = [m for m in candidates if m["tier"] in ["budget_conscious", "standard"]]
                if tier_candidates:
                    candidates = tier_candidates

            # Select primary candidate
            chosen = candidates[0] if candidates else {
                "title": f"Nutritious {display_name}",
                "desc": "Freshly prepared grain and pulse porridge with added healthy fat.",
                "texture": "Age-appropriate soft mash",
                "groups": [2, 3]
            }

            foods = [chosen["title"]]
            # Add therapeutic note if SAM / MAM
            if severity == "SAM" and slot_key in ["breakfast", "lunch", "dinner"]:
                foods.append("Therapeutic feed consideration (Subject to medical officer evaluation)")
            elif severity == "MAM" and slot_key in ["breakfast", "lunch"]:
                foods.append("Supplementary nutrition support (Subject to health centre review)")

            # Generate specific why rationale
            meal_groups = chosen.get("groups", [])
            why_reasons = []
            if 3 in meal_groups or 4 in meal_groups or 5 in meal_groups or 6 in meal_groups:
                why_reasons.append("Supplies bioavailable protein to improve daily nutrient density and dietary diversity.")
            if 7 in meal_groups:
                why_reasons.append("Provides vitamin-A precursors and micronutrients for immunity and growth.")
            if 8 in meal_groups:
                why_reasons.append("Offers gentle dietary fiber and potassium from fruits/vegetables.")
            if not why_reasons:
                why_reasons.append(f"Provides energy-dense complementary feeding appropriate for {age_months:.0f} months.")

            selected_meals.append({
                "time_slot": display_name,
                "target_kcal": slot_kcal,
                "title": chosen["title"],
                "description": chosen["desc"],
                "texture": chosen.get("texture", "Soft mash"),
                "food_groups": chosen.get("groups", []),
                "foods": foods,
                "why_selected": " ".join(why_reasons),
                "notes": "Ensure all food is soft and lump-free." if age_months < 12 else "Encourage self-feeding."
            })

        # -----------------------------------------------------------------------
        # 6. Supplements Prescription
        # -----------------------------------------------------------------------
        if severity == "SAM":
            supplements = SUPPLEMENTS_SAM
        elif severity == "MAM":
            supplements = SUPPLEMENTS_MAM
        elif severity == "Mild":
            supplements = SUPPLEMENTS_MILD
        else:
            supplements = SUPPLEMENTS_NORMAL

        # -----------------------------------------------------------------------
        # 7. Foods to Avoid & Choking Hazards (WHO 2023)
        # -----------------------------------------------------------------------
        foods_to_avoid = [
            "Tea, coffee, sweet packaged drinks, or sodas",
            "Ultra-processed packaged snacks and high-salt foods",
            "Whole round nuts, hard seeds, unmashed chickpeas, and whole grapes (serious choking hazards under 3 years)",
            "Unpasteurized milk or unboiled drinking water",
        ]
        if severity in ["SAM", "MAM"]:
            foods_to_avoid.append("Sharing RUTF with other household members")
            foods_to_avoid.append("Watery or dilute porridges that have low energy density")

        # -----------------------------------------------------------------------
        # 8. Clinical Explainability Rationale Breakdown
        # -----------------------------------------------------------------------
        rationale = []
        # Anthropometry Point
        if whz is not None and (whz < -3.0 or (muac and muac < 11.5)):
            rationale.append(f"Clinical Triage Priority: Severe wasting detected (WHZ: {whz:.2f} SD, MUAC: {muac or 0:.1f} cm). Medical assessment and supervised therapeutic feeding take priority.")
        elif whz is not None and (whz < -2.0 or (muac and muac < 12.5)):
            rationale.append(f"Moderate Risk Identified: WHZ {whz:.2f} SD indicates moderate wasting. Focus is on energy and nutrient density alongside healthcare worker review.")
        elif whz is not None:
            rationale.append(f"Adequate Physical Growth: WHZ {whz:+.2f} SD is within normal WHO standards. Guidance maintains balanced dietary adequacy.")
        else:
            rationale.append("Physical Growth: WHO LMS Z-score not available for this record.")

        # Diversity Point
        if recall_groups is None:
            rationale.append("Dietary Recall: 24-hour food intake not yet assessed. Complete food recall to identify specific food group gaps.")
        elif mdd_achieved:
            rationale.append(f"Dietary Diversity: {mdd_score}/8 WHO food groups consumed. Minimum dietary diversity target achieved.")
        else:
            rationale.append(f"Dietary Diversity Gap: {mdd_score}/8 WHO groups consumed (target: >=5). Priorities focus on adding missing nutrient-dense food groups.")

        # Age & Development Point
        rationale.append(f"Developmental Stage: Age {age_months:.0f} months. {freq_info['guidance']}")

        # Household Access Point
        tier_labels = {"budget_conscious": "Budget-Conscious (₹)", "standard": "Standard (₹₹)", "flexible": "Flexible (₹₹₹)"}
        rationale.append(f"Household Food Access: {tier_labels.get(budget_tier, 'Standard')} tier changes available food options to match household capacity without lowering nutritional targets.")

        # 10-Part Clinical Explanation
        effective_recall_eval = recall_eval or {
            "status": "ASSESSED" if recall_groups is not None else "NOT_ASSESSED",
            "mdd_score": mdd_score if recall_groups is not None else None,
            "display_score": f"{mdd_score} / 8" if recall_groups is not None else "Not assessed yet.",
            "groups_consumed": list(active_group_ids)
        }
        safety_eval = ConversationalNutritionEngine.check_clinical_safety_and_disagreement(
            prediction=prediction,
            triage_level="RED" if severity == "SAM" else ("AMBER" if severity == "MAM" else "GREEN"),
            whz=whz,
            muac=muac,
            has_bilateral_edema=has_bilateral_edema
        )
        gaps_list = ConversationalNutritionEngine.conduct_gap_analysis(
            age_months=age_months,
            recall_eval=effective_recall_eval,
            reported_occasions=reported_occasions,
            clinical_severity=severity,
            edema=has_bilateral_edema
        )
        explanation_10_parts = ConversationalNutritionEngine.generate_10_part_explanation(
            child_name=child_name,
            age_months=age_months,
            gender=gender,
            wt=weight_kg,
            ht=100.0, # default if not known
            muac=muac,
            whz=whz,
            safety_info=safety_eval,
            recall_eval=effective_recall_eval,
            reported_occasions=reported_occasions,
            gaps=gaps_list,
            selected_meals=[{"slot": s[1], "title": m["title"], "desc": m["description"], "texture": m["texture"], "why_selected": m["why_selected"]} for s, m in zip(slot_names, selected_meals)],
            diet_pattern=diet_pattern,
            budget_tier=budget_tier,
            available_foods=set(available_foods or []),
            longitudinal_note=None
        )

        # -----------------------------------------------------------------------
        # 9. Return Unified Plan
        # -----------------------------------------------------------------------
        return {
            "child_name": child_name,
            "severity": severity,
            "malnutrition_classification": prediction,
            "nutrition_mode": nutrition_mode,
            "who_protocol": f"WHO CMAM {severity} Protocol" if severity in ["SAM", "MAM"] else "WHO 2023 Complementary Feeding Guidance",
            "caloric_target": {
                "kcal_per_kg_per_day": kcal_per_kg,
                "total_kcal_per_day": total_kcal_day,
                "protein_target_g_per_day": round(weight_kg * 2.5, 1),
            },
            "rutf_sachets_per_day": rutf_sachets,
            "rutf_clinical_guidance": rutf_guidance,
            "is_caregiver_prescription": False,
            "meal_schedule": selected_meals,
            "supplements": supplements,
            "dietary_counselling": COUNSELLING.get(severity, COUNSELLING["Normal"]),
            "foods_to_avoid": foods_to_avoid,
            "follow_up_interval_days": 7 if severity == "SAM" else (14 if severity == "MAM" else 30),
            "prescribed_by": doctor_name,
            "algorithm": "WHO 2023 Complementary Feeding & CMAM Rule-Based Decision-Support Engine",
            "cohort_context": cohort_name,
            "age_months": age_months,
            "gender": gender,
            "budget_tier": budget_tier,
            "diet_pattern": diet_pattern,
            "who_8_food_groups": WHO_8_FOOD_GROUPS,
            "age_appropriate_frequency": freq_info,
            "frequency_gap_identified": frequency_gap_identified,
            "mdd_score": mdd_score if recall_groups is not None else None,
            "mdd_achieved": mdd_achieved,
            "clinical_rationale": rationale,
            "explanation_10_parts": explanation_10_parts,
            "nutrition_gaps": gaps_list,
            "safety_status": safety_eval["safety_status"],
        }
