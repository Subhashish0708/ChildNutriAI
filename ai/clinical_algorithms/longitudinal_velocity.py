"""
=============================================================================
Longitudinal Growth-Velocity & Early-Warning Degradation Engine
=============================================================================
Academic Reference:
  World Health Organization. WHO Child Growth Standards: Growth velocity based
  on weight, length and head circumference: Methods and development.
  Geneva: World Health Organization; 2009.

Methodology:
  Analyzes chronological sequential assessments to compute true growth velocity
  based on elapsed time between assessments:
    • Weight Velocity: g/day, kg/month
    • Height/Length Velocity: cm/month
    • MUAC Delta: mm/month
    • Trajectory Classification: Rapid weight loss, growth faltering,
      steady progression, or catch-up recovery.

Insufficient History Boundary:
  If fewer than 2 valid assessments exist, the engine explicitly returns
  status="insufficient_history" and refuses to compute or display synthetic velocities.

Medical Safety Boundary:
  Growth trajectory analysis is a clinical decision-support indicator.
  It does not diagnose underlying chronic pathologies or medical conditions.
=============================================================================
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional

class LongitudinalGrowthVelocityEngine:
    """
    Computes delta-velocity metrics between consecutive clinical assessments.
    Handles irregular intervals based on actual calendar elapsed time.
    """

    @staticmethod
    def parse_date(d_val: Any) -> Optional[date]:
        """Parses diverse date formats into a datetime.date object."""
        if isinstance(d_val, date) and not isinstance(d_val, datetime):
            return d_val
        if isinstance(d_val, datetime):
            return d_val.date()
        if isinstance(d_val, str):
            s = d_val.strip()
            # Try ISO format first
            for fmt in [
                "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"
            ]:
                try:
                    return datetime.strptime(s[:19], fmt).date()
                except ValueError:
                    pass
        return None

    @classmethod
    def analyze_growth_history(cls, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes list of historical assessment dicts and computes velocity trends
        between the most recent two chronological assessments.
        """
        # ---------------------------------------------------------------------
        # 1. INSUFFICIENT HISTORY CHECK (< 2 assessments)
        # ---------------------------------------------------------------------
        if not assessments or len(assessments) < 2:
            return {
                "status": "insufficient_history",
                "velocity_status": "insufficient_history",
                "trajectory": "Insufficient history (< 2 assessments)",
                "trend_points": len(assessments) if assessments else 0,
                "weight_velocity_g_day": None,
                "weight_velocity_kg_month": None,
                "height_velocity_cm_month": None,
                "delta_muac_mm": None,
                "days_between_checks": None,
                "early_warning_alert": False,
                "growth_warning": False,
                "alert_level": "None",
                "clinical_reason": (
                    "Insufficient longitudinal history to establish growth velocity. "
                    "At least two chronological assessments are required."
                ),
                "disclaimer": "Longitudinal velocity requires minimum 2 documented visits."
            }

        # ---------------------------------------------------------------------
        # 2. CHRONOLOGICAL SORTING BY DATE & AGE
        # ---------------------------------------------------------------------
        valid_records = []
        for a in assessments:
            if not isinstance(a, dict):
                continue
            d = cls.parse_date(a.get("assessment_date") or a.get("date"))
            age_m = float(a.get("age_months") or 0.0)
            wt = float(a.get("weight") or a.get("weight_kg") or 0.0)
            ht = float(a.get("height") or a.get("height_cm") or 0.0)
            if wt > 0 and ht > 0:
                valid_records.append({
                    "date": d,
                    "age_months": age_m,
                    "weight": wt,
                    "height": ht,
                    "muac": float(a.get("muac") or a.get("muac_cm")) if (a.get("muac") or a.get("muac_cm")) is not None else None
                })

        if len(valid_records) < 2:
            return {
                "status": "insufficient_history",
                "velocity_status": "insufficient_history",
                "trajectory": "Insufficient history (< 2 valid assessments)",
                "trend_points": len(valid_records),
                "weight_velocity_g_day": None,
                "weight_velocity_kg_month": None,
                "height_velocity_cm_month": None,
                "delta_muac_mm": None,
                "days_between_checks": None,
                "early_warning_alert": False,
                "growth_warning": False,
                "alert_level": "None",
                "clinical_reason": "Insufficient valid anthropometric records to calculate growth velocity.",
                "disclaimer": "Longitudinal velocity requires minimum 2 documented visits."
            }

        # Sort chronologically by date if available, else by age_months
        sorted_records = sorted(
            valid_records,
            key=lambda x: (x["date"] if x["date"] is not None else date.min, x["age_months"])
        )

        prev = sorted_records[-2]
        curr = sorted_records[-1]

        # ---------------------------------------------------------------------
        # 3. ACTUAL TIME INTERVAL CALCULATION
        # ---------------------------------------------------------------------
        if prev["date"] is not None and curr["date"] is not None and curr["date"] > prev["date"]:
            days = max(1, (curr["date"] - prev["date"]).days)
        else:
            # Fall back to difference in age in months converted to days
            age_delta_months = max(0.25, curr["age_months"] - prev["age_months"])
            days = max(7, int(age_delta_months * 30.4375))

        months = max(0.25, days / 30.4375)

        # ---------------------------------------------------------------------
        # 4. MEASUREMENTS & VELOCITIES
        # ---------------------------------------------------------------------
        wt_prev, wt_curr = prev["weight"], curr["weight"]
        ht_prev, ht_curr = prev["height"], curr["height"]
        muac_prev, muac_curr = prev["muac"], curr["muac"]

        delta_wt_kg = wt_curr - wt_prev
        wt_velocity_g_day = (delta_wt_kg * 1000.0) / days
        wt_velocity_kg_month = delta_wt_kg / months

        delta_ht_cm = ht_curr - ht_prev
        ht_velocity_cm_month = delta_ht_cm / months

        delta_muac_mm = None
        if muac_prev is not None and muac_curr is not None:
            delta_muac_mm = (muac_curr - muac_prev) * 10.0

        # Minimum expected daily weight gain per WHO growth velocity tables:
        # Infants < 6m: ~20-25 g/day; 6-12m: ~12-15 g/day; > 12m: ~6-8 g/day
        curr_age = curr["age_months"]
        expected_g_day = 25.0 if curr_age < 6 else (15.0 if curr_age < 12 else 8.0)

        # ---------------------------------------------------------------------
        # 5. CLINICAL TRAJECTORY CLASSIFICATION & DATA PLAUSIBILITY CHECKS
        # ---------------------------------------------------------------------
        growth_warning = False
        data_quality_warning = False
        velocity_status = "Calculated"
        alert_level = "Green: Normal"
        status = "available"

        # Check 5a: Assessment interval too short (< 7 days)
        if days < 7:
            data_quality_warning = True
            status = "unreliable_interval"
            trajectory = "Unreliable Trajectory (Interval < 7 Days)"
            if abs(wt_velocity_g_day) > 100.0 or abs(delta_wt_kg) > 1.0:
                growth_warning = True
                velocity_status = "Biologically Implausible / Verification Required"
                alert_level = "Orange: Data Quality Warning"
                clinical_reason = (
                    f"Assessment interval is only {days} day(s) with recorded weight change of {delta_wt_kg:+.2f} kg "
                    f"({wt_velocity_g_day:+.1f} g/day), which exceeds biological plausibility thresholds (> 100 g/day). "
                    f"Growth velocity cannot be calculated reliably. Physical re-measurement recommended to rule out clerical error."
                )
            else:
                alert_level = "Amber: Data Quality Warning"
                velocity_status = "Unreliable: Interval Too Short (< 7 days)"
                clinical_reason = (
                    f"Assessment interval is only {days} day(s). Reliable pediatric growth velocity "
                    f"requires at least 7–14 days between anthropometric evaluations to reflect genuine "
                    f"somatic tissue accretion rather than acute fluid fluctuation or measurement variation."
                )
        # Check 5b: Biological implausibility (> 100 g/day or > 2.5 kg gain in < 30 days)
        elif wt_velocity_g_day > 100.0 or (delta_wt_kg > 2.5 and days < 30):
            data_quality_warning = True
            growth_warning = True
            velocity_status = "Biologically Implausible / Verification Required"
            status = "biologically_implausible"
            trajectory = "Implausible Velocity (Requires Verification)"
            alert_level = "Orange: Data Quality Warning"
            clinical_reason = (
                f"Recorded weight change of {delta_wt_kg:+.2f} kg across {days} days "
                f"({wt_velocity_g_day:+.1f} g/day) exceeds biological plausibility thresholds (> 100 g/day). "
                f"Possible cause: measurement scale discrepancy, clerical entry error, or acute fluid accumulation (edema). "
                f"Physical re-measurement recommended before clinical decision-making."
            )
        # Check 5c: Extreme acute weight loss
        elif wt_velocity_g_day < -150.0 or (delta_wt_kg < -2.0 and days < 14):
            data_quality_warning = True
            growth_warning = True
            velocity_status = "Severe Acute Loss / Verification Required"
            status = "biologically_implausible"
            trajectory = "Extreme Weight Loss (Requires Urgent Verification)"
            alert_level = "Red: Rapid Weight Loss"
            clinical_reason = (
                f"Severe acute weight change of {delta_wt_kg:+.2f} kg across {days} days "
                f"({wt_velocity_g_day:+.1f} g/day). Rule out severe dehydration or clerical error; "
                f"urgent clinical verification required."
            )
        elif delta_wt_kg < -0.20:
            # Rapid active weight loss (> 200g loss)
            growth_warning = True
            alert_level = "Red: Rapid Weight Loss"
            trajectory = "Sinking / Acute Degradation"
            clinical_reason = (
                f"Concerning growth trajectory - clinical review recommended. "
                f"Child lost {abs(delta_wt_kg):.2f} kg across {days} days ({wt_velocity_g_day:.1f} g/day). "
                f"Investigate potential acute illness, diarrhea, or acute food deprivation."
            )
        elif delta_wt_kg <= 0.05 and days >= 25:
            # Weight stagnation / flattening growth curve
            growth_warning = True
            alert_level = "Orange: Growth Faltering"
            trajectory = "Flattening / Growth Stagnation"
            clinical_reason = (
                f"Concerning growth trajectory - clinical review recommended. "
                f"Weight is flat across {days} days (gain <= 50g; weight stagnation detected). "
                f"Early growth faltering detected prior to visible clinical wasting."
            )
        elif wt_velocity_g_day >= expected_g_day * 1.5:
            # Accelerated positive recovery
            trajectory = "Catch-up Growth (Accelerated Recovery)"
            alert_level = "Green: Robust Catch-up"
            clinical_reason = (
                f"Growth velocity reflects robust positive catch-up trajectory "
                f"({wt_velocity_g_day:.1f} g/day vs standard {expected_g_day:.0f} g/day)."
            )
        else:
            # Standard trajectory
            trajectory = "Steady Growth (On Track)"
            alert_level = "Green: Normal"
            clinical_reason = (
                f"Growth velocity aligns with standard pediatric trajectory "
                f"({wt_velocity_g_day:.1f} g/day)."
            )

        return {
            "status": status,
            "velocity_status": velocity_status,
            "trajectory": trajectory,
            "trend_points": len(sorted_records),
            "weight_velocity_g_day": round(wt_velocity_g_day, 1),
            "weight_velocity_kg_month": round(wt_velocity_kg_month, 2),
            "height_velocity_cm_month": round(ht_velocity_cm_month, 2),
            "delta_weight_kg": round(delta_wt_kg, 2),
            "delta_height_cm": round(delta_ht_cm, 1),
            "delta_muac_mm": round(delta_muac_mm, 1) if delta_muac_mm is not None else None,
            "days_between_checks": days,
            "expected_gain_g_day": expected_g_day,
            "early_warning_alert": growth_warning,
            "growth_warning": growth_warning,
            "data_quality_warning": data_quality_warning,
            "alert_level": alert_level,
            "clinical_reason": clinical_reason,
            "safety_boundary": "Trajectory analysis is a decision-support indicator, non-diagnostic."
        }

if __name__ == "__main__":
    eng = LongitudinalGrowthVelocityEngine()
    history = [
        {"assessment_date": "2026-06-15", "age_months": 12.0, "weight": 7.0, "height": 66.0, "muac": 12.2},
        {"assessment_date": "2026-07-20", "age_months": 13.0, "weight": 7.1, "height": 67.5, "muac": 12.3}
    ]
    res = eng.analyze_growth_history(history)
    print("Longitudinal Analysis:")
    for k, v in res.items():
        print(f"  {k:<26}: {v}")
