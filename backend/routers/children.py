"""
Child Profile & Growth History Endpoints.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Child, User, Assessment
from backend.schemas import ChildCreate, ChildUpdate, ChildResponse, GrowthPointResponse, AssessmentResponse
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/children", tags=["Children"])


def format_child_response(child: Child) -> ChildResponse:
    latest = child.assessments[0] if child.assessments else None
    latest_resp = AssessmentResponse.model_validate(latest) if latest else None
    resp = ChildResponse.model_validate(child)
    resp.latest_assessment = latest_resp
    return resp


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    payload: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new child profile."""
    # Generate unique Health ID if not provided
    health_id = payload.health_id or f"CHN-2026-{uuid.uuid4().hex[:5].upper()}"
    
    # Duplicate Health ID check
    if db.query(Child).filter(Child.health_id == health_id).first():
        health_id = f"CHN-2026-{uuid.uuid4().hex[:5].upper()}"

    parent_id = payload.parent_id
    if current_user.role == "parent":
        parent_id = current_user.id

    new_child = Child(
        health_id=health_id,
        parent_id=parent_id,
        name=payload.name.strip(),
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        birth_weight=payload.birth_weight,
        birth_length=payload.birth_length
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)
    return format_child_response(new_child)


@router.get("", response_model=List[ChildResponse])
def list_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns children accessible to the current user.
    Parents see only their own children; Health Workers see all.
    """
    if current_user.role == "parent":
        children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    else:
        children = db.query(Child).all()
    
    return [format_child_response(c) for c in children]


@router.get("/{child_id}", response_model=ChildResponse)
def get_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full child profile."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found.")
    check_child_access(child, current_user)
    return format_child_response(child)


@router.put("/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: int,
    payload: ChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update child information."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found.")
    check_child_access(child, current_user)

    if payload.name:
        child.name = payload.name.strip()
    if payload.date_of_birth:
        child.date_of_birth = payload.date_of_birth
    if payload.gender:
        child.gender = payload.gender
    if payload.birth_weight is not None:
        child.birth_weight = payload.birth_weight
    if payload.birth_length is not None:
        child.birth_length = payload.birth_length
    if payload.parent_id and current_user.role != "parent":
        child.parent_id = payload.parent_id

    db.commit()
    db.refresh(child)
    return format_child_response(child)


@router.delete("/{child_id}")
def delete_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete child and associated data (only health workers/admins)."""
    if current_user.role == "parent":
        raise HTTPException(status_code=403, detail="Parents cannot delete child records.")
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found.")
    db.delete(child)
    db.commit()
    return {"message": "Child record deleted successfully."}


@router.get("/{child_id}/growth", response_model=List[GrowthPointResponse])
def get_growth_history(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns chronological growth history (date, weight, height, MUAC, head_circ, risk)
    for rendering Growth Tracker charts.
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found.")
    check_child_access(child, current_user)

    assessments = (
        db.query(Assessment)
        .filter(Assessment.child_id == child_id)
        .order_by(Assessment.assessment_date.asc())
        .all()
    )

    points = []
    for a in assessments:
        points.append(GrowthPointResponse(
            date=a.assessment_date,
            age_months=a.age_months,
            weight=a.weight,
            height=a.height,
            muac=a.muac,
            head_circumference=a.head_circumference,
            prediction=a.prediction.prediction if a.prediction else None,
            risk_score=a.prediction.risk_score if a.prediction else None
        ))
    return points
