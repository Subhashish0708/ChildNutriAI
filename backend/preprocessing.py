"""
preprocessing.py

Handles the data-preparation steps that sit in front of both branches of
the pipeline:

  Numerical branch : read_csv -> check_missing_values -> clean_data
                     -> normalize_numerical_features -> encode_gender
  Image branch     : prepare_image_input (resize/normalize; used once
                     image_model.py exists)

This is intentionally the first backend module implemented — everything
downstream (numerical_model.py, train_model.py, predict.py) depends on it
producing a clean, numeric feature matrix.
"""

from __future__ import annotations

import os
import pandas as pd
import numpy as np

# Columns expected in dataset/anthropometric/child_health_data.csv
REQUIRED_COLUMNS = [
    "child_id", "age", "height", "weight", "muac", "gender",
    "malnutrition", "image_path",
]

NUMERICAL_FEATURES = ["age", "height", "weight", "muac"]

GENDER_MAP = {"male": 0, "female": 1, "other": 2}
CLASS_MAP = {"normal": 0, "moderate": 1, "severe": 2}
INVERSE_CLASS_MAP = {v: k.capitalize() for k, v in CLASS_MAP.items()}


def load_anthropometric_data(csv_path: str) -> pd.DataFrame:
    """Read the anthropometric CSV and verify it has the columns we expect."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV is missing required column(s): {missing_cols}. "
            f"Expected columns: {REQUIRED_COLUMNS}"
        )

    return df


def check_missing_values(df: pd.DataFrame) -> pd.Series:
    """Return a per-column count of missing values (0 for fully complete columns)."""
    return df[REQUIRED_COLUMNS].isnull().sum()


def clean_data(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Drop rows with missing values in the columns the model actually needs,
    and coerce numerical columns to numeric dtype (catches stray strings/typos).
    """
    df = df.copy()

    for col in NUMERICAL_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=NUMERICAL_FEATURES + ["gender", "malnutrition"])
    after = len(df)

    if verbose and before != after:
        print(f"[preprocessing] Dropped {before - after} row(s) with missing/invalid values.")

    # Normalize text casing so "male"/"Male"/"MALE" etc. all match
    df["gender"] = df["gender"].astype(str).str.strip().str.lower()
    df["malnutrition"] = df["malnutrition"].astype(str).str.strip().str.lower()

    unknown_gender = ~df["gender"].isin(GENDER_MAP.keys())
    unknown_class = ~df["malnutrition"].isin(CLASS_MAP.keys())
    if unknown_gender.any() and verbose:
        print(f"[preprocessing] Warning: unrecognized gender value(s): "
              f"{df.loc[unknown_gender, 'gender'].unique().tolist()}")
    if unknown_class.any() and verbose:
        print(f"[preprocessing] Warning: unrecognized malnutrition label(s): "
              f"{df.loc[unknown_class, 'malnutrition'].unique().tolist()}")

    df = df[~unknown_gender & ~unknown_class].reset_index(drop=True)
    return df


def encode_gender(df: pd.DataFrame) -> pd.DataFrame:
    """Map gender strings to integers so they can feed a scikit-learn model."""
    df = df.copy()
    df["gender_encoded"] = df["gender"].map(GENDER_MAP)
    return df


def encode_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map malnutrition class strings to integers (0=Normal, 1=Moderate, 2=Severe)."""
    df = df.copy()
    df["label_encoded"] = df["malnutrition"].map(CLASS_MAP)
    return df


def normalize_numerical_features(df: pd.DataFrame, scaler=None, fit: bool = True):
    """
    Scale age/height/weight/muac to zero mean, unit variance.

    Pass a fitted `scaler` (e.g. when preprocessing new prediction input)
    with fit=False to reuse the exact scaling learned during training,
    rather than fitting a new one on a single row.
    """
    from sklearn.preprocessing import StandardScaler

    df = df.copy()
    if scaler is None:
        scaler = StandardScaler()

    if fit:
        scaled = scaler.fit_transform(df[NUMERICAL_FEATURES])
    else:
        scaled = scaler.transform(df[NUMERICAL_FEATURES])

    for i, col in enumerate(NUMERICAL_FEATURES):
        df[f"{col}_scaled"] = scaled[:, i]

    return df, scaler


def prepare_numerical_pipeline(csv_path: str, verbose: bool = True):
    """
    Convenience wrapper chaining the steps above. Returns:
      df       - cleaned dataframe with *_scaled and *_encoded columns
      scaler   - the fitted StandardScaler (needed again at predict time)
    """
    df = load_anthropometric_data(csv_path)

    if verbose:
        missing = check_missing_values(df)
        print("[preprocessing] Missing value counts:\n", missing)

    df = clean_data(df, verbose=verbose)
    df = encode_gender(df)
    df = encode_labels(df)
    df, scaler = normalize_numerical_features(df, fit=True)

    if verbose:
        print(f"[preprocessing] Ready: {len(df)} row(s) after cleaning.")

    return df, scaler


# ---------------------------------------------------------------------------
# Image branch (used once image_model.py is implemented — Step 5).
# Kept here now so the CSV's image_path column and this function are ready
# ahead of time, per the preprocessing responsibilities in the architecture.
# ---------------------------------------------------------------------------

def prepare_image_input(image_path: str, target_size: tuple = (224, 224)) -> np.ndarray:
    """
    Load an image, resize, and normalize pixel values to [0, 1] for a
    CNN (EfficientNet-B0 input size is 224x224 by default).

    Not yet wired into training/prediction — the numerical branch comes
    first. This exists so image_model.py has a stable preprocessing
    function to import once it's built.
    """
    from PIL import Image

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(image_path).convert("RGB")
    img = img.resize(target_size)
    array = np.asarray(img, dtype=np.float32) / 255.0
    return array


if __name__ == "__main__":
    # Quick manual check: run `python preprocessing.py` from backend/
    default_csv = os.path.join("..", "dataset", "anthropometric", "child_health_data.csv")
    df, scaler = prepare_numerical_pipeline(default_csv)
    print(df[["child_id", "age", "height", "weight", "muac",
              "gender_encoded", "label_encoded"]])
