"""
User Management and Dashboard Analytics Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.database import get_db
from backend.models import User, Child, Assessment, Prediction, Appointment
from backend.schemas import UserResponse, UserUpdate, HealthWorkerStats
from backend.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/users", tags=["Users & Stats"])


@router.get("/stats", response_model=HealthWorkerStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["health_worker", "admin"]))
):
    """
    Computes live dashboard statistics from SQLite for the Health Worker dashboard.
    """
    total_children = db.query(Child).count()
    
    # Latest assessment per child to evaluate current risk
    latest_assessments = (
        db.query(Assessment)
        .order_by(Assessment.child_id, Assessment.assessment_date.desc())
        .all()
    )
    
    # Count distinct latest assessment results
    seen_children = set()
    normal_count = 0
    at_risk_count = 0
    status_counts = {"Normal": 0, "Stunted": 0, "Wasted": 0, "Severe SAM": 0, "Underweight": 0}
    
    for a in latest_assessments:
        if a.child_id in seen_children:
            continue
        seen_children.add(a.child_id)
        
        pred = a.prediction
        if pred:
            p_name = pred.prediction
            if p_name in ["Normal", "Healthy"]:
                normal_count += 1
                status_counts["Normal"] += 1
            else:
                at_risk_count += 1
                if "Severe" in p_name or "SAM" in p_name:
                    status_counts["Severe SAM"] += 1
                elif "Stunted" in p_name:
                    status_counts["Stunted"] += 1
                elif "Wasted" in p_name:
                    status_counts["Wasted"] += 1
                elif "Underweight" in p_name:
                    status_counts["Underweight"] += 1
                else:
                    status_counts["Stunted"] += 1
    
    # Children with no assessments default to normal count if total > assessed
    unassessed = total_children - len(seen_children)
    if unassessed > 0:
        normal_count += unassessed
        status_counts["Normal"] += unassessed

    # Upcoming follow-up appointments scheduled
    followups_scheduled = (
        db.query(Appointment)
        .filter(Appointment.status == "upcoming")
        .count()
    )

    # Recent assessments in the last 7 days
    seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
    recent_assessments_count = (
        db.query(Assessment)
        .filter(Assessment.assessment_date >= seven_days_ago)
        .count()
    )

    return HealthWorkerStats(
        total_children=total_children,
        at_risk_count=at_risk_count,
        normal_count=normal_count,
        followups_scheduled=followups_scheduled,
        status_distribution=status_counts,
        recent_assessments_count=recent_assessments_count
    )


@router.put("/me", response_model=UserResponse)
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile info."""
    if payload.full_name:
        current_user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone.strip()
    db.commit()
    db.refresh(current_user)
    return current_user
