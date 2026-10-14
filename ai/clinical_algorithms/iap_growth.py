"""
=============================================================================
Indian Academy of Pediatrics (IAP) 2015 Growth Charts Engine
=============================================================================
Academic Reference:
  Indian Academy of Pediatrics Growth Charts Committee, Khadilkar V, Yadav S,
  Agrawal KK, Tamboli S, Banerjee M, et al. Revised IAP growth charts for height,
  weight and body mass index for 5- to 18-year-old Indian children.
  Indian Pediatr. 2015;52:47–55. PMID: 25638185.

Scope & Target Population:
  • Indian children and adolescents aged 5 to 18 years (60 to 216 months).
  • Implements official IAP 2015 reference centiles and standard deviations for:
      - Height-for-age (HFA)
      - Weight-for-age (WFA)
      - Body Mass Index-for-age (BMI)
  • Implements adult-equivalent BMI cut-offs for Asian Indian children:
      - 23 kg/m² adult-equivalent line -> Overweight screening
      - 27 kg/m² adult-equivalent line -> Obesity screening
  • Stunting screening: Height < 3rd centile (or Z < -2.0 SD)
  • Underweight screening: Weight < 3rd centile (or Z < -2.0 SD)

Medical Disclaimer:
  This system is intended for screening and clinical decision support and does
  not replace diagnostic assessment by a qualified pediatrician or endocrinologist.
=============================================================================
"""

import os
import math
import logging
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("childnutri.iap_growth")

REFERENCE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iap_growth_data.csv")


