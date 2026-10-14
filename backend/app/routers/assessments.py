"""Assessments router — run pipeline, list, get, PDF download"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.app.database import get_db
from backend.app.models import User, Child, Assessment, Measurement, Photo, Report
from backend.app.schemas import AssessmentCreate, AssessmentOut
from backend.app.deps import get_current_user
from backend.app.services.pipeline import run_assessment_pipeline, compute_age_months
from backend.app.services.report_pdf import generate_pdf_report
from backend.app.routers.children import _get_owned

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(body: AssessmentCreate, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    child = _get_owned(body.child_id, user, db)

    # Build growth history from prior assessments for trend analysis
    history = []
    for prior in child.assessments:
        if prior.result_json:
            zs = prior.result_json.get("zscores", {})
            history.append({
                "measurement_date": str(prior.measurement_date),
                "waz": zs.get("waz"),
                "haz": zs.get("haz"),
                "whz": zs.get("whz"),
            })

    # Extract sub-objects
    m = body.measurement
    f = body.feeding or {}
    h = body.health or {}
    ho = body.home or {}

    # Feeding dict handling
    def _f(obj, key, default=None):
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    result = run_assessment_pipeline(
        sex=child.sex,
        dob=child.date_of_birth,
        measurement_date=body.measurement_date,
        weight_kg=m.weight_kg,
        height_cm=m.height_cm,
        muac_cm=m.muac_cm,
        head_circ_cm=m.head_circ_cm,
        bilateral_edema=m.bilateral_edema,
        measured_lying=None,
        food_groups_yesterday=_f(f, "food_groups_yesterday"),
        meals_per_day=_f(f, "meals_per_day"),
        breastfed=_f(f, "breastfed"),
        appetite=_f(f, "appetite"),
        diarrhoea_2w=_f(h, "diarrhoea_2w"),
        fever_2w=_f(h, "fever_2w"),
        vaccination_status=_f(h, "vaccination_status"),
        known_illness=_f(h, "known_illness"),
        food_allergy=_f(h, "food_allergy"),
        mother_education=_f(ho, "mother_education"),
        mother_age=_f(ho, "mother_age"),
        wealth_score=_f(ho, "wealth_score"),
        rural_urban=_f(ho, "rural_urban"),
        water_source=_f(ho, "water_source"),
        toilet_type=_f(ho, "toilet_type"),
        veg_only=_f(ho, "food_preference") == "veg",
        growth_history=history,
        photo_screening_result=body.photo_screening_result,
    )

    age_months = compute_age_months(child.date_of_birth, body.measurement_date)

    # Save to DB
    assessment = Assessment(
        child_id=child.id,
        conducted_by=user.id,
        measurement_date=body.measurement_date,
        age_months=age_months,
        inputs_json=body.model_dump(mode="json"),
        result_json=result,
        status_now=result["status_now"]["headline"],
        tier_future=result["future_risk"]["tier"],
        data_confidence=result["data_confidence"],
        model_versions=result["model_versions"],
    )
    db.add(assessment)
    db.flush()

    meas = Measurement(
        assessment_id=assessment.id,
        weight_kg=m.weight_kg,
        height_cm=m.height_cm,
        muac_cm=m.muac_cm,
        head_circ_cm=m.head_circ_cm,
        bilateral_edema=m.bilateral_edema,
        how_measured=m.how_measured,
    )
    db.add(meas)

    if body.photo_id:
        photo = db.get(Photo, body.photo_id)
        if photo:
            photo.assessment_id = assessment.id

    if body.report_id:
        report = db.get(Report, body.report_id)
        if report:
            report.assessment_id = assessment.id

    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/child/{child_id}/history")
def get_child_history(child_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """Return lightweight growth history for chart rendering."""
    child = _get_owned(child_id, user, db)
    history = []
    for a in child.assessments:
        if a.result_json:
            zs = a.result_json.get("zscores", {})
            history.append({
                "id": a.id,
                "date": str(a.measurement_date),
                "age_months": a.age_months,
                "status": a.status_now,
                "tier": a.tier_future,
                "waz": zs.get("waz"),
                "haz": zs.get("haz"),
                "whz": zs.get("whz"),
                "weight_kg": a.measurements.weight_kg if a.measurements else None,
                "height_cm": a.measurements.height_cm if a.measurements else None,
                "muac_cm": a.measurements.muac_cm if a.measurements else None,
            })
    return history


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    a = db.get(Assessment, assessment_id)
    if not a:
        raise HTTPException(404, "Assessment not found")
    _get_owned(a.child_id, user, db)
    return a


@router.get("/{assessment_id}/pdf")
def download_pdf(assessment_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    a = db.get(Assessment, assessment_id)
    if not a:
        raise HTTPException(404, "Assessment not found")
    child = _get_owned(a.child_id, user, db)

    pdf_bytes = generate_pdf_report(
        child_name=child.name,
        child_dob=str(child.date_of_birth),
        child_sex=child.sex,
        assessment_date=str(a.measurement_date),
        result=a.result_json or {},
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ChildNutriAI_Report_{assessment_id}.pdf"'},
    )
