from __future__ import annotations

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.classify import classifier
from backend.app.services.pipeline import run_assessment_pipeline


client = TestClient(app)


def _signup():
    email = f"parent-{uuid4().hex[:8]}@example.com"
    password = "Strong123"
    res = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Parent",
            "role": "parent",
        },
    )
    assert res.status_code == 201, res.text
    return email, password


def test_classifier_muac_boundaries():
    assert classifier.classify(None, None, -1.0, 11.49, False, 12)["headline"] == "Severe Acute Malnutrition (SAM)"
    assert classifier.classify(None, None, -1.0, 11.50, False, 12)["headline"] == "Moderate Acute Malnutrition (MAM)"
    assert classifier.classify(None, None, -1.0, 12.49, False, 12)["headline"] == "Moderate Acute Malnutrition (MAM)"
    assert classifier.classify(None, None, -1.0, 12.50, False, 12)["headline"] == "Healthy"


def test_pipeline_returns_complete_result():
    result = run_assessment_pipeline(
        sex="Male",
        dob=date(2024, 10, 1),
        measurement_date=date(2026, 10, 1),
        weight_kg=9.8,
        height_cm=83.0,
        muac_cm=12.8,
        bilateral_edema=False,
        food_groups_yesterday=5,
        meals_per_day=4,
        breastfed=False,
        vaccination_status="full",
        mother_education="secondary",
        wealth_score=3,
        rural_urban="Urban",
    )
    assert set(["zscores", "status_now", "future_risk", "diet_plan", "data_confidence"]).issubset(result)
    assert result["status_now"]["headline"]
    assert result["future_risk"]["tier"] in {"LOW", "WATCH", "HIGH"}


def test_auth_child_assessment_and_history_flow():
    _signup()
    child_res = client.post(
        "/api/children",
        json={
            "name": "Aarav",
            "date_of_birth": "2024-10-01",
            "sex": "Male",
            "area_type": "Urban",
        },
    )
    assert child_res.status_code == 201, child_res.text
    child_id = child_res.json()["id"]

    assessment_res = client.post(
        "/api/assessments",
        json={
            "child_id": child_id,
            "measurement_date": "2026-10-01",
            "measurement": {
                "weight_kg": 9.8,
                "height_cm": 83.0,
                "muac_cm": 12.8,
                "bilateral_edema": False,
                "how_measured": "doctor",
            },
            "feeding": {"food_groups_yesterday": 5, "meals_per_day": 4, "breastfed": False, "appetite": "good"},
            "health": {"diarrhoea_2w": False, "fever_2w": False, "vaccination_status": "full"},
            "home": {"mother_education": "secondary", "wealth_score": 3, "rural_urban": "Urban"},
        },
    )
    assert assessment_res.status_code == 201, assessment_res.text
    assessment = assessment_res.json()
    assert assessment["status_now"]
    assert assessment["tier_future"] in {"LOW", "WATCH", "HIGH"}

    history_res = client.get(f"/api/assessments/child/{child_id}/history")
    assert history_res.status_code == 200, history_res.text
    assert history_res.json()[0]["id"] == assessment["id"]

    # Verify PDF download returns valid attachment header
    pdf_res = client.get(f"/api/assessments/{assessment['id']}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers.get("content-type") == "application/pdf"
    assert "filename=\"ChildNutriAI_Report_" in pdf_res.headers.get("content-disposition", "")


def test_resources_seed_count_and_topics():
    res = client.get("/api/resources")
    assert res.status_code == 200
    articles = res.json()
    assert len(articles) == 20
    topics = set(a["topic"] for a in articles)
    assert {"Symptoms", "Feeding", "Schemes", "Prevention"}.issubset(topics)


def test_ocr_vector_pdf_extraction():
    import tempfile, os
    from backend.app.services.report_pdf import generate_pdf_report
    from backend.app.services.ocr_service import extract_from_report

    pdf_bytes = generate_pdf_report(
        child_name="Aarav Sharma",
        child_dob="2025-01-15",
        child_sex="Male",
        assessment_date="2026-01-15",
        result={
            "classification": {"verdict": "HEALTHY", "waz": 0.1, "haz": -0.2, "whz": 0.3, "muac_status": "green"},
            "future_risk": {"risk_level": "Low", "risk_score": 20, "stunting_risk_pct": 18},
            "diet_plan": {"summary": "Balanced family foods"},
        },
    )
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf_bytes)
        tpath = tf.name

    try:
        res = extract_from_report(tpath)
        assert res["status"] == "success"
        assert len(res["raw_text"]) > 100
        assert "Aarav Sharma" in res["raw_text"]
    finally:
        if os.path.exists(tpath):
            os.remove(tpath)

