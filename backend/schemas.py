"""
Pydantic schemas for request validation and response serialization.
Ensures strict type-checking and prevents sensitive fields (e.g., password_hash)
from leaking in API responses.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# -------------------------------------------------------------
# Auth & User Schemas
# -------------------------------------------------------------
class UserRegister(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str = Field(..., min_length=3, max_length=120)
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: Optional[str] = "parent"  # parent, health_worker, admin

    model_config = ConfigDict(extra="ignore")


class UserLogin(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


# -------------------------------------------------------------
# Prediction & Assessment Schemas
# -------------------------------------------------------------
class PredictionResponse(BaseModel):
    id: int
    assessment_id: int
    model_name: str
    prediction: str
    risk_score: float
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssessmentCreate(BaseModel):
    child_id: int
    age_months: float = Field(..., ge=0, le=72)
    weight: float = Field(..., gt=0, le=50)
    height: float = Field(..., gt=20, le=150)
    muac: Optional[float] = Field(None, ge=5, le=30)
    head_circumference: Optional[float] = Field(None, ge=20, le=60)
    assessment_date: Optional[date] = None
    notes: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: int
    child_id: int
    health_worker_id: Optional[int] = None
    assessment_date: date
    age_months: float
    weight: float
    height: float
    muac: Optional[float] = None
    head_circumference: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    prediction: Optional[PredictionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class GrowthPointResponse(BaseModel):
    date: date
    age_months: float
    weight: float
    height: float
    muac: Optional[float] = None
    head_circumference: Optional[float] = None
    prediction: Optional[str] = None
    risk_score: Optional[float] = None


# -------------------------------------------------------------
# Photo Schemas
# -------------------------------------------------------------
class PhotoResponse(BaseModel):
    id: int
    child_id: int
    assessment_id: Optional[int] = None
    photo_type: str
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Child Schemas
# -------------------------------------------------------------
class ChildCreate(BaseModel):
    health_id: Optional[str] = None
    parent_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    birth_weight: Optional[float] = None
    birth_length: Optional[float] = None


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    birth_weight: Optional[float] = None
    birth_length: Optional[float] = None


class ChildResponse(BaseModel):
    id: int
    health_id: str
    parent_id: Optional[int] = None
    name: str
    date_of_birth: date
    gender: str
    birth_weight: Optional[float] = None
    birth_length: Optional[float] = None
    created_at: datetime
    latest_assessment: Optional[AssessmentResponse] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Medical History Schemas
# -------------------------------------------------------------
class MedicalCreate(BaseModel):
    child_id: int
    doctor_name: str
    visit_date: date
    diagnosis: str
    treatment: Optional[str] = None
    notes: Optional[str] = None


class MedicalUpdate(BaseModel):
    doctor_name: Optional[str] = None
    visit_date: Optional[date] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None


class MedicalResponse(BaseModel):
    id: int
    child_id: int
    doctor_name: str
    visit_date: date
    diagnosis: str
    treatment: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Nutrition Plan Schemas
# -------------------------------------------------------------
class NutritionCreate(BaseModel):
    child_id: int
    plan_title: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class NutritionUpdate(BaseModel):
    plan_title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class NutritionResponse(BaseModel):
    id: int
    child_id: int
    created_by: Optional[int] = None
    plan_title: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Appointment Schemas
# -------------------------------------------------------------
class AppointmentCreate(BaseModel):
    child_id: int
    health_worker_id: Optional[int] = None
    appointment_date: date
    appointment_time: Optional[str] = None
    purpose: str
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = None  # upcoming, completed, cancelled
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    child_id: int
    health_worker_id: Optional[int] = None
    appointment_date: date
    appointment_time: Optional[str] = None
    purpose: str
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Notification Schemas
# -------------------------------------------------------------
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# AI Inference Schemas
# -------------------------------------------------------------
class AIInferenceRequest(BaseModel):
    age_months: float
    gender: Optional[str] = "Male"
    weight: float
    height: float
    muac: Optional[float] = None
    head_circumference: Optional[float] = None


class AIInferenceResponse(BaseModel):
    prediction: str
    classification: str
    risk_score: float
    confidence: float
    model_name: str
    details: Optional[dict] = None


# -------------------------------------------------------------
# Dashboard Stats Schema
# -------------------------------------------------------------
class HealthWorkerStats(BaseModel):
    total_children: int
    at_risk_count: int
    normal_count: int
    followups_scheduled: int
    status_distribution: dict
    recent_assessments_count: int
