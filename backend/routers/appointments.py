"""
Appointment Scheduling & Follow-Up Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Appointment, Child, User
from backend.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from backend.dependencies import get_current_user, check_child_access

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def schedule_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a new check-up / follow-up appointment."""
    child = db.query(Child).filter(Child.id == payload.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    appt = Appointment(
        child_id=payload.child_id,
        health_worker_id=payload.health_worker_id or (current_user.id if current_user.role != "parent" else None),
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time or "10:00 AM",
        purpose=payload.purpose.strip(),
        notes=payload.notes.strip() if payload.notes else None,
        status="upcoming"
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.get("", response_model=List[AppointmentResponse])
def get_all_appointments(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List appointments. Health workers see all, Parents see only their children's appointments.
    """
    query = db.query(Appointment)
    if current_user.role == "parent":
        query = query.join(Child).filter(Child.parent_id == current_user.id)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    return query.order_by(Appointment.appointment_date.asc()).all()


@router.get("/child/{child_id}", response_model=List[AppointmentResponse])
def get_child_appointments(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all appointments for a specific child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found.")
    check_child_access(child, current_user)

    return db.query(Appointment).filter(Appointment.child_id == child_id).order_by(Appointment.appointment_date.asc()).all()


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update appointment status (e.g., mark completed) or reschedule."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    check_child_access(appt.child, current_user)

    if payload.appointment_date:
        appt.appointment_date = payload.appointment_date
    if payload.appointment_time:
        appt.appointment_time = payload.appointment_time
    if payload.purpose:
        appt.purpose = payload.purpose
    if payload.status:
        appt.status = payload.status
    if payload.notes is not None:
        appt.notes = payload.notes

    db.commit()
    db.refresh(appt)
    return appt
