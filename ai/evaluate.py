"""
=============================================================================
ChildNutri AI - Model Evaluation & Performance Visualization
=============================================================================
Evaluates the trained model on test data, prints performance metrics,
and saves a comprehensive evaluation report.
=============================================================================
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
TEST_CSV_PATH = os.path.join(MODELS_DIR, "splits", "test.csv")

def evaluate_pipeline():
    if not os.path.exists(TEST_CSV_PATH):
        print("Test split not found at:", TEST_CSV_PATH)
        return

    test_df = pd.read_csv(TEST_CSV_PATH)
    transformer = joblib.load(os.path.join(MODELS_DIR, "transformer.pkl"))
    model = joblib.load(os.path.join(MODELS_DIR, "ensemble_model.pkl"))
    classes = list(model.classes_)

    X_test = transformer.transform(test_df)
    y_test = transformer.label_encoder.transform(test_df["label"].astype(str))

    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=classes, digits=4)

    print("=" * 60)
    print("EVALUATION REPORT: Soft-Voting Ensemble (XGB 40% + LGB 35% + RF 25%)")
    print("=" * 60)
    print(f"Test Samples:     {len(test_df)}")
    print(f"Overall Accuracy: {acc * 100:.2f}%")
    print(f"Weighted F1:      {f1 * 100:.2f}%\n")
    print("Classification Report:")
    print(report)
    print("Confusion Matrix:")
    print(cm)
    print("=" * 60)

if __name__ == "__main__":
    evaluate_pipeline()
