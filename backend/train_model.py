"""
train_model.py

Trains the numerical branch (Random Forest baseline) on
dataset/anthropometric/child_health_data.csv and saves:

    backend/models/numerical_model.joblib   - the trained classifier
    backend/models/scaler.joblib            - the fitted StandardScaler

predict.py loads both to score new children with the exact same scaling
used at training time.

Run from backend/:  python train_model.py
"""

import os
import joblib

from preprocessing import prepare_numerical_pipeline
from numerical_model import (
    NumericalModel, FEATURE_COLUMNS, train_test_split_by_size, evaluate,
)

DEFAULT_CSV = os.path.join("..", "dataset", "anthropometric", "child_health_data.csv")
MODELS_DIR = "models"


def main(csv_path: str = DEFAULT_CSV):
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"[train_model] Loading and preprocessing {csv_path} ...")
    df, scaler = prepare_numerical_pipeline(csv_path)

    X = df[FEATURE_COLUMNS].values
    y = df["label_encoded"].values

    X_train, X_test, y_train, y_test = train_test_split_by_size(X, y)

    print(f"[train_model] Training Random Forest on {len(X_train)} row(s) ...")
    model = NumericalModel()
    model.fit(X_train, y_train)

    print("[train_model] Evaluating ...")
    metrics = evaluate(model, X_test, y_test)
    print(f"[train_model] Metrics: {metrics}")

    print("[train_model] Feature importances:", model.feature_importances())

    model_path = os.path.join(MODELS_DIR, "numerical_model.joblib")
    scaler_path = os.path.join(MODELS_DIR, "scaler.joblib")
    model.save(model_path)
    joblib.dump(scaler, scaler_path)
    print(f"[train_model] Saved model to {model_path}")
    print(f"[train_model] Saved scaler to {scaler_path}")

    return model, scaler, metrics


if __name__ == "__main__":
    main()
