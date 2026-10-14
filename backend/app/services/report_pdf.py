"""
ChildNutri AI — PDF Report Generator (ReportLab)
"""
from __future__ import annotations
import io
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


# Colour palette
C_GREEN = HexColor("#34d399") if HAS_REPORTLAB else None
C_AMBER = HexColor("#fbbf24") if HAS_REPORTLAB else None
C_RED = HexColor("#f87171") if HAS_REPORTLAB else None
C_DARK = HexColor("#0f1e1a") if HAS_REPORTLAB else None
C_LIGHT = HexColor("#f4faf8") if HAS_REPORTLAB else None
C_GREY = HexColor("#64748b") if HAS_REPORTLAB else None


def _status_color(severity: str):
    m = {"normal": C_GREEN, "moderate": C_AMBER, "severe": C_RED, "critical": C_RED}
    return m.get(severity, C_GREY)


def generate_pdf_report(
    child_name: str,
    child_dob: str,
    child_sex: str,
    assessment_date: str,
    result: dict,
) -> bytes:
    """Generate a PDF report for one assessment. Returns raw bytes."""
    if not HAS_REPORTLAB:
        return b"PDF generation not available. Install reportlab."

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=20 * mm, rightMargin=20 * mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=20,
                                  textColor=C_DARK, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                         textColor=C_DARK, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10,
                           leading=14, spaceAfter=4)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8,
                            textColor=C_GREY, leading=12)

    elements = []

    # Header
    elements.append(Paragraph("🌿 ChildNutri AI — Assessment Report", title_style))
    elements.append(HRFlowable(color=C_GREEN, thickness=2, width="100%"))
    elements.append(Spacer(1, 4 * mm))

    # Child info table
    status_now = result.get("status_now", {})
    future = result.get("future_risk", {})
    zscores = result.get("zscores", {})

    info_data = [
        ["Child Name:", child_name, "Assessment Date:", assessment_date],
        ["Date of Birth:", child_dob, "Sex:", child_sex],
        ["Age at Assessment:", f"{result.get('age_months', 0):.1f} months",
         "Data Confidence:", result.get("data_confidence", "—")],
    ]
    info_table = Table(info_data, colWidths=[45 * mm, 55 * mm, 45 * mm, 55 * mm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), C_GREY),
        ("TEXTCOLOR", (2, 0), (2, -1), C_GREY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Verdict NOW ──────────────────────────────────────────────────────────
    elements.append(Paragraph("Current Nutritional Status", h2))
    headline = status_now.get("headline", "—")
    severity = status_now.get("severity", "normal")
    verdict_color = _status_color(severity)

    verdict_style = ParagraphStyle("Verdict", parent=styles["Normal"], fontSize=14,
                                    fontName="Helvetica-Bold", textColor=verdict_color)
    elements.append(Paragraph(f"▶  {headline}", verdict_style))
    elements.append(Spacer(1, 3 * mm))

    # Z-scores
    z_data = [["Indicator", "Z-Score", "Interpretation"]]
    for key, label in [("waz", "Weight-for-Age (WAZ)"), ("haz", "Height-for-Age (HAZ)"),
                        ("whz", "Weight-for-Height (WHZ)")]:
        z = zscores.get(key)
        if z is not None:
            interp = "Healthy" if z > -2 else ("Moderate concern" if z > -3 else "Severe concern")
            z_data.append([label, f"{z:.2f}", interp])

    if muac := result.get("zscores", {}).get("muac_z"):
        z_data.append(["MUAC Z-score", f"{muac:.2f}", ""])

    z_table = Table(z_data, colWidths=[80 * mm, 40 * mm, 70 * mm])
    z_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f0fdf4"), HexColor("#ffffff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#d1d5db")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(z_table)
    elements.append(Spacer(1, 5 * mm))

    # Explanations
    for expl in status_now.get("explanation", {}).values():
        elements.append(Paragraph(f"• {expl}", body))

    if status_now.get("red_flag_hospital"):
        elements.append(Spacer(1, 3 * mm))
        red_style = ParagraphStyle("Red", parent=styles["Normal"], fontSize=11,
                                    fontName="Helvetica-Bold", textColor=C_RED)
        elements.append(Paragraph("⚠ URGENT: Please take this child to a hospital or NRC immediately.", red_style))

    elements.append(Spacer(1, 6 * mm))

    # ── Future Risk ──────────────────────────────────────────────────────────
    elements.append(Paragraph("Future Risk Assessment", h2))
    tier = future.get("tier", "LOW")
    tier_color = {"LOW": C_GREEN, "WATCH": C_AMBER, "HIGH": C_RED}.get(tier, C_GREY)
    tier_style = ParagraphStyle("Tier", parent=styles["Normal"], fontSize=12,
                                 fontName="Helvetica-Bold", textColor=tier_color)
    elements.append(Paragraph(f"Risk Tier: {tier}  (Total Points: {future.get('total_points', 0)}/8)", tier_style))
    elements.append(Paragraph(f"Horizon: {future.get('horizon', '')}", small))
    elements.append(Spacer(1, 3 * mm))

    bp = future.get("breakdown", {})
    elements.append(Paragraph(
        f"Breakdown — Trend: {bp.get('trend', 0)} pts | Closeness to cut-off: {bp.get('closeness', 0)} pts | "
        f"Risk model: {bp.get('model', 0)} pts", body))

    for r in future.get("reasons", []):
        elements.append(Paragraph(f"• {r}", body))

    elements.append(Spacer(1, 6 * mm))

    # ── Diet Plan ────────────────────────────────────────────────────────────
    diet = result.get("diet_plan", {})
    if diet:
        elements.append(Paragraph("Diet & Care Plan", h2))

        sections = [
            ("What this means", diet.get("what_this_means", "")),
            ("How to feed", diet.get("how_to_feed", "")),
            ("Foods that help", "\n".join(f"• {f}" for f in diet.get("foods_that_help", []))),
            ("Foods to limit / avoid", "\n".join(f"• {f}" for f in diet.get("foods_to_limit", []))),
            ("Keep the child healthy", diet.get("keep_healthy", "")),
            ("Ask your doctor about", diet.get("ask_doctor", "")),
            ("Government help available", diet.get("government_help", "")),
            ("Follow-up schedule", diet.get("follow_up", "")),
        ]

        for sec_title, sec_body in sections:
            if sec_body:
                sec_style = ParagraphStyle("SecTitle", parent=styles["Normal"], fontSize=10,
                                            fontName="Helvetica-Bold", textColor=C_DARK, spaceBefore=5)
                elements.append(Paragraph(sec_title, sec_style))
                elements.append(Paragraph(sec_body.replace("\n", "<br/>"), body))

        # Red flags
        red_flags = diet.get("red_flags", [])
        if red_flags:
            elements.append(Spacer(1, 3 * mm))
            rf_title = ParagraphStyle("RFTitle", parent=styles["Normal"], fontSize=10,
                                       fontName="Helvetica-Bold", textColor=C_RED)
            elements.append(Paragraph("🚨 Red Flags — Go to hospital now if you notice:", rf_title))
            for rf in red_flags:
                elements.append(Paragraph(f"• {rf}", body))

    elements.append(Spacer(1, 8 * mm))

    # Disclaimer
    disc_style = ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8,
                                 textColor=C_GREY, leading=11)
    elements.append(HRFlowable(color=C_GREY, thickness=0.5, width="100%"))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        "ChildNutri AI is a screening and education tool. It does not diagnose illness and does not replace a doctor, "
        "nurse, or Anganwadi worker. Generated by ChildNutri AI © 2026.", disc_style))

    doc.build(elements)
    return buf.getvalue()
