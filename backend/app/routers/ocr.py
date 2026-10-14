"""OCR router — upload health report → extract fields → return for review"""
import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.deps import get_current_user
from backend.app.services.ocr_service import extract_from_report
from backend.app.config import settings

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/extract")
async def extract_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"File type {file.content_type} not allowed. Use JPEG, PNG, or PDF.")

    # Read and size-check
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB)")

    # Save to temp
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}.get(file.content_type, ".jpg")
    tmp_name = f"/tmp/ocr_{uuid.uuid4().hex}{ext}"
    with open(tmp_name, "wb") as f_out:
        f_out.write(content)

    try:
        result = extract_from_report(tmp_name)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    result["notice"] = (
        "⚠ All extracted values MUST be verified before use. "
        "OCR accuracy depends on image quality. Do not trust without review."
    )
    return result


# Resources router
from backend.app.models import Article

resources_router = APIRouter(prefix="/api/resources", tags=["resources"])


@resources_router.get("")
def list_resources(topic: str = None, q: str = None, db: Session = Depends(get_db)):
    query = db.query(Article)
    if topic:
        query = query.filter(Article.topic == topic)
    if q:
        query = query.filter(
            Article.title.ilike(f"%{q}%") | Article.summary.ilike(f"%{q}%")
        )
    return query.limit(50).all()


@resources_router.get("/{slug}")
def get_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(404, "Article not found")
    return article


# Meta router
meta_router = APIRouter(prefix="/api/meta", tags=["meta"])


@meta_router.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@meta_router.get("/model-card")
def model_card():
    """Return model card — load real metrics from artifact if available."""
    import os
    import joblib

    artifact_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "ml_artifacts", "risk_model.joblib"
    )
    ml_metrics = {
        "method": "LightGBM (n_est=120, max_depth=5) + Isotonic calibration",
        "training_data": "Dataset Stunting and Nutritional Status of Toddler (40k records)",
        "roc_auc": "Not yet computed",
        "brier_score": "Not yet computed",
        "limits": "Survey data ≠ clinic data. Context prediction only, not clinical diagnosis.",
    }
    if os.path.exists(artifact_path):
        try:
            art = joblib.load(artifact_path)
            m = art.get("metrics", {})
            ml_metrics["roc_auc"] = m.get("roc_auc", "N/A")
            ml_metrics["brier_score"] = m.get("brier_score", "N/A")
            ml_metrics["train_samples"] = m.get("train_samples", "N/A")
            ml_metrics["test_samples"] = m.get("test_samples", "N/A")
        except Exception:
            pass

    return {
        "who_engine": {
            "method": "WHO LMS formula (2006)",
            "accuracy": "Deterministic — near-perfect with WHO Anthro software",
            "validated_on": "WHO published LMS tables (WAZ, HAZ, WHZ, BAZ, HCZ)",
        },
        "classifier": {
            "method": "WHO/CMAM deterministic cut-off rules",
            "accuracy": "100% by definition — real error comes from measurement error only",
            "rules": "SAM: WHZ<-3 or MUAC<11.5cm or oedema | MAM: -3≤WHZ<-2",
        },
        "future_risk_model": ml_metrics,
        "ocr_pipeline": {
            "engine": "Tesseract 4 (LSTM) + OpenCV preprocessing",
            "fields_extracted": "weight_kg, height_cm, age_months, muac_cm, child_name, date",
            "note": "All extracted values MUST be verified by a human before clinical use.",
        },
        "disclaimer": (
            "ChildNutri AI is a screening and education tool. "
            "It does not diagnose illness and does not replace a doctor, nurse, or Anganwadi worker."
        ),
    }