class IAPGrowthEngine:
    """
    Official Indian Academy of Pediatrics (IAP) 2015 Growth Engine for 5-18 Years.
    """
    _table_cache: Optional[pd.DataFrame] = None

    @classmethod
    def _get_reference_table(cls) -> pd.DataFrame:
        if cls._table_cache is None:
            if not os.path.exists(REFERENCE_CSV):
                raise FileNotFoundError(
                    f"Official IAP reference data file missing: {REFERENCE_CSV}. "
                    "Ensure iap_growth_data.csv is present in ai/clinical_algorithms/."
                )
            cls._table_cache = pd.read_csv(REFERENCE_CSV)
        return cls._table_cache

    @classmethod
    def normalize_gender(cls, gender: Union[str, int, float, bool]) -> str:
        """
        Normalizes gender to 'Male' or 'Female'.
        Raises ValueError if gender is invalid.
        """
        if gender is None:
            raise ValueError("Child sex/gender cannot be None. Must specify 'Male' or 'Female'.")
        if isinstance(gender, bool):
            return "Male" if gender else "Female"
        s = str(gender).strip().lower()
        if s in ["1", "1.0", "male", "m", "boy"]:
            return "Male"
        elif s in ["2", "2.0", "female", "f", "girl", "0", "0.0"]:
            return "Female"
        else:
            raise ValueError(f"Unrecognized child sex/gender specification: '{gender}'. Must be 'Male' or 'Female'.")

    @classmethod
    def interpolate_reference_row(
        cls,
        df: pd.DataFrame,
        indicator: str,
        sex: str,
        age_years: float
    ) -> Optional[Dict[str, float]]:
        """
        Linearly interpolates percentile/SD parameters for exact age in years [5.0, 18.0].
        """
        sub = df[(df["indicator"] == indicator) & (df["sex"] == sex)].sort_values("age_years")
        if sub.empty:
            return None

        ages = sub["age_years"].values
        if age_years < ages[0] or age_years > ages[-1]:
            return None

        # Exact match
        exact = sub[sub["age_years"] == age_years]
        if not exact.empty:
            return exact.iloc[0].to_dict()

        # Find adjacent brackets for linear interpolation
        idx = np.searchsorted(ages, age_years)
        a0, a1 = ages[idx - 1], ages[idx]
        row0 = sub[sub["age_years"] == a0].iloc[0]
        row1 = sub[sub["age_years"] == a1].iloc[0]

        t = (age_years - a0) / (a1 - a0)
        res = {"indicator": indicator, "sex": sex, "age_years": age_years}
        for col in sub.columns:
            if col in ["indicator", "sex"]:
                continue
            v0 = row0[col]
            v1 = row1[col]
            if pd.notna(v0) and pd.notna(v1):
                res[col] = float(v0 + t * (v1 - v0))
            else:
                res[col] = None
        return res

    @classmethod
    def calculate_growth_assessment(
        cls,
        age_months: float,
        gender: Union[str, int, float, bool],
        weight: Optional[float],
        height: Optional[float]
    ) -> Dict[str, Any]:
        """
        Comprehensive IAP 2015 Growth Assessment for a child aged 5.0 to 18.0 years (60-216 months).
        Returns standardized dictionary with height, weight, and BMI evaluation.
        """
        sex = cls.normalize_gender(gender)
        age_years = round(age_months / 12.0, 2)
        df = cls._get_reference_table()

        # Strict Age Boundary Enforcement for IAP 2015 (5 to 18 years / 60 to 216 months)
        if age_months < 60.0 or age_months > 216.0 or age_years < 5.0 or age_years > 18.0:
            return {
                "status": "out_of_range",
                "calculation_status": "REFERENCE_DATA_UNAVAILABLE",
                "reference_standard": {
                    "system": "IAP",
                    "version": "IAP-2015",
                    "age_group": "5_to_18",
                    "guideline_title": "Growth reference: IAP 2015 Growth Charts — Indian children 5–18 years",
                    "target_population": "Indian children and adolescents (5–18 years)",
                    "academic_citation": "Khadilkar V, et al. Indian Pediatr. 2015;52:47–55"
                },
                "age_years": age_years,
                "age_months": age_months,
                "sex": sex,
                "height_assessment": None,
                "weight_assessment": None,
                "bmi_assessment": None,
                "primary_concern": f"Age ({age_months:.1f} months / {age_years:.1f} years) outside supported IAP 2015 range (5–18 years)",
                "clinical_status": "UNABLE_TO_ASSESS",
                "is_stunted": False,
                "is_underweight": False,
                "is_overweight": False,
                "is_obese": False,
                "message": "IAP 2015 Growth Charts apply strictly to children and adolescents aged 5 to 18 years (60 to 216 months)."
            }

        result = {
            "status": "available",
            "calculation_status": "CALCULATED",
            "reference_standard": {
                "system": "IAP",
                "version": "IAP-2015",
                "age_group": "5_to_18",
                "guideline_title": "Growth reference: IAP 2015 Growth Charts — Indian children 5–18 years",
                "target_population": "Indian children and adolescents (5–18 years)",
                "academic_citation": "Khadilkar V, et al. Indian Pediatr. 2015;52:47–55"
            },
            "age_years": age_years,
            "age_months": age_months,
            "sex": sex,
            "height_assessment": None,
            "weight_assessment": None,
            "bmi_assessment": None,
            "primary_concern": "No current screening concern",
            "clinical_status": "NORMAL",
            "is_stunted": False,
            "is_underweight": False,
            "is_overweight": False,
            "is_obese": False
        }

        has_ht = (height is not None and height > 0)
        has_wt = (weight is not None and weight > 0)
        if not has_ht and not has_wt:
            result["status"] = "incomplete_inputs"
            result["calculation_status"] = "DATA_INSUFFICIENT"
            result["primary_concern"] = "Unable to calculate — weight and height measurements missing"
            result["clinical_status"] = "UNABLE_TO_ASSESS"
            return result

        # 1. Height-for-Age Assessment
        if height is not None and height > 0:
            h_ref = cls.interpolate_reference_row(df, "hfa", sex, age_years)
            if h_ref:
                p50 = h_ref["p50"]
                sd = h_ref["sd"]
                z = round((height - p50) / sd, 2) if sd and sd > 0 else None
                
                # Percentile approximation
                p3 = h_ref.get("p3")
                p10 = h_ref.get("p10")
                p97 = h_ref.get("p97")

                if p3 is not None and height < p3:
                    interp = "Short stature / Stunted (< 3rd percentile IAP 2015)"
                    is_stunted = True
                elif p10 is not None and height < p10:
                    interp = "Mildly low height-for-age (3rd–10th percentile IAP 2015)"
                    is_stunted = False
                elif p97 is not None and height > p97:
                    interp = "Tall stature (> 97th percentile IAP 2015)"
                    is_stunted = False
                else:
                    interp = "Normal stature (within 10th–97th percentile IAP 2015)"
                    is_stunted = False

                result["height_assessment"] = {
                    "indicator": "Height-for-age",
                    "value": round(float(height), 1),
                    "unit": "cm",
                    "z_score": z,
                    "median_reference": round(p50, 1),
                    "sd": round(sd, 1),
                    "p3": round(p3, 1) if p3 else None,
                    "p50": round(p50, 1),
                    "p97": round(p97, 1) if p97 else None,
                    "interpretation": interp,
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18",
                    "interpretation_method": "IAP 2015 Centiles & Z-scores"
                }
                result["is_stunted"] = is_stunted

        # 2. Weight-for-Age Assessment
        if weight is not None and weight > 0:
            w_ref = cls.interpolate_reference_row(df, "wfa", sex, age_years)
            if w_ref:
                p50 = w_ref["p50"]
                sd = w_ref["sd"]
                z = round((weight - p50) / sd, 2) if sd and sd > 0 else None
                p3 = w_ref.get("p3")
                p10 = w_ref.get("p10")
                p97 = w_ref.get("p97")

                if p3 is not None and weight < p3:
                    interp = "Underweight (< 3rd percentile IAP 2015)"
                    is_underweight = True
                elif p10 is not None and weight < p10:
                    interp = "Borderline low weight-for-age (3rd–10th percentile IAP 2015)"
                    is_underweight = False
                elif p97 is not None and weight > p97:
                    interp = "High weight-for-age (> 97th percentile IAP 2015)"
                    is_underweight = False
                else:
                    interp = "Normal weight-for-age (IAP 2015)"
                    is_underweight = False

                result["weight_assessment"] = {
                    "indicator": "Weight-for-age",
                    "value": round(float(weight), 1),
                    "unit": "kg",
                    "z_score": z,
                    "median_reference": round(p50, 1),
                    "sd": round(sd, 1),
                    "p3": round(p3, 1) if p3 else None,
                    "p50": round(p50, 1),
                    "p97": round(p97, 1) if p97 else None,
                    "interpretation": interp,
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18",
                    "interpretation_method": "IAP 2015 Centiles & Z-scores"
                }
                result["is_underweight"] = is_underweight

        # 3. BMI-for-Age Assessment (with adult-equivalent 23 and 27 cut-offs)
        if weight is not None and height is not None and weight > 0 and height > 0:
            bmi = round(float(weight) / ((float(height) / 100.0) ** 2), 2)
            b_ref = cls.interpolate_reference_row(df, "bmi", sex, age_years)
            if b_ref:
                p50 = b_ref["p50"]
                sd = b_ref["sd"]
                c23 = b_ref.get("cutoff_23_overweight")
                c27 = b_ref.get("cutoff_27_obese")
                p3 = b_ref.get("p3")
                p5 = b_ref.get("p5")

                z = round((bmi - p50) / sd, 2) if sd and sd > 0 else None

                if c27 is not None and bmi >= c27:
                    interp = "Obesity (>= 27 kg/m² adult-equivalent cutoff IAP 2015)"
                    result["is_obese"] = True
                elif c23 is not None and bmi >= c23:
                    interp = "Overweight (>= 23 kg/m² adult-equivalent cutoff IAP 2015)"
                    result["is_overweight"] = True
                elif p3 is not None and bmi < p3:
                    interp = "Severe thinness (< 3rd percentile IAP 2015)"
                elif p5 is not None and bmi < p5:
                    interp = "Thinness / Mild undernutrition (< 5th percentile IAP 2015)"
                else:
                    interp = "Normal BMI range (IAP 2015)"

                result["bmi_assessment"] = {
                    "indicator": "BMI-for-age",
                    "value": bmi,
                    "unit": "kg/m2",
                    "z_score": z,
                    "median_reference": round(p50, 1),
                    "sd": round(sd, 1),
                    "cutoff_23_overweight": round(c23, 1) if c23 else None,
                    "cutoff_27_obese": round(c27, 1) if c27 else None,
                    "p3": round(p3, 1) if p3 else None,
                    "p5": round(p5, 1) if p5 else None,
                    "p50": round(p50, 1),
                    "interpretation": interp,
                    "reference_system": "IAP",
                    "reference_version": "IAP-2015",
                    "age_group": "5_to_18",
                    "interpretation_method": "IAP 2015 Adult-equivalent 23/27 cutoffs"
                }

        # Determine Primary Concern
        if not result["height_assessment"] and not result["weight_assessment"] and not result["bmi_assessment"]:
            result["status"] = "incomplete_inputs"
            result["calculation_status"] = "DATA_INSUFFICIENT"
            result["primary_concern"] = "Unable to calculate — measurements could not be evaluated"
            result["clinical_status"] = "UNABLE_TO_ASSESS"
        elif result["is_obese"]:
            result["primary_concern"] = "Pediatric Obesity (IAP 2015 27 kg/m² adult-equivalent)"
            result["clinical_status"] = "CONCERN_OBESITY"
        elif result["is_overweight"]:
            result["primary_concern"] = "Pediatric Overweight (IAP 2015 23 kg/m² adult-equivalent)"
            result["clinical_status"] = "CONCERN_OVERWEIGHT"
        elif result["is_stunted"]:
            result["primary_concern"] = "Stunting / Short Stature (IAP 2015)"
            result["clinical_status"] = "CONCERN_STUNTING"
        elif result["is_underweight"]:
            result["primary_concern"] = "Underweight (IAP 2015)"
            result["clinical_status"] = "CONCERN_UNDERWEIGHT"
        elif result["bmi_assessment"] and "thinness" in result["bmi_assessment"]["interpretation"].lower():
            result["primary_concern"] = "Thinness / Low BMI (IAP 2015)"
            result["clinical_status"] = "CONCERN_THINNESS"
        else:
            result["primary_concern"] = "No current screening concern"
            result["clinical_status"] = "NORMAL"

        return result

        return result
