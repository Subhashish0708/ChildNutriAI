"""
Assessment & AI Inference Pipeline Endpoints.
Accepts raw anthropometric data, executes AI prediction, creates historical records,
and triggers notifications when high risk is detected.
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Assessment, Prediction, Child, User, Notification
from backend.schemas import AssessmentCreate, AssessmentResponse
from backend.services.ai_service import predict_malnutrition
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Conduct new assessment:
    1. Verify child exists and check access
    2. Save raw anthropometric measurement in assessments table
    3. Call AI prediction service
    4. Save AI inference in predictions table
    5. Generate automatic alert/notification if risk is high
    """
    child = db.query(Child).filter(Child.id == payload.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    # 1. Save raw assessment
    new_assessment = Assessment(
        child_id=child.id,
        health_worker_id=current_user.id if current_user.role != "parent" else None,
        assessment_date=payload.assessment_date or date.today(),
        age_months=payload.age_months,
        weight=payload.weight,
        height=payload.height,
        muac=payload.muac,
        head_circumference=payload.head_circumference,
        notes=payload.notes
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    # 2. Call AI service
    ai_input = {
        "age_months": payload.age_months,
        "gender": child.gender,
        "weight": payload.weight,
        "height": payload.height,
        "muac": payload.muac,
        "head_circumference": payload.head_circumference
    }
    ai_result = predict_malnutrition(ai_input)

    # 3. Store prediction
    pred = Prediction(
        assessment_id=new_assessment.id,
        model_name=ai_result.get("model_name", "ChildNutri Anthropometric Model v1"),
        prediction=ai_result.get("prediction", "Normal"),
        risk_score=ai_result.get("risk_score", 0.0),
        confidence=ai_result.get("confidence", 0.9)
    )
    db.add(pred)

    # 4. Trigger alert notification if high risk (risk_score >= 65)
    if pred.risk_score >= 65:
        # Notify parent
        if child.parent_id:
            notif_parent = Notification(
                user_id=child.parent_id,
                title=f"Urgent AI Alert for {child.name}",
                message=f"Assessment on {new_assessment.assessment_date} detected {pred.prediction} (Risk Score: {pred.risk_score}%). Please visit the health center.",
                type="alert"
            )
            db.add(notif_parent)
        
        # Notify health worker
        if current_user.role == "health_worker":
            notif_hw = Notification(
                user_id=current_user.id,
                title=f"High Risk Flag: {child.name}",
                message=f"{child.name} flagged with {pred.prediction} ({pred.risk_score}% risk). Follow-up recommended.",
                type="alert"
            )
            db.add(notif_hw)

    db.commit()
    db.refresh(new_assessment)
    return new_assessment


@router.get("/recent", response_model=List[AssessmentResponse])
def get_recent_assessments(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the most recent assessments across all authorized children."""
    if current_user.role == "parent":
        assessments = (
            db.query(Assessment)
            .join(Child)
            .filter(Child.parent_id == current_user.id)
            .order_by(Assessment.assessment_date.desc())
            .limit(limit)
            .all()
        )
    else:
        assessments = (
            db.query(Assessment)
            .order_by(Assessment.assessment_date.desc())
            .limit(limit)
            .all()
        )
    return assessments


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single assessment with its AI prediction."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    check_child_access(assessment.child, current_user)
    return assessment


@router.get("/child/{child_id}", response_model=List[AssessmentResponse])
def get_child_assessments(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full assessment history for a specific child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)
    
    return child.assessments
