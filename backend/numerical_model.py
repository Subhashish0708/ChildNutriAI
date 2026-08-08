
from __future__ import annotations

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)

FEATURE_COLUMNS = ["age_scaled", "height_scaled", "weight_scaled", "muac_scaled", "gender_encoded"]
CLASS_NAMES = ["Normal", "Moderate", "Severe"]  # index-aligned with preprocessing.CLASS_MAP


class NumericalModel:
    """Thin wrapper so train_model.py / predict.py don't depend on sklearn directly."""

    def __init__(self, n_estimators: int = 200, random_state: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            class_weight="balanced",  # dataset is likely to be class-imbalanced early on
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        return self.model.predict_proba(X)

    def feature_importances(self) -> dict:
        """Which of age/height/weight/muac/gender drove the model's splits.

        A quick built-in stand-in for SHAP until explainability.py exists —
        SHAP gives per-prediction contributions, this gives overall ranking.
        """
        self._check_fitted()
        return dict(zip(FEATURE_COLUMNS, self.model.feature_importances_))

    def save(self, path: str):
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str) -> "NumericalModel":
        wrapper = cls()
        wrapper.model = joblib.load(path)
        wrapper.is_fitted = True
        return wrapper

    def _check_fitted(self):
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained or loaded yet.")


def train_test_split_by_size(X, y, test_size: float = 0.2, random_state: int = 42):
    """
    Wraps sklearn's split, but falls back to using all data for both train
    and test when the dataset is too small to split meaningfully (true for
    the current 3-row sample dataset — this keeps the pipeline runnable
    end-to-end before a real dataset exists, while making the limitation visible).
    """
    if len(X) < 5:
        print(f"[numerical_model] Only {len(X)} sample(s) available — "
              f"too few for a train/test split. Evaluating on the training "
              f"set itself; treat any metrics as a smoke test, not a real score.")
        return X, X, y, y

    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def evaluate(model: NumericalModel, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average="macro", zero_division=0),
        "recall": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
    }
    print("[numerical_model] Classification report:\n",
          classification_report(y_test, y_pred, target_names=CLASS_NAMES,
                                 labels=[0, 1, 2], zero_division=0))
    print("[numerical_model] Confusion matrix:\n", confusion_matrix(y_test, y_pred, labels=[0, 1, 2]))
    return metrics
