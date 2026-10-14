"""
ChildNutri AI — Vision Router for Pediatric Photo Nutritional Screening
Accepts infant / child photograph, executes Image Suitability & Quality Gate,
runs ONNX neural feature extraction, and provides transparent preliminary visual triage.
"""
from __future__ import annotations

import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Cookie, Header
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, Child
from backend.app.security import decode_token
from backend.app.services.vision_service import analyze_child_photo
from backend.app.services.pipeline import compute_age_months

router = APIRouter(prefix="/api/vision", tags=["vision"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_optional_user(
    access_token: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    token = access_token
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = int(payload["sub"])
        user = db.get(User, user_id)
        if user and user.is_active:
            return user
    except Exception:
        pass
    return None


@router.post("/predict")
async def predict_child_photo(
    file: UploadFile = File(...),
    age_months: Optional[float] = Form(None),
    child_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Accepts an infant / child photo and executes:
    - Image Suitability Gate (optical quality, blur, exposure).
    - Clothing & Torso Obstruction detection.
    - Pediatric Age Range Validation (0–59 months for WHO 2006 acute malnutrition).
    - ONNX Neural Feature Extraction.
    - Transparent preliminary triage and clinical next steps.
    """
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_TYPES and not (file.filename and file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type ({content_type or 'unknown'}). Please upload a JPEG, PNG, or WebP photo."
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (maximum 10 MB).")

    if len(image_bytes) < 1024:
        raise HTTPException(status_code=400, detail="Corrupted or empty image file.")

    # If child_id provided, calculate exact age from birth date
    calculated_age_months = age_months
    child_name = None
    if child_id is not None:
        child = db.get(Child, child_id)
        if child:
            calculated_age_months = compute_age_months(child.date_of_birth)
            child_name = child.name

    result = analyze_child_photo(
        image_bytes,
        filename=file.filename or "child_photo.jpg",
        age_months=calculated_age_months
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message", "Image analysis failed."))

    # Clinical safety disclaimer
    result["safety_notice"] = (
        "AI Visual Screening is an adjunct triaging tool and CANNOT diagnose malnutrition. "
        "A clinical anthropometric assessment (weight, height, MUAC) is required to establish diagnosis."
    )
    result["user_authenticated"] = user is not None
    if user:
        result["analyst"] = user.full_name or user.email
    if child_name:
        result["child_name"] = child_name
    result["evaluated_age_months"] = calculated_age_months

    return result
