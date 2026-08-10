"""
explainability.py — NOT YET IMPLEMENTED.

Step 7 of the build plan. Comes after the fused model produces predictions
worth explaining.

Two explainers, one per branch:

    explain_image(image_array, image_model) -> heatmap
        Grad-CAM over the EfficientNet-B0 branch. Answers:
        "which region of the image influenced the prediction?"

    explain_numerical(feature_row, numerical_model) -> dict
        SHAP values over the Random Forest/XGBoost branch. Answers:
        "how much did age / height / weight / MUAC each contribute?"
        e.g. {"muac": 0.42, "weight": 0.31, "age": 0.15, "height": 0.08,
              "gender": 0.04}

`numerical_model.NumericalModel.feature_importances()` already gives a
model-wide ranking as a stand-in — SHAP will replace that with real
per-prediction contributions, which is what the dashboard's
"Important Factors" section is meant to show.
"""
