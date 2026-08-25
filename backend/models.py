"""
SQLAlchemy ORM Models for ChildNutri AI.
Represents Users, Children, Assessments, AI Predictions, Photos,
Medical History, Nutrition Plans, Appointments, and Notifications.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, 
    ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    """
    System user model for Authentication and Role-based Access.
    Roles: 'parent', 'health_worker', 'admin'
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="parent")  # parent, health_worker, admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    assessments_conducted = relationship("Assessment", back_populates="health_worker")
    appointments = relationship("Appointment", back_populates="health_worker")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    nutrition_plans = relationship("NutritionPlan", back_populates="creator")


class Child(Base):
    """
    Infant/Child profile model.
    Linked to parent User. Health ID is a unique tracking code.
    """
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    health_id = Column(String(50), unique=True, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)  # Male, Female, Other
    birth_weight = Column(Float, nullable=True)  # in kg
    birth_length = Column(Float, nullable=True)  # in cm
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    parent = relationship("User", back_populates="children")
    assessments = relationship("Assessment", back_populates="child", cascade="all, delete-orphan", order_by="Assessment.assessment_date.desc()")
    photos = relationship("ChildPhoto", back_populates="child", cascade="all, delete-orphan")
    medical_history = relationship("MedicalHistory", back_populates="child", cascade="all, delete-orphan", order_by="MedicalHistory.visit_date.desc()")
    nutrition_plans = relationship("NutritionPlan", back_populates="child", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="child", cascade="all, delete-orphan", order_by="Appointment.appointment_date.asc()")


class Assessment(Base):
    """
    Anthropometric assessment record.
    Historical measurements are always appended as new rows (never overwritten).
    """
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    health_worker_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assessment_date = Column(Date, default=date.today, nullable=False)
    age_months = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)  # in kg
    height = Column(Float, nullable=False)  # in cm
    muac = Column(Float, nullable=True)     # Mid-Upper Arm Circumference in cm
    head_circumference = Column(Float, nullable=True) # in cm
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    child = relationship("Child", back_populates="assessments")
    health_worker = relationship("User", back_populates="assessments_conducted")
    prediction = relationship("Prediction", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    photos = relationship("ChildPhoto", back_populates="assessment")


class Prediction(Base):
    """
    AI inference results for an assessment.
    Stores classification, risk score (0-100), and confidence.
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), unique=True, nullable=False)
    model_name = Column(String(100), default="ChildNutri Anthropometric Model v1")
    prediction = Column(String(50), nullable=False)  # Normal, Stunted, Wasted, Underweight, Severe (SAM)
    risk_score = Column(Float, nullable=False)       # 0 - 100 percentage
    confidence = Column(Float, nullable=False)       # 0.0 - 1.0 probability
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    assessment = relationship("Assessment", back_populates="prediction")


class ChildPhoto(Base):
    """
    Uploaded child photo metadata.
    Actual image file resides on disk in uploads/children/{child_id}/, path stored here.
    photo_type: 'front', 'side', 'full_body'
    """
    __tablename__ = "child_photos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    photo_type = Column(String(20), nullable=False)  # front, side, full_body
    file_path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    child = relationship("Child", back_populates="photos")
    assessment = relationship("Assessment", back_populates="photos")


class MedicalHistory(Base):
    """
    Clinical visits and medical records timeline for a child.
    """
    __tablename__ = "medical_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    visit_date = Column(Date, nullable=False)
    diagnosis = Column(String(200), nullable=False)
    treatment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    child = relationship("Child", back_populates="medical_history")


class NutritionPlan(Base):
    """
    Personalized dietary and therapeutic feeding plan for a child.
    """
    __tablename__ = "nutrition_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    plan_title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    child = relationship("Child", back_populates="nutrition_plans")
    creator = relationship("User", back_populates="nutrition_plans")


class Appointment(Base):
    """
    Scheduled clinic/health-center visits for follow-up and monitoring.
    Status: 'upcoming', 'completed', 'cancelled'
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    health_worker_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(20), nullable=True)  # e.g., "10:00 AM"
    purpose = Column(String(200), nullable=False)
    status = Column(String(20), default="upcoming", nullable=False)  # upcoming, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    child = relationship("Child", back_populates="appointments")
    health_worker = relationship("User", back_populates="appointments")


class Notification(Base):
    """
    In-app alerts and notifications for parents and health workers.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(30), default="info", nullable=False)  # alert, warning, info, appointment
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="notifications")
