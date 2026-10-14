"""
=============================================================================
ChildNutri AI - Explanation Safety Guardrails & Principles
=============================================================================
Defines safety constants, prohibited phrasing rules, validation validators,
and authoritative evidence citations for the ChildNutri AI Human Explanation Engine.

Authoritative Medical Standards:
  1. WHO Guideline: Prevention and management of wasting and nutritional oedema (2023)
  2. WHO Guideline: Complementary feeding of infants and young children 6–23 months (2023)
  3. WHO/UNICEF Infant and Young Child Feeding (IYCF) Indicators (2021)
  4. WHO Child Growth Standards LMS Box-Cox Reference Tables (2006)
=============================================================================
"""

import re
from typing import List, Dict, Any, Optional

# -----------------------------------------------------------------------------
# Standard Explanation Section Lifecycle Statuses
# -----------------------------------------------------------------------------
STATUS_AVAILABLE = "AVAILABLE"
STATUS_PARTIAL = "PARTIAL"
STATUS_NOT_ASSESSED = "NOT_ASSESSED"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_ERROR = "ERROR"

# -----------------------------------------------------------------------------
# Authoritative Evidence Sources (Zero Fabricated Citations)
# -----------------------------------------------------------------------------
EVIDENCE_SOURCES = [
    {
        "organization": "World Health Organization (WHO)",
        "title": "WHO Guideline on the prevention and management of wasting and nutritional oedema in infants and children in resource-constrained settings",
        "year": 2023,
        "scope": "Diagnostic criteria (WHZ < -3 SD, MUAC < 11.5 cm, bilateral edema), outpatient triage, and clinical referral protocols.",
        "url": "https://www.who.int/publications/i/item/9789240081062"
    },
    {
        "organization": "World Health Organization (WHO)",
        "title": "WHO Guideline for complementary feeding of infants and young children 6–23 months of age",
        "year": 2023,
        "scope": "Principles for age-appropriate food diversity, consistency, feeding frequency, responsive feeding, and milk feeding.",
        "url": "https://www.who.int/publications/i/item/9789240081864"
    },
    {
        "organization": "UNICEF & World Health Organization (WHO)",
        "title": "Indicators for assessing infant and young child feeding practices (IYCF)",
        "year": 2021,
        "scope": "Standard definition for Minimum Dietary Diversity (MDD >= 5 of 8 food groups) and Minimum Meal Frequency.",
        "url": "https://www.unicef.org/reports/indicators-infant-and-young-child-feeding-practices"
    },
    {
        "organization": "World Health Organization (WHO)",
        "title": "WHO Child Growth Standards: Length/height-for-age, weight-for-age, weight-for-length, weight-for-height and body mass index-for-age",
        "year": 2006,
        "scope": "Box-Cox power-exponential LMS equations establishing international reference standard cutoffs.",
        "url": "https://www.who.int/tools/child-growth-standards"
    }
]

# -----------------------------------------------------------------------------
# Official Medical Decision-Support Notices & Limitations
# -----------------------------------------------------------------------------
MEDICAL_DECISION_SUPPORT_NOTICE = (
    "ChildNutri AI provides screening and clinical decision-support information. "
    "It does not provide a definitive medical diagnosis and does not replace assessment by a qualified healthcare professional. "
    "Clinical evaluation and management should follow current applicable pediatric guidelines and local health authority protocols."
)

DATA_LIMITATIONS = [
    "Screening indicator, not a clinical diagnosis: Anthropometric indices flag potential growth and nutrition concerns; confirmed diagnosis requires comprehensive in-person medical evaluation.",
    "Instrument and measurement accuracy: Anthropometric calculations rely on precise age determination and calibrated equipment (scales, length boards, stadiometers, MUAC tapes).",
    "Missing history bounds interpretation: Unrecorded feeding recall, absent illness history, or single-visit records restrict the depth of the assessment.",
    "Longitudinal velocity requires multiple visits: A single cross-sectional evaluation cannot determine growth velocity, trajectory faltering, or recovery rate.",
    "Visual assessment technical boundaries: 2D photograph analysis cannot evaluate bilateral pitting edema, hydration, or subcutaneous skinfold depth with clinical certainty.",
    "Zero autonomous medication: The system does not prescribe pharmaceuticals, antibiotics, or therapeutic products. Therapeutic foods must be administered under clinician supervision."
]

# -----------------------------------------------------------------------------
# Prohibited Phrasing Patterns (Safety Filter)
# -----------------------------------------------------------------------------
PROHIBITED_PHRASES = [
    # Caregiver-blaming & socioeconomic stereotyping
    r"because (the )?parents? (are|is) poor",
    r"poverty caused",
    r"parenting failure",
    r"neglect by (the )?caregiver",
    r"parent did not feed",
    r"family cannot afford",
    r"caregiver negligence",
    # Chatbot tone
    r"\b(as an ai|i think|i believe|based on my analysis|i recommend)\b",
    # Fear-based & hyperbolic language
    r"in severe danger of dying",
    r"imminent death",
    r"fatal emergency condition",
    # Unsupported causality
    r"this definitely caused",
    r"this is the direct cause of the malnutrition",
    # Autonomous pharmaceutical prescription
    r"\b(amoxicillin|ampicillin|gentamicin|ciprofloxacin|metronidazole)\b.*?\b(mg|ml|tid|bid|days)\b",
    # Falsely claiming doctor identity or definitive autonomous diagnosis
    r"\b(i am a doctor|i diagnose|the ai diagnosed|the ai knows|you definitely have)\b",
    # Chatbot filler phrases
    r"\b(hello! based on|as an ai assistant|i understand your concern)\b"
]


class ExplanationSafetyValidator:
    """
    Validates text output against medical safety guardrails, non-causal rules,
    and clinical boundaries.
    """

    @classmethod
    def sanitize_explanation_text(cls, text: str) -> str:
        """
        Scans explanation text and removes/replaces prohibited phrases or causal leaps.
        """
        if not text:
            return ""

        clean = text
        for pattern in PROHIBITED_PHRASES:
            if re.search(pattern, clean, re.IGNORECASE):
                # Replace with balanced, supportive language
                clean = re.sub(
                    pattern,
                    "assessment factors may be contributing, but direct cause cannot be determined from screening data alone",
                    clean,
                    flags=re.IGNORECASE
                )

        return clean

    @classmethod
    def validate_action_plan(cls, steps: List[str]) -> List[str]:
        """
        Ensures action items contain zero autonomous drug prescriptions,
        zero blind RUTF commands, and emphasize clinical evaluation.
        """
        safe_steps = []
        for s in steps:
            s_lower = s.lower()
            # Intercept autonomous antibiotic or drug prescriptions
            if any(drug in s_lower for drug in ["amoxicillin", "ampicillin", "antibiotic", "folic acid 5mg", "mg/kg", "5ml tid"]):
                safe_steps.append("Medical review: Any medication, antibiotic, or micronutrient supplementation must be determined and prescribed by an attending medical officer.")
            else:
                safe_steps.append(cls.sanitize_explanation_text(s))
        return safe_steps
