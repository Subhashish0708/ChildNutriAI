"""
Nutrition & Dietary Plan Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import NutritionPlan, Child, User
from backend.schemas import NutritionCreate, NutritionUpdate, NutritionResponse
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/nutrition", tags=["Nutrition Plans"])


@router.post("", response_model=NutritionResponse, status_code=status.HTTP_201_CREATED)
def create_nutrition_plan(
    payload: NutritionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a nutrition plan for a child."""
    child = db.query(Child).filter(Child.id == payload.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    plan = NutritionPlan(
        child_id=payload.child_id,
        created_by=current_user.id,
        plan_title=payload.plan_title.strip(),
        description=payload.description.strip() if payload.description else None,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/child/{child_id}", response_model=List[NutritionResponse])
def get_child_nutrition_plans(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve nutrition plans for a child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    return db.query(NutritionPlan).filter(NutritionPlan.child_id == child_id).order_by(NutritionPlan.created_at.desc()).all()


@router.put("/{plan_id}", response_model=NutritionResponse)
def update_nutrition_plan(
    plan_id: int,
    payload: NutritionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a nutrition plan."""
    plan = db.query(NutritionPlan).filter(NutritionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Nutrition plan not found.")
    check_child_access(plan.child, current_user)

    if payload.plan_title:
        plan.plan_title = payload.plan_title.strip()
    if payload.description is not None:
        plan.description = payload.description.strip()
    if payload.start_date:
        plan.start_date = payload.start_date
    if payload.end_date:
        plan.end_date = payload.end_date

    db.commit()
    db.refresh(plan)
    return plan
