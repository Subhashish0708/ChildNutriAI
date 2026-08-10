"""
app.py

Minimal API around the numerical branch. This is intentionally small —
it exposes the one thing that's actually implemented (predict_numerical)
rather than stubbing out routes for the image/fusion branches before
they exist.

Run from backend/:  python app.py
Then:  curl -X POST http://localhost:5000/predict \
         -H "Content-Type: application/json" \
         -d '{"age":3,"height":78,"weight":8,"muac":10.5,"gender":"Female"}'

TODO once later steps land:
  POST /predict/image   -> image_model.py + fusion_model.py
  POST /predict          -> switch to predict_fused() once fusion exists
  POST /children         -> persist registration data (needs a database — see backend/README.md)
  POST /children/:id/images -> store uploads (see ../uploads/)
"""

from flask import Flask, request, jsonify

from predict import predict_numerical, load_trained_model
from preprocessing import GENDER_MAP

app = Flask(__name__)

_model = None
_scaler = None


def get_model():
    """Lazy-load so the app can start even before training has run."""
    global _model, _scaler
    if _model is None:
        _model, _scaler = load_trained_model()
    return _model, _scaler


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    """
    Numerical-branch-only prediction.

    Body: {"age": 3, "height": 78, "weight": 8, "muac": 10.5, "gender": "Female"}
    """
    data = request.get_json(silent=True) or {}

    required = ["age", "height", "weight", "muac", "gender"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing field(s): {missing}"}), 400

    if str(data["gender"]).strip().lower() not in GENDER_MAP:
        return jsonify({"error": f"gender must be one of {list(GENDER_MAP)}"}), 400

    try:
        model, scaler = get_model()
        result = predict_numerical(
            age=data["age"], height=data["height"], weight=data["weight"],
            muac=data["muac"], gender=data["gender"], model=model, scaler=scaler,
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503  # model not trained yet
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
