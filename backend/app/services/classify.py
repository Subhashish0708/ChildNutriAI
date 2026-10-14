"""
ChildNutri AI — Current-Status Classifier
WHO / CMAM cut-off rules (deterministic, no ML).

Priority hierarchy: SAM > MAM > STUNTED > UNDERWEIGHT > OVERWEIGHT > HEALTHY
A child can be multiply classified (e.g., stunted AND wasted).
"""

from typing import Optional


class StatusClassifier:
    """
    Classify nutritional status from WHO z-scores and clinical measurements.
    All boundary tests are unit-testable with exact cut-off values.
    """

    # ── Cut-off constants ─────────────────────────────────────────────────────
    SAM_WHZ = -3.0
    SAM_MUAC = 11.5          # cm, ages 6–59 months
    MAM_WHZ_LOWER = -3.0
    MAM_WHZ_UPPER = -2.0
    MAM_MUAC_LOWER = 11.5
    MAM_MUAC_UPPER = 12.5
    STUNTING_CUT = -2.0
    STUNTING_SEVERE = -3.0
    UNDERWEIGHT_CUT = -2.0
    UNDERWEIGHT_SEVERE = -3.0
    OVERWEIGHT_CUT = 2.0
    OBESE_CUT = 3.0

    def classify(
        self,
        waz: Optional[float],
        haz: Optional[float],
        whz: Optional[float],
        muac_cm: Optional[float],
        bilateral_edema: bool,
        age_months: float,
    ) -> dict:
        """
        Returns:
            {
              "headline": str,           # Primary verdict
              "conditions": list[str],   # All conditions present
              "severity": str,           # normal | moderate | severe | critical
              "muac_category": str,      # normal | mam | sam | not_applicable
              "edema": bool,
              "red_flag_hospital": bool, # True → big red banner
              "explanation": dict        # human-readable z-score text
            }
        """
        conditions = []
        red_flag = False

        # ── Bilateral oedema → immediate SAM ─────────────────────────────────
        if bilateral_edema:
            conditions.append("SAM_EDEMA")
            red_flag = True

        # ── WHZ checks ───────────────────────────────────────────────────────
        if whz is not None:
            if whz < self.SAM_WHZ:
                conditions.append("SAM_WHZ")
                red_flag = True
            elif self.MAM_WHZ_LOWER <= whz < self.MAM_WHZ_UPPER:
                conditions.append("MAM_WHZ")

        # ── MUAC checks (6–59 months only) ──────────────────────────────────
        muac_cat = "not_applicable"
        if age_months >= 6 and muac_cm is not None:
            if muac_cm < self.SAM_MUAC:
                conditions.append("SAM_MUAC")
                red_flag = True
                muac_cat = "sam"
            elif self.MAM_MUAC_LOWER <= muac_cm < self.MAM_MUAC_UPPER:
                conditions.append("MAM_MUAC")
                muac_cat = "mam"
            else:
                muac_cat = "normal"

        # ── HAZ — stunting ───────────────────────────────────────────────────
        if haz is not None:
            if haz < self.STUNTING_SEVERE:
                conditions.append("SEVERE_STUNTING")
            elif haz < self.STUNTING_CUT:
                conditions.append("STUNTING")

        # ── WAZ — underweight ────────────────────────────────────────────────
        if waz is not None:
            if waz < self.UNDERWEIGHT_SEVERE:
                conditions.append("SEVERE_UNDERWEIGHT")
            elif waz < self.UNDERWEIGHT_CUT:
                conditions.append("UNDERWEIGHT")

        # ── WHZ — overweight ─────────────────────────────────────────────────
        if whz is not None:
            if whz > self.OBESE_CUT:
                conditions.append("OBESE")
            elif whz > self.OVERWEIGHT_CUT:
                conditions.append("OVERWEIGHT")

        # ── Determine headline & severity ─────────────────────────────────────
        headline, severity = self._headline(conditions)

        # ── Build explanation ─────────────────────────────────────────────────
        explanation = self._explain(waz, haz, whz, muac_cm, age_months)

        return {
            "headline": headline,
            "conditions": conditions,
            "severity": severity,
            "muac_category": muac_cat,
            "edema": bilateral_edema,
            "red_flag_hospital": red_flag,
            "explanation": explanation,
        }

    def _headline(self, conditions: list) -> tuple[str, str]:
        """Priority: SAM > MAM > STUNTING > UNDERWEIGHT > OVERWEIGHT > HEALTHY."""
        if any(c in conditions for c in ("SAM_EDEMA", "SAM_WHZ", "SAM_MUAC")):
            return "Severe Acute Malnutrition (SAM)", "critical"
        if any(c in conditions for c in ("MAM_WHZ", "MAM_MUAC")):
            return "Moderate Acute Malnutrition (MAM)", "severe"
        if "SEVERE_STUNTING" in conditions:
            return "Severely Stunted", "severe"
        if "STUNTING" in conditions:
            return "Stunted", "moderate"
        if "SEVERE_UNDERWEIGHT" in conditions:
            return "Severely Underweight", "severe"
        if "UNDERWEIGHT" in conditions:
            return "Underweight", "moderate"
        if "OBESE" in conditions:
            return "Obese", "moderate"
        if "OVERWEIGHT" in conditions:
            return "Overweight", "moderate"
        return "Healthy", "normal"

    def _explain(self, waz, haz, whz, muac_cm, age_months) -> dict:
        explanations = {}
        if waz is not None:
            explanations["waz"] = self._z_text("weight-for-age", waz)
        if haz is not None:
            explanations["haz"] = self._z_text("height/length-for-age", haz)
        if whz is not None:
            explanations["whz"] = self._z_text("weight-for-height", whz)
        if muac_cm is not None and age_months >= 6:
            if muac_cm < 11.5:
                explanations["muac"] = f"MUAC is {muac_cm:.1f} cm — in the severe zone (< 11.5 cm)"
            elif muac_cm < 12.5:
                explanations["muac"] = f"MUAC is {muac_cm:.1f} cm — in the moderate zone (11.5–12.5 cm)"
            else:
                explanations["muac"] = f"MUAC is {muac_cm:.1f} cm — normal (≥ 12.5 cm)"
        return explanations

    def _z_text(self, label: str, z: float) -> str:
        if z <= -3:
            return f"The child's {label} z-score is {z:.2f} — well below the expected range (severe)"
        if z <= -2:
            return f"The child's {label} z-score is {z:.2f} — below the expected range (moderate concern)"
        if z <= -1:
            return f"The child's {label} z-score is {z:.2f} — slightly below average (watch zone)"
        if z <= 1:
            return f"The child's {label} z-score is {z:.2f} — within the healthy range"
        return f"The child's {label} z-score is {z:.2f} — above average"


classifier = StatusClassifier()
