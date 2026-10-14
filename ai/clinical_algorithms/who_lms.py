"""
=============================================================================
WHO Child Growth Standards (2006) LMS Reference Engine - ChildNutri AI
=============================================================================
Academic Reference:
  World Health Organization. WHO Child Growth Standards: Length/height-for-age,
  weight-for-age, weight-for-length, weight-for-height and body mass index-for-age:
  Methods and development. Geneva: World Health Organization; 2006.

Methodology:
  Computes exact Box-Cox Power Exponential (LMS) Z-scores using tabulated WHO
  Multicentre Growth Reference Study (MGRS) data files for children aged 0-60 months:
    • HAZ  (Height/Length-for-Age Z-score) -> Stunting Assessment
    • WAZ  (Weight-for-Age Z-score)         -> Underweight Assessment
    • WHZ  (Weight-for-Height Z-score)      -> Acute Wasting Assessment
    • BAZ  (BMI-for-Age Z-score)            -> Explicitly flagged as not available
                                              when official bfa table is not in CSV
    • MUAC Screening Classification        -> Clinical Triage Safety Thresholds

Box-Cox LMS Formulation:
  Z = ((measurement / M)^L - 1) / (L * S)   if |L| > 0.0001
  Z = ln(measurement / M) / S               if |L| <= 0.0001

Extreme Z-Score Adjustment (WHO 2006 Guideline):
  For |Z| > 3 SD, standard LMS is adjusted using the distance to +/- 3 SD
  divided by the standard deviation of the corresponding half of the distribution.

Medical Safety Boundary:
  ChildNutri AI is a screening and clinical decision-support prototype.
  It does not provide a medical diagnosis or replace assessment by a qualified
  healthcare professional. Clinical management should follow current applicable
  clinical guidelines and local protocols.
=============================================================================
"""

import os
import math
import logging
from typing import Dict, Any, Optional, Tuple, Union
import pandas as pd

logger = logging.getLogger("childnutri.who_lms")

REFERENCE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "who_wgs_data.csv")

