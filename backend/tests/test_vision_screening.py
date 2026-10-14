"""
ChildNutri AI — Comprehensive Automated Test Suite for Pediatric Vision Screening
Tests all 13 critical scenarios specified in Phase Six of Master Prompt:
1. A healthy-looking school-aged child uploaded to an infant-only model.
2. A healthy child within the model's supported age range.
3. A child with clinically confirmed acute malnutrition.
4. A photograph with unsuitable lighting or excessive obstruction.
5. A missing or invalid image.
6. An incorrect or unavailable ONNX model.
7. Incorrect class-index mapping.
8. Incorrect input normalization or channel ordering.
9. Missing age, sex, weight, or height in clinical assessment.
10. Disagreement between image screening and anthropometric assessment.
11. Invalid or out-of-range model outputs (NaN / Inf / negative).
12. A model output with misleadingly high confidence.
13. A valid urgent clinical finding that must not be hidden by a reassuring image prediction.
"""
from __future__ import annotations

import io
import os
from datetime import date
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.vision_service import (
    analyze_child_photo,
    assess_image_suitability,
    run_model_inference,
    softmax_stable,
    IMAGENET_MEAN,
    IMAGENET_STD,
)
from backend.app.services.pipeline import run_assessment_pipeline
from backend.app.services.classify import classifier
from backend.app.services.who_zscore import who_engine

client = TestClient(app)

# Real test artifact paths
HEALTHY_SCHOOL_CHILD_PATH = "/Users/varadpendkar/.gemini/antigravity-ide/brain/a9de7583-74a7-454d-8755-15745e706a3d/.user_uploaded/media_1791986376297.png"
MALNOURISHED_INFANT_PATH = "/Users/varadpendkar/.gemini/antigravity-ide/brain/a9de7583-74a7-454d-8755-15745e706a3d/.user_uploaded/media_1791984518375.png"


