"""
ChildNutri AI — SQLAlchemy ORM Models
Tables: users, children, assessments, measurements, photos, reports, articles, refresh_tokens
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="parent")  # parent | health_worker | admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)  # JWT ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    health_id = Column(String(20), unique=True, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(String(10), nullable=False)            # Male | Female
    birth_weight_kg = Column(Float, nullable=True)
    birth_length_cm = Column(Float, nullable=True)
    birth_order = Column(Integer, nullable=True)
    state_region = Column(String(100), nullable=True)
    area_type = Column(String(10), nullable=True)       # Urban | Rural
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    parent = relationship("User", back_populates="children")
    assessments = relationship("Assessment", back_populates="child", cascade="all, delete-orphan",
                               order_by="Assessment.created_at.desc()")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    conducted_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # health_worker
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    measurement_date = Column(Date, nullable=False)
    age_months = Column(Float, nullable=False)

    # Full inputs stored as JSON for reproducibility
    inputs_json = Column(JSON, nullable=True)
    # Full result stored as JSON
    result_json = Column(JSON, nullable=True)

    # Quick-query fields
    status_now = Column(String(30), nullable=True)     # SAM | MAM | STUNTED | UNDERWEIGHT | OVERWEIGHT | HEALTHY
    tier_future = Column(String(10), nullable=True)    # LOW | WATCH | HIGH
    data_confidence = Column(String(10), nullable=True) # High | Medium | Low
    model_versions = Column(JSON, nullable=True)

    child = relationship("Child", back_populates="assessments")
    measurements = relationship("Measurement", back_populates="assessment", cascade="all, delete-orphan",
                                uselist=False)
    photos = relationship("Photo", back_populates="assessment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="assessment", cascade="all, delete-orphan")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)
    muac_cm = Column(Float, nullable=True)
    head_circ_cm = Column(Float, nullable=True)
    bilateral_edema = Column(Boolean, default=False, nullable=False)
    how_measured = Column(String(30), nullable=True)   # self | anganwadi | doctor

    assessment = relationship("Assessment", back_populates="measurements")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    file_path = Column(String(255), nullable=False)
    photo_type = Column(String(20), nullable=True)     # face | full_body
    deleted = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="photos")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    extracted_json = Column(JSON, nullable=True)       # OCR-extracted fields
    kept_original = Column(Boolean, default=False)
    file_path = Column(String(255), nullable=True)     # original report file (optional)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="reports")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    topic = Column(String(50), nullable=False)   # Causes|Symptoms|Feeding|Recipes|Schemes|Myths|Prevention|WhenToSeek
    summary = Column(String(500), nullable=False)
    body_md = Column(Text, nullable=False)
    source_name = Column(String(150), nullable=True)
    source_url = Column(String(500), nullable=True)
    reviewed_on = Column(String(20), nullable=True)    # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)