class WHOLMSEngine:
    """
    Official WHO Child Growth Standards 2006 LMS Reference Engine.
    Loads validated reference tables and performs deterministic Box-Cox LMS calculation.
    """
    _table_cache: Optional[pd.DataFrame] = None

    @classmethod
    def _get_reference_table(cls) -> pd.DataFrame:
        if cls._table_cache is None:
            if not os.path.exists(REFERENCE_CSV):
                raise FileNotFoundError(
                    f"Official WHO reference data file missing: {REFERENCE_CSV}. "
                    "Ensure who_wgs_data.csv is present in ai/clinical_algorithms/."
                )
            cls._table_cache = pd.read_csv(REFERENCE_CSV)
        return cls._table_cache

    @classmethod
    def normalize_gender(cls, gender: Union[str, int, float, bool]) -> bool:
        """
        Normalizes gender input to boolean: True for Male (sex=1.0), False for Female (sex=2.0).
        Raises ValueError if gender is missing or unrecognized.
        """
        if gender is None:
            raise ValueError("Child sex/gender cannot be None. Must specify 'Male' or 'Female'.")
        
        if isinstance(gender, bool):
            return gender

        s = str(gender).strip().lower()
        if s in ["1", "1.0", "male", "m", "boy"]:
            return True
        elif s in ["2", "2.0", "female", "f", "girl"]:
            return False
        else:
            raise ValueError(f"Unrecognized child sex/gender specification: '{gender}'. Must be 'Male' or 'Female'.")

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
        Validates anthropometric inputs against strict pediatric physiological boundaries.
        Returns: (is_valid, error_message)
        """
        try:
            cls.normalize_gender(gender)
        except ValueError as e:
            return False, str(e)

        if age_months is None or not isinstance(age_months, (int, float)):
            return False, "Age in months is required and must be numeric."
        if age_months < 0.0:
            return False, f"Age cannot be negative ({age_months} months provided)."

        if weight is None or not isinstance(weight, (int, float)):
            return False, "Weight in kg is required and must be numeric."
        if weight <= 0.0:
            return False, f"Weight must be greater than zero ({weight} kg provided)."
        if weight > 50.0:
            return False, f"Weight ({weight} kg) exceeds plausible pediatric screening range (max 50 kg)."

        if height is None or not isinstance(height, (int, float)):
            return False, "Height/length in cm is required and must be numeric."
        if height <= 0.0:
            return False, f"Height must be greater than zero ({height} cm provided)."
        if height < 30.0 or height > 150.0:
            return False, f"Height ({height} cm) is outside plausible pediatric screening range (30-150 cm)."

        if muac is not None:
            if not isinstance(muac, (int, float)) or muac <= 0.0:
                return False, f"MUAC must be a positive number ({muac} provided)."
            if muac < 5.0 or muac > 35.0:
                return False, f"MUAC ({muac} cm) is outside plausible pediatric range (5-35 cm)."

        if head_circumference is not None:
            if not isinstance(head_circumference, (int, float)) or head_circumference <= 0.0:
                return False, f"Head circumference must be a positive number ({head_circumference} provided)."
            if head_circumference < 20.0 or head_circumference > 65.0:
                return False, f"Head circumference ({head_circumference} cm) is outside plausible pediatric range (20-65 cm)."

        return True, None

    @classmethod
    def get_lms_from_table(cls, indicator: str, is_male: bool, given_value: float) -> Tuple[float, float, float]:
        """
        Interpolates LMS parameters from official WHO 2006 reference table.
        indicator: 'hfa', 'wfa', or 'wfh'
        is_male: True for male (sex=1.0), False for female (sex=2.0)
        given_value: age in months (for hfa, wfa) or height in cm (for wfh)
        """
        df = cls._get_reference_table()
        sex_val = 1.0 if is_male else 2.0
        sub = df[(df["indicator"] == indicator) & (df["sex"] == sex_val)].sort_values("given")

        if sub.empty:
            raise ValueError(f"No WHO reference records found for indicator '{indicator}', sex={sex_val}")

        min_given = float(sub["given"].min())
        max_given = float(sub["given"].max())

        # Strict boundary validation: do not silently clamp out-of-range inputs
        if float(given_value) < min_given - 1e-6 or float(given_value) > max_given + 1e-6:
            raise ValueError(
                f"Given value {given_value} is outside supported WHO reference range "
                f"[{min_given}, {max_given}] for indicator '{indicator}', sex={sex_val}."
            )

        val = float(given_value)

        # Find surrounding points for linear interpolation
        exact_match = sub[sub["given"] == val]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            return float(row["l"]), float(row["m"]), float(row["s"])

        lower_rows = sub[sub["given"] <= val]
        upper_rows = sub[sub["given"] >= val]

        if lower_rows.empty:
            row = upper_rows.iloc[0]
            return float(row["l"]), float(row["m"]), float(row["s"])
        if upper_rows.empty:
            row = lower_rows.iloc[-1]
            return float(row["l"]), float(row["m"]), float(row["s"])

        r1 = lower_rows.iloc[-1]
        r2 = upper_rows.iloc[0]

        g1, g2 = float(r1["given"]), float(r2["given"])
        if abs(g2 - g1) < 1e-6:
            return float(r1["l"]), float(r1["m"]), float(r1["s"])

        weight = (val - g1) / (g2 - g1)
        l_interp = float(r1["l"]) + weight * (float(r2["l"]) - float(r1["l"]))
        m_interp = float(r1["m"]) + weight * (float(r2["m"]) - float(r1["m"]))
        s_interp = float(r1["s"]) + weight * (float(r2["s"]) - float(r1["s"]))

        return l_interp, m_interp, s_interp

    @classmethod
    def calculate_zscore(cls, measurement: float, L: float, M: float, S: float) -> float:
        """
        Calculates LMS Z-Score per WHO 2006 guidelines:
        Z = ((measurement / M)^L - 1) / (L * S)  if |L| > 0.0001
        Z = ln(measurement / M) / S               if |L| <= 0.0001
        Applies WHO extreme Z-score adjustments beyond +/- 3 SD.
        Never returns a silent 0.0 default for invalid parameters.
        """
        if measurement is None or measurement <= 0:
            raise ValueError(f"Measurement must be a positive number for LMS calculation (got {measurement}).")
        if M is None or M <= 0:
            raise ValueError(f"LMS parameter M (median) must be a positive number (got {M}).")
        if S is None or S <= 0:
            raise ValueError(f"LMS parameter S (dispersion) must be a positive number (got {S}).")

        if abs(L) < 1e-4:
            z = math.log(measurement / M) / S
        else:
            z = (((measurement / M) ** L) - 1.0) / (L * S)

        # Extreme Z-Score Adjustment (WHO standard cutoffs at +/- 3 SD)
        if z > 3.0:
            if abs(L) < 1e-4:
                sd3pos = M * math.exp(3.0 * S)
                sd2pos = M * math.exp(2.0 * S)
            else:
                sd3pos = M * ((1.0 + L * S * 3.0) ** (1.0 / L))
                sd2pos = M * ((1.0 + L * S * 2.0) ** (1.0 / L))
            sd23pos = sd3pos - sd2pos
            if sd23pos > 0:
                z = 3.0 + (measurement - sd3pos) / sd23pos
        elif z < -3.0:
            if abs(L) < 1e-4:
                sd3neg = M * math.exp(-3.0 * S)
                sd2neg = M * math.exp(-2.0 * S)
            else:
                sd3neg = M * ((1.0 - L * S * 3.0) ** (1.0 / L))
                sd2neg = M * ((1.0 - L * S * 2.0) ** (1.0 / L))
            sd23neg = sd2neg - sd3neg
            if sd23neg > 0:
                z = -3.0 + (measurement - sd3neg) / sd23neg

        return round(float(z), 2)

    @classmethod
    def compute_haz(
        cls,
        age_months: float,
        height: float,
        gender: Any = "Male",
        is_recumbent: Optional[bool] = None
    ) -> Optional[float]:
        """
        Computes Height/Length-for-Age Z-score (HAZ) using official WHO 2006 reference table.
        Per WHO 2006 Child Growth Standards methodology:
          - Children < 24 months (or < 85 cm) are measured recumbently (length).
          - Children >= 24 months (or >= 85 cm) are measured standing (height).
          - If standing height is measured on a child < 24 months, +0.7 cm is added to convert to length.
          - If recumbent length is measured on a child >= 24 months, -0.7 cm is subtracted to convert to height.
        Returns None if child age exceeds WHO 0-60 months range.
        """
        if age_months is None or age_months < 0:
            raise ValueError(f"Invalid age for HAZ calculation: {age_months}")
        if age_months > 60.0:
            logger.info(f"Age {age_months}m exceeds supported WHO 0-60m range. Returning None.")
            return None
        if height is None or height <= 0:
            raise ValueError(f"Invalid height for HAZ calculation: {height}")
        is_male = cls.normalize_gender(gender)

        eff_height = float(height)
        if is_recumbent is not None:
            if age_months < 24.0 and not is_recumbent:
                eff_height += 0.7
            elif age_months >= 24.0 and is_recumbent:
                eff_height -= 0.7

        L, M, S = cls.get_lms_from_table("hfa", is_male, float(age_months))
        return cls.calculate_zscore(eff_height, L, M, S)

    @classmethod
    def compute_waz(cls, age_months: float, weight: float, gender: Any = "Male") -> Optional[float]:
        """Computes Weight-for-Age Z-score (WAZ) using official WHO 2006 reference table.
        Returns None if child age exceeds WHO 0-60 months range."""
        if age_months is None or age_months < 0:
            raise ValueError(f"Invalid age for WAZ calculation: {age_months}")
        if age_months > 60.0:
            logger.info(f"Age {age_months}m exceeds supported WHO 0-60m range. Returning None.")
            return None
        if weight is None or weight <= 0:
            raise ValueError(f"Invalid weight for WAZ calculation: {weight}")
        is_male = cls.normalize_gender(gender)
        L, M, S = cls.get_lms_from_table("wfa", is_male, float(age_months))
        return cls.calculate_zscore(float(weight), L, M, S)

    @classmethod
    def compute_whz(
        cls,
        height: float,
        weight: float,
        gender: Any = "Male",
        age_months: Optional[float] = None,
        is_recumbent: Optional[bool] = None
    ) -> Optional[float]:
        """
        Computes Weight-for-Height/Length Z-score (WHZ) using official WHO 2006 reference table.
        Applies posture correction if measurement method is specified.
        Returns None without extrapolation if effective height falls outside [45.0, 120.0] cm.
        """
        if height is None or height <= 0:
            raise ValueError(f"Invalid height for WHZ calculation: {height}")
        if weight is None or weight <= 0:
            raise ValueError(f"Invalid weight for WHZ calculation: {weight}")
        is_male = cls.normalize_gender(gender)

        eff_height = float(height)
        if is_recumbent is not None and age_months is not None:
            if age_months < 24.0 and not is_recumbent:
                eff_height += 0.7
            elif age_months >= 24.0 and is_recumbent:
                eff_height -= 0.7

        # Weight-for-height is officially defined only for 45.0 to 120.0 cm
        if eff_height < 45.0 or eff_height > 120.0:
            logger.info(
                f"Effective height {eff_height:.1f} cm is outside supported WHO weight-for-height range "
                "[45.0, 120.0] cm. Returning None without extrapolation."
            )
            return None

        L, M, S = cls.get_lms_from_table("wfh", is_male, eff_height)
        return cls.calculate_zscore(float(weight), L, M, S)

    @classmethod
    def compute_baz(cls, age_months: float, height: float, weight: float, gender: Any = "Male") -> Optional[float]:
        """
        BMI-for-Age Z-score (BAZ) reference method.
        Note: The official WHO 2006 BMI-for-Age (bfa) reference tables are NOT included
        in who_wgs_data.csv. Per Phase 2 medical integrity specifications, ChildNutri AI
        strictly refuses to substitute arbitrary synthetic formulas for official WHO standards.
        Returns None to honestly indicate reference data unavailability.
        """
        df = cls._get_reference_table()
        if "bfa" not in df["indicator"].values:
            logger.info("WHO BMI-for-Age (bfa) reference table not present in reference data. Returning None.")
            return None
        is_male = cls.normalize_gender(gender)
        height_m = float(height) / 100.0
        bmi = float(weight) / (height_m ** 2) if height_m > 0 else 0.0
        L, M, S = cls.get_lms_from_table("bfa", is_male, float(age_months))
        return cls.calculate_zscore(bmi, L, M, S)

    @classmethod
    def interpret_whz(cls, whz: Optional[float]) -> str:
        if whz is None:
            return "Not available — Weight-for-height reference requires height between 45.0 and 120.0 cm"
        if whz < -5.0 or whz > 5.0:
            return f"Extreme biological outlier requiring clinical verification (|WHZ| > 5 SD: {whz:+.2f} SD)"
        elif whz < -3.0:
            return "Severe wasting range (< -3 SD)"
        elif whz < -2.0:
            return "Moderate wasting range (< -2 SD)"
        elif whz > 3.0:
            return "Obese range (> +3 SD)"
        elif whz > 2.0:
            return "Overweight range (> +2 SD)"
        return "Normal body mass (within reference range: -2 to +2 SD)"

    @classmethod
    def interpret_haz(cls, haz: Optional[float]) -> str:
        if haz is None:
            return "Not available — Height-for-age reference requires age between 0 and 60 months"
        if haz < -6.0 or haz > 6.0:
            return f"Extreme biological outlier requiring clinical verification (|HAZ| > 6 SD: {haz:+.2f} SD)"
        elif haz < -3.0:
            return "Severe stunting range (< -3 SD)"
        elif haz < -2.0:
            return "Moderate stunting range (< -2 SD)"
        elif haz > 3.0:
            return "Very tall range (> +3 SD)"
        return "Normal linear growth (within reference range: -2 to +2 SD)"

    @classmethod
    def interpret_waz(cls, waz: Optional[float]) -> str:
        if waz is None:
            return "Not available — Weight-for-age reference requires age between 0 and 60 months"
        if waz < -6.0 or waz > 5.0:
            return f"Extreme biological outlier requiring clinical verification (WAZ flag: {waz:+.2f} SD)"
        elif waz < -3.0:
            return "Severe underweight range (< -3 SD)"
        elif waz < -2.0:
            return "Moderate underweight range (< -2 SD)"
        return "Normal weight range (within reference range: -2 to +2 SD)"

    @classmethod
    def interpret_baz(cls, baz: Optional[float]) -> str:
        if baz is None:
            return "Not available — WHO BMI-for-age reference table not loaded in dataset"
        if baz < -5.0 or baz > 5.0:
            return f"Extreme biological outlier requiring clinical verification (BAZ flag: {baz:+.2f} SD)"
        elif baz < -3.0:
            return "Severe acute thinness range (< -3 SD)"
        elif baz < -2.0:
            return "Moderate thinness range (< -2 SD)"
        elif baz > 3.0:
            return "Obese range (> +3 SD)"
        elif baz > 2.0:
            return "Overweight range (> +2 SD)"
        return "Normal BMI range (within reference range: -2 to +2 SD)"

    @classmethod
    def calculate_all_zscores(
        cls,
        age_months: float,
        gender: Any,
        weight: float,
        height: float,
        muac: Optional[float] = None,
        head_circumference: Optional[float] = None,
        is_recumbent: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Computes all WHO standard Z-scores, clinical classifications, and deficit percentiles.
        Uses WHO 2006 reference tables (hfa, wfa, wfh).
        Rejects invalid inputs and explicitly flags out-of-range (>60 months) evaluations.
        """
        # 1. Input Validation
        is_valid, err_msg = cls.validate_anthropometric_inputs(
            age_months=age_months,
            gender=gender,
            weight=weight,
            height=height,
            muac=muac,
            head_circumference=head_circumference
        )
        if not is_valid:
            raise ValueError(f"Anthropometric validation failed: {err_msg}")

        # 2. Check Age Range (WHO 0-60 Months Standard)
        if age_months > 60.0:
            logger.warning(f"Age {age_months} months outside supported WHO 0-60 standard range.")
            return {
                "status": "out_of_range",
                "calculation_status": "REFERENCE_DATA_UNAVAILABLE",
                "reference_standard": "WHO Child Growth Standards (2006) 0-60 Months",
                "reference": {
                    "organization": "WHO",
                    "standard": "Child Growth Standards",
                    "version": "2006 (0-60 months)",
                    "supported_age_months": [0.0, 60.0]
                },
                "age_months": age_months,
                "sex": "male" if cls.normalize_gender(gender) else "female",
                "haz": None,
                "waz": None,
                "whz": None,
                "baz": None,
                "baz_status": "not_available",
                "haz_status": "REFERENCE_DATA_UNAVAILABLE",
                "waz_status": "REFERENCE_DATA_UNAVAILABLE",
                "whz_status": "REFERENCE_DATA_UNAVAILABLE",
                "raw_height_cm": float(height),
                "calculation_height_cm": float(height),
                "posture_adjustment_applied": False,
                "posture_adjustment_cm": 0.0,
                "posture_note": "No adjustment applied (out of range).",
                "bmi": round(weight / ((height / 100.0) ** 2), 2) if height > 0 else None,
                "stunting_status": "Out of Range (>60 months)",
                "wasting_status": "Out of Range (>60 months)",
                "underweight_status": "Out of Range (>60 months)",
                "muac_category": "Standard Evaluation Required",
                "who_summary": f"Age {age_months}m exceeds WHO 0-60m standard range.",
                "interpretations": {
                    "whz": "Out of Range (>60 months)",
                    "haz": "Out of Range (>60 months)",
                    "waz": "Out of Range (>60 months)",
                    "baz": "Out of Range (>60 months)"
                },
                "message": "WHO Child Growth Standards (2006) apply to children aged 0-60 months. Child exceeds supported age range."
            }

        # 3. Track Posture Adjustment Provenance
        eff_height = float(height)
        posture_adjustment_applied = False
        posture_adjustment_cm = 0.0
        posture_note = "Standard measurement protocol applied."
        if is_recumbent is not None:
            if age_months < 24.0 and not is_recumbent:
                eff_height += 0.7
                posture_adjustment_applied = True
                posture_adjustment_cm = 0.7
                posture_note = "Standing height converted to recumbent length (+0.7 cm) for age < 24 months."
            elif age_months >= 24.0 and is_recumbent:
                eff_height -= 0.7
                posture_adjustment_applied = True
                posture_adjustment_cm = -0.7
                posture_note = "Recumbent length converted to standing height (-0.7 cm) for age >= 24 months."

        # 4. Compute Official LMS Z-Scores
        haz = cls.compute_haz(age_months, height, gender, is_recumbent=is_recumbent)
        waz = cls.compute_waz(age_months, weight, gender)
        whz = cls.compute_whz(height, weight, gender, age_months=age_months, is_recumbent=is_recumbent)
        baz = cls.compute_baz(age_months, height, weight, gender)

        height_m = float(height) / 100.0
        bmi = round(float(weight) / (height_m ** 2), 2) if height_m > 0 else 0.0

        # 5. Reference-Based Clinical Classifications (Official WHO cutoffs)
        # Stunting: Height-for-Age
        if haz is not None:
            if haz < -3.0:
                stunting_class = "Severe Stunting"
            elif haz < -2.0:
                stunting_class = "Moderate Stunting"
            elif haz > 3.0:
                stunting_class = "Very Tall"
            else:
                stunting_class = "Normal"
        else:
            stunting_class = "Unable to assess (reference unavailable)"

        # Acute Wasting: Weight-for-Height & MUAC
        if (whz is not None and whz < -3.0) or (muac is not None and muac < 11.5):
            wasting_class = "Severe Wasting (SAM)"
        elif (whz is not None and whz < -2.0) or (muac is not None and muac < 12.5):
            wasting_class = "Moderate Wasting (MAM)"
        elif whz is not None and whz > 3.0:
            wasting_class = "Obese"
        elif whz is not None and whz > 2.0:
            wasting_class = "Overweight"
        elif whz is not None:
            wasting_class = "Normal"
        elif muac is not None:
            wasting_class = "Normal by MUAC"
        else:
            wasting_class = "Unable to assess (height outside 45-120 cm range)"

        # Underweight: Weight-for-Age
        if waz is not None:
            if waz < -3.0:
                underweight_class = "Severe Underweight"
            elif waz < -2.0:
                underweight_class = "Moderate Underweight"
            else:
                underweight_class = "Normal"
        else:
            underweight_class = "Unable to assess (reference unavailable)"

        # MUAC Category (WHO/UNICEF cutoffs for children 6-59 months)
        muac_category = "Normal (>= 12.5 cm)"
        if muac is not None:
            if muac < 11.5:
                muac_category = "Red: Severe Acute Malnutrition (< 11.5 cm)"
            elif muac < 12.5:
                muac_category = "Yellow: Moderate Acute Malnutrition (11.5 - 12.4 cm)"
            else:
                muac_category = "Green: Normal (>= 12.5 cm)"

        interpretations = {
            "whz": cls.interpret_whz(whz),
            "haz": cls.interpret_haz(haz),
            "waz": cls.interpret_waz(waz),
            "baz": cls.interpret_baz(baz)
        }

        # Build summary
        summary_parts = []
        if haz is not None:
            summary_parts.append(f"HAZ={haz} SD")
        if waz is not None:
            summary_parts.append(f"WAZ={waz} SD")
        if whz is not None:
            summary_parts.append(f"WHZ={whz} SD")
        who_summary = ", ".join(summary_parts) if summary_parts else "Growth indices not calculable for given measurements"

        # Overall calculation status
        if haz is not None and waz is not None and whz is not None:
            calc_status = "CALCULATED"
        elif haz is not None or waz is not None or whz is not None:
            calc_status = "PARTIAL_CALCULATION"
        else:
            calc_status = "REFERENCE_DATA_UNAVAILABLE"

        return {
            "status": "available",
            "calculation_status": calc_status,
            "reference_standard": "WHO Child Growth Standards (2006) 0-60 Months",
            "reference": {
                "organization": "WHO",
                "standard": "Child Growth Standards",
                "version": "2006 (0-60 months)",
                "methodology": "Box-Cox Power Exponential (LMS) with Extreme Z-Score Adjustment"
            },
            "age_months": float(age_months),
            "sex": "male" if cls.normalize_gender(gender) else "female",
            "haz": haz,
            "waz": waz,
            "whz": whz,
            "baz": baz,
            "haz_status": "CALCULATED" if haz is not None else "REFERENCE_DATA_UNAVAILABLE",
            "waz_status": "CALCULATED" if waz is not None else "REFERENCE_DATA_UNAVAILABLE",
            "whz_status": "CALCULATED" if whz is not None else "REFERENCE_DATA_UNAVAILABLE",
            "baz_status": "available" if baz is not None else "not_available",
            "raw_height_cm": round(float(height), 1),
            "calculation_height_cm": round(eff_height, 1),
            "posture_adjustment_applied": posture_adjustment_applied,
            "posture_adjustment_cm": posture_adjustment_cm,
            "posture_note": posture_note,
            "bmi": bmi,
            "stunting_status": stunting_class,
            "wasting_status": wasting_class,
            "underweight_status": underweight_class,
            "muac_category": muac_category,
            "who_summary": who_summary,
            "interpretations": interpretations,
            "safety_boundary": "Screening and decision-support reference. Non-diagnostic."
        }

if __name__ == "__main__":
    eng = WHOLMSEngine()
    sample = eng.calculate_all_zscores(
        age_months=12.0,
        gender="Male",
        weight=9.68,
        height=75.7,
        muac=13.0,
        head_circumference=46.0
    )
    print("WHO 2006 Reference LMS Output:")
    for k, v in sample.items():
        print(f"  {k:<22}: {v}")
