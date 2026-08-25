"""
Medical History & Clinic Visit Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import MedicalHistory, Child, User
from backend.schemas import MedicalCreate, MedicalUpdate, MedicalResponse
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/medical", tags=["Medical History"])


@router.post("", response_model=MedicalResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    payload: MedicalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a medical history / clinic visit record."""
    child = db.query(Child).filter(Child.id == payload.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    record = MedicalHistory(
        child_id=payload.child_id,
        doctor_name=payload.doctor_name.strip(),
        visit_date=payload.visit_date,
        diagnosis=payload.diagnosis.strip(),
        treatment=payload.treatment.strip() if payload.treatment else None,
        notes=payload.notes.strip() if payload.notes else None
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/child/{child_id}", response_model=List[MedicalResponse])
def get_child_medical_history(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chronological medical visit records for a child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    return db.query(MedicalHistory).filter(MedicalHistory.child_id == child_id).order_by(MedicalHistory.visit_date.desc()).all()


@router.put("/{record_id}", response_model=MedicalResponse)
def update_medical_record(
    record_id: int,
    payload: MedicalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update medical history record."""
    record = db.query(MedicalHistory).filter(MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    check_child_access(record.child, current_user)

    if payload.doctor_name:
        record.doctor_name = payload.doctor_name.strip()
    if payload.visit_date:
        record.visit_date = payload.visit_date
    if payload.diagnosis:
        record.diagnosis = payload.diagnosis.strip()
    if payload.treatment is not None:
        record.treatment = payload.treatment.strip()
    if payload.notes is not None:
        record.notes = payload.notes.strip()

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}")
def delete_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a medical record."""
    record = db.query(MedicalHistory).filter(MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    check_child_access(record.child, current_user)

    db.delete(record)
    db.commit()
    return {"message": "Medical record deleted successfully."}