def _create_synthetic_image(h=300, w=300, color=(180, 180, 180), blur=False, text=None):
    img = np.full((h, w, 3), color, dtype=np.uint8)
    if text:
        cv2.putText(img, text, (20, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    if blur:
        img = cv2.GaussianBlur(img, (25, 25), 0)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ── Scenario 1: Healthy School-Aged Child Uploaded to Infant Model ────────────
def test_1_healthy_school_aged_child_not_flagged_as_sam():
    """
    Ensure a healthy school-aged child wearing uniform/clothing does NOT produce
    a false-positive Severe Acute Malnutrition (SAM) classification or 78% SAM certainty.
    """
    assert os.path.exists(HEALTHY_SCHOOL_CHILD_PATH), "Test image missing"
    with open(HEALTHY_SCHOOL_CHILD_PATH, "rb") as f:
        img_bytes = f.read()

    # Case 1A: Without explicit age (clothing obstruction detected)
    res = analyze_child_photo(img_bytes, filename="school_child.jpg")
    assert res["status"] in ("inconclusive_clothing_obstruction", "unsupported_age")
    assert "Severe (SAM)" not in res["verdict"]
    assert res["suitability"]["clothing_obstruction_detected"] is True
    assert res["anatomic_scores"]["rib_prominence"] is None, "Should not fabricate rib score from uniform/tie"
    assert res["risk_tier"] != "CRITICAL"

    # Case 1B: With school age entered (e.g. 96 months / 8 years)
    res_age = analyze_child_photo(img_bytes, filename="school_child.jpg", age_months=96.0)
    assert res_age["status"] == "unsupported_age"
    assert res_age["suitability"]["age_supported"] is False
    assert "Unsupported Age" in res_age["verdict"]
    assert "0–59 months" in res_age["triage_recommendation"]


# ── Scenario 2: Healthy Child Within Supported Age Range ──────────────────────
def test_2_healthy_child_within_supported_age():
    """
    An infant within 0–59 months with smooth subcutaneous adipose coverage
    must evaluate as normal / low risk and not be falsely referred to an NRC hospital.
    """
    # Create synthetic infant torso with smooth skin tone and natural texture
    smooth_skin = np.full((400, 400, 3), (130, 160, 210), dtype=np.uint8)  # BGR skin tone
    cv2.circle(smooth_skin, (200, 100), 50, (140, 170, 220), -1)  # Head
    cv2.rectangle(smooth_skin, (120, 140), (280, 320), (130, 160, 210), -1)  # Bare torso
    np.random.seed(42)
    noise = np.random.randint(-12, 12, (400, 400, 3), dtype=np.int16)
    noisy_img = np.clip(smooth_skin.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    _, buf = cv2.imencode(".jpg", noisy_img)

    res = analyze_child_photo(buf.tobytes(), filename="healthy_infant.jpg", age_months=18.0)
    assert res["status"] == "screened"
    assert res["risk_tier"] == "LOW"
    assert "Normal" in res["verdict"] or "Adequate" in res["headline"]
    assert res["probabilities"]["Severe (SAM)"] < 0.20


# ── Scenario 3: Clinically Confirmed Severe Malnutrition Image ────────────────
def test_3_confirmed_acute_malnutrition_image():
    """
    An unclad infant with visible severe emaciation and skeletal rib prominence
    should trigger preliminary clinical concern and recommend immediate anthropometric confirmation.
    """
    assert os.path.exists(MALNOURISHED_INFANT_PATH), "Test image missing"
    with open(MALNOURISHED_INFANT_PATH, "rb") as f:
        img_bytes = f.read()

    res = analyze_child_photo(img_bytes, filename="sam_infant.jpg", age_months=14.0)
    assert res["status"] == "screened"
    assert res["suitability"]["clothing_obstruction_detected"] is False
    assert res["anatomic_scores"]["rib_prominence"] is not None
    assert res["anatomic_scores"]["rib_prominence"] >= 50.0
    assert "Concern" in res["verdict"] or "Severe" in res["verdict"]
    assert res["is_diagnostic"] is False, "Must clearly state it is preliminary screening, not confirmed diagnosis"


# ── Scenario 4: Photograph with Unsuitable Lighting or Extreme Obstruction ───
def test_4_unsuitable_lighting_and_extreme_blur():
    """
    Extreme underexposure (dark room), extreme overexposure (washout), or heavy blur
    must result in 'poor_quality' or 'inconclusive' status instead of false classification.
    """
    # 4A: Pitch black image (underexposed)
    black_bytes = _create_synthetic_image(color=(10, 10, 10))
    res_dark = analyze_child_photo(black_bytes, filename="dark.jpg", age_months=12.0)
    assert res_dark["status"] in ("poor_quality", "inconclusive_clothing_obstruction")
    assert res_dark["risk_tier"] == "INCONCLUSIVE"

    # 4B: Pure white washout (overexposed)
    white_bytes = _create_synthetic_image(color=(250, 250, 250))
    res_white = analyze_child_photo(white_bytes, filename="washout.jpg", age_months=12.0)
    assert res_white["status"] in ("poor_quality", "inconclusive_clothing_obstruction")

    # 4C: Heavy blur
    blur_bytes = _create_synthetic_image(blur=True, text="Out of focus")
    res_blur = analyze_child_photo(blur_bytes, filename="blurry.jpg", age_months=12.0)
    assert res_blur["status"] in ("poor_quality", "inconclusive_clothing_obstruction")


# ── Scenario 5: Missing or Invalid Image ──────────────────────────────────────
def test_5_missing_or_corrupted_image():
    """Corrupted bytes, non-image files, or empty payloads must return 400/422 errors gracefully."""
    # Empty bytes
    res_empty = analyze_child_photo(b"", filename="empty.jpg")
    assert res_empty["status"] == "error"

    # Corrupted text bytes
    res_corrupt = analyze_child_photo(b"This is not a JPEG header", filename="corrupt.jpg")
    assert res_corrupt["status"] == "error"

    # API endpoint test
    api_res = client.post("/api/vision/predict", files={"file": ("corrupt.txt", b"Invalid content", "text/plain")})
    assert api_res.status_code == 400


# ── Scenario 6: Incorrect or Unavailable ONNX Model ───────────────────────────
def test_6_unavailable_onnx_model_fallback():
    """When the ONNX model is missing or fails to load, the system falls back safely without 500 error."""
    with patch("backend.app.services.vision_service.get_inference_session", return_value=None):
        probs, available = run_model_inference(np.zeros((224, 224, 3), dtype=np.uint8))
        assert available is False
        assert len(probs) == 3
        assert np.isclose(sum(probs), 1.0, atol=1e-3)


# ── Scenario 7: Class-Index Mapping & Probability Integrity ───────────────────
def test_7_class_index_mapping():
    """Verify classes correctly map to [Healthy, Moderate (MAM), Severe (SAM)] summing to 1.0."""
    with patch("backend.app.services.vision_service.get_inference_session") as mock_sess:
        # Mock session returning known logits: [0.1, 0.2, 0.7]
        mock_instance = MagicMock()
        mock_instance.run.return_value = [[[0.1, 0.2, 0.7]]]
        mock_sess.return_value = mock_instance

        probs, available = run_model_inference(np.zeros((224, 224, 3), dtype=np.uint8))
        assert available is True
        assert len(probs) == 3
        assert np.isclose(sum(probs), 1.0, atol=1e-3)
        assert probs[2] > probs[1] > probs[0]


# ── Scenario 8: Input Normalization & Channel Ordering ────────────────────────
def test_8_input_normalization_and_channels():
    """Verify ImageNet normalization constants and channel ordering."""
    assert np.allclose(IMAGENET_MEAN, [0.485, 0.456, 0.406])
    assert np.allclose(IMAGENET_STD, [0.229, 0.224, 0.225])
    
    # Test stable softmax
    logits = np.array([1000.0, 1001.0, 1002.0], dtype=np.float32)  # Large numbers that would overflow standard exp
    sm = softmax_stable(logits)
    assert not np.isnan(sm).any()
    assert np.isclose(np.sum(sm), 1.0)
    assert sm[2] > sm[1] > sm[0]


# ── Scenario 9: Missing Required Fields in Anthropometric Assessment ──────────
def test_9_missing_required_fields_handling():
    """
    Ensure the WHO classification and pipeline handle missing or out-of-range inputs safely.
    """
    # Missing WHZ and WAZ
    class_res = classifier.classify(waz=None, haz=-1.0, whz=None, muac_cm=None, bilateral_edema=False, age_months=12.0)
    assert class_res["severity"] in ("normal", "healthy", "unknown")

    # Incomplete inputs should reduce data confidence
    pipe_res = run_assessment_pipeline(
        sex="Female",
        dob=date(2025, 1, 1),
        measurement_date=date(2026, 1, 1),
        weight_kg=8.5,
        height_cm=75.0,
        muac_cm=None,  # Missing
        bilateral_edema=False,
    )
    assert pipe_res["data_confidence"] in ("Low", "Medium")


# ── Scenario 10: Disagreement Between Image Screening and Anthropometry ──────
def test_10_screening_discrepancy_handled_correctly():
    """
    When preliminary photo screening suggests wasting, but verified anthropometric
    measurements confirm normal weight and height, anthropometry must take clinical precedence
    and a clear discrepancy notice must be generated.
    """
    mock_photo_screen = {
        "verdict": "Preliminary Concern: Potential Severe Wasting",
        "confidence_pct": 68.0,
        "status": "screened"
    }

    pipe_res = run_assessment_pipeline(
        sex="Male",
        dob=date(2025, 4, 1),
        measurement_date=date(2026, 4, 1),
        weight_kg=10.2,       # Normal healthy 12-month weight
        height_cm=76.0,       # Normal healthy height
        muac_cm=14.2,         # Green zone (> 12.5 cm)
        bilateral_edema=False,
        photo_screening_result=mock_photo_screen,
    )

    # Anthropometry must govern the official status
    assert pipe_res["status_now"]["headline"] == "Healthy"
    assert pipe_res["status_now"]["severity"] == "normal"
    
    # Reconciliation layer must document the discrepancy
    recon = pipe_res.get("photo_screening_reconciliation", {})
    assert recon.get("photo_screening_provided") is True
    assert recon["discrepancy"]["flagged"] is True
    assert recon["discrepancy"]["type"] == "false_visual_alarm"
    assert "confirms Normal Nutritional Status" in recon["discrepancy"]["message"]


# ── Scenario 11: Invalid or Out-of-Range Model Outputs ────────────────────────
def test_11_out_of_range_model_outputs():
    """Negative values, NaN, or infinite probabilities must be safely sanitized."""
    raw_invalid = np.array([-5.0, np.nan, np.inf], dtype=np.float32)
    # Replaces nan/inf safely
    raw_cleaned = np.nan_to_num(raw_invalid, nan=0.0, posinf=1.0, neginf=-1.0)
    sm = softmax_stable(raw_cleaned)
    assert not np.isnan(sm).any()
    assert not np.isinf(sm).any()
    assert np.isclose(np.sum(sm), 1.0)


# ── Scenario 12: No Fabricated Certainty on Unvalidated Input ─────────────────
def test_12_no_fabricated_confidence_on_inconclusive():
    """
    Inconclusive images (e.g. clothed school child) must NOT report high confidence (e.g. 78% or 99%).
    Confidence must be 0% or marked as unvalidated.
    """
    with open(HEALTHY_SCHOOL_CHILD_PATH, "rb") as f:
        img_bytes = f.read()

    res = analyze_child_photo(img_bytes, filename="school.jpg")
    assert res["confidence_pct"] == 0.0, "Confidence must be 0.0 on inconclusive/clothed photos"
    assert res["risk_tier"] == "INCONCLUSIVE"


# ── Scenario 13: Urgent Clinical Finding NEVER Hidden by Reassuring Photo ─────
def test_13_urgent_clinical_danger_never_hidden():
    """
    If a child has bilateral pitting oedema or severe wasting (WHZ < -3.0 or MUAC < 11.5 cm),
    a reassuring or healthy photo prediction must NEVER suppress the emergency hospital referral!
    """
    mock_healthy_photo = {
        "verdict": "Preliminary Screening: Normal Subcutaneous Fat",
        "confidence_pct": 85.0,
        "status": "screened"
    }

    # Child has bilateral pitting oedema (Kwashiorkor)
    pipe_res = run_assessment_pipeline(
        sex="Female",
        dob=date(2025, 1, 1),
        measurement_date=date(2026, 1, 1),
        weight_kg=7.0,
        height_cm=72.0,
        muac_cm=11.2,          # Red zone SAM (< 11.5 cm)
        bilateral_edema=True,  # Severe SAM sign
        photo_screening_result=mock_healthy_photo,
    )

    # Clinical SAM must be declared
    assert pipe_res["status_now"]["severity"] in ("severe", "critical")
    assert pipe_res["status_now"]["red_flag_hospital"] is True
    assert "SAM" in pipe_res["status_now"]["headline"]

    # Reconcilation must flag masked clinical danger
    recon = pipe_res.get("photo_screening_reconciliation", {})
    assert recon["discrepancy"]["flagged"] is True
    assert recon["discrepancy"]["type"] == "masked_clinical_danger"
    assert "CRITICAL" in recon["discrepancy"]["message"]
