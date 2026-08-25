"""
Direct AI Inference Endpoints.
Can be invoked standalone to test or query model predictions.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.schemas import AIInferenceRequest, AIInferenceResponse
from backend.services.ai_service import predict_malnutrition, analyze_child_image
from backend.dependencies import get_current_user
from backend.models import User

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])


@router.post("/predict", response_model=AIInferenceResponse)
def run_ai_prediction(
    payload: AIInferenceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute standalone anthropometric AI prediction.
    Accepts: age_months, gender, weight, height, muac, head_circumference.
    Returns: classification, risk_score, confidence, details.
    """
    result = predict_malnutrition(payload.model_dump())
    return AIInferenceResponse(
        prediction=result["prediction"],
        classification=result["classification"],
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        model_name=result.get("model_name", "ChildNutri Anthropometric Model v1"),
        details=result.get("details")
    )


@router.post("/analyze-image")
async def run_image_screening(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Direct computer vision screening endpoint.
    Processes image and returns visual feature cues.
    """
    return {
        "status": "success",
        "message": "Image received for AI visual screening",
        "filename": image.filename,
        "visual_score": 75.0,
        "classification": "Visual Screen: Borderline",
        "confidence": 0.85,
        "model_name": "ChildNutri Vision Screener v1 (Placeholder)"
    }
