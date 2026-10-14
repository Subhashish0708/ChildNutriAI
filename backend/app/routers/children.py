"""Children router — CRUD for child profiles"""
import uuid
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, Child
from backend.app.schemas import ChildCreate, ChildOut
from backend.app.deps import get_current_user

router = APIRouter(prefix="/api/children", tags=["children"])


def _compute_age_months(dob: date) -> float:
    from datetime import date as d
    today = d.today()
    return round(((today - dob).days) / 30.4375, 1)


@router.post("", response_model=ChildOut, status_code=201)
def create_child(body: ChildCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    hid = f"CN{uuid.uuid4().hex[:8].upper()}"
    child = Child(
        health_id=hid,
        parent_id=user.id,
        name=body.name,
        date_of_birth=body.date_of_birth,
        sex=body.sex,
        birth_weight_kg=body.birth_weight_kg,
        birth_length_cm=body.birth_length_cm,
        birth_order=body.birth_order,
        state_region=body.state_region,
        area_type=body.area_type,
        observations=body.observations,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


@router.get("", response_model=List[ChildOut])
def list_children(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Child).filter(Child.parent_id == user.id).all()


@router.get("/{child_id}", response_model=ChildOut)
def get_child(child_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    child = _get_owned(child_id, user, db)
    return child


@router.put("/{child_id}", response_model=ChildOut)
def update_child(child_id: int, body: ChildCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    child = _get_owned(child_id, user, db)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(child, k, v)
    db.commit()
    db.refresh(child)
    return child


@router.delete("/{child_id}", status_code=204)
def delete_child(child_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    child = _get_owned(child_id, user, db)
    db.delete(child)
    db.commit()


def _get_owned(child_id: int, user: User, db: Session) -> Child:
    child = db.get(Child, child_id)
    if not child:
        raise HTTPException(404, "Child not found")
    # Health workers can see all; parents only their own
    if user.role == "parent" and child.parent_id != user.id:
        raise HTTPException(403, "Access denied")
    return child
