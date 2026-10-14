"""
ChildNutri AI — Pydantic Schemas (request / response)
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "parent"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("parent", "health_worker"):
            raise ValueError("Role must be parent or health_worker")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"

    model_config = {"from_attributes": True}


# ── Child ─────────────────────────────────────────────────────────────────────

class ChildCreate(BaseModel):
    name: str
    date_of_birth: date
    sex: str
    birth_weight_kg: Optional[float] = None
    birth_length_cm: Optional[float] = None
    birth_order: Optional[int] = None
    state_region: Optional[str] = None
    area_type: Optional[str] = "Urban"
    observations: Optional[str] = None

    @field_validator("sex")
    @classmethod
    def valid_sex(cls, v: str) -> str:
        if v not in ("Male", "Female"):
            raise ValueError("Sex must be Male or Female")
        return v


class ChildOut(BaseModel):
    id: int
    health_id: str
    name: str
    date_of_birth: date
    sex: str
    birth_weight_kg: Optional[float]
    birth_length_cm: Optional[float]
    state_region: Optional[str]
    area_type: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Assessment ───────────────────────────────────────────────────────────────

class MeasurementIn(BaseModel):
    weight_kg: float
    height_cm: float
    muac_cm: Optional[float] = None
    head_circ_cm: Optional[float] = None
    bilateral_edema: bool = False
    how_measured: Optional[str] = "doctor"


class FeedingIn(BaseModel):
    breastfed: Optional[bool] = None
    exclusive_bf_6m: Optional[bool] = None
    complementary_food_age_months: Optional[float] = None
    food_groups_yesterday: Optional[int] = None  # 0-8
    meals_per_day: Optional[int] = None
    appetite: Optional[str] = None  # good | poor | refuses


class HealthIn(BaseModel):
    diarrhoea_2w: Optional[bool] = None
    fever_2w: Optional[bool] = None
    cough_2w: Optional[bool] = None
    vaccination_status: Optional[str] = None  # full | partial | none
    vitamin_a: Optional[bool] = None
    known_illness: Optional[str] = None
    food_allergy: Optional[str] = None


class HomeIn(BaseModel):
    mother_education: Optional[str] = None   # none | primary | secondary | higher
    mother_age: Optional[int] = None
    wealth_score: Optional[int] = None       # 0-5
    rural_urban: Optional[str] = None
    toilet_type: Optional[str] = None
    water_source: Optional[str] = None
    cooking_fuel: Optional[str] = None
    food_preference: Optional[str] = None    # veg | non-veg
    anganwadi_access: Optional[bool] = None


class AssessmentCreate(BaseModel):
    child_id: int
    measurement_date: date
    measurement: MeasurementIn
    feeding: Optional[FeedingIn] = None
    health: Optional[HealthIn] = None
    home: Optional[HomeIn] = None
    photo_id: Optional[int] = None
    report_id: Optional[int] = None
    photo_screening_result: Optional[dict] = None


class AssessmentOut(BaseModel):
    id: int
    child_id: int
    age_months: float
    measurement_date: date
    status_now: Optional[str]
    tier_future: Optional[str]
    data_confidence: Optional[str]
    result_json: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Resources ─────────────────────────────────────────────────────────────────

class ArticleOut(BaseModel):
    id: int
    slug: str
    title: str
    topic: str
    summary: str
    body_md: str
    source_name: Optional[str]
    source_url: Optional[str]
    reviewed_on: Optional[str]

    model_config = {"from_attributes": True}
