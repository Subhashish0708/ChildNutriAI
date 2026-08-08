import pandas as pd
from pathlib import Path
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "anthropometric"
    / "child_health_data.csv"
)

MODEL_DIR = BASE_DIR / "backend" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "numerical_model.pkl"
GENDER_ENCODER_PATH = MODEL_DIR / "gender_encoder.pkl"
STATUS_ENCODER_PATH = MODEL_DIR / "status_encoder.pkl"


# --------------------------------------------------
# Load dataset
# --------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Number of records:", len(df))


# --------------------------------------------------
# Select features
# --------------------------------------------------

features = [
    "age",
    "height",
    "weight",
    "muac",
    "gender"
]

X = df[features].copy()


# --------------------------------------------------
# Encode Gender
# --------------------------------------------------

gender_encoder = LabelEncoder()

X["gender"] = gender_encoder.fit_transform(
    X["gender"]
)


# --------------------------------------------------
# Encode Target
# --------------------------------------------------

status_encoder = LabelEncoder()

y = status_encoder.fit_transform(
    df["malnutrition_status"]
)


# --------------------------------------------------
# Display information
# --------------------------------------------------

print("\nFeatures used:")
print(features)

print("\nGender classes:")
print(gender_encoder.classes_)

print("\nMalnutrition classes:")
print(status_encoder.classes_)


# --------------------------------------------------
# Train Random Forest
# --------------------------------------------------

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)


# --------------------------------------------------
# Save model
# --------------------------------------------------

joblib.dump(model, MODEL_PATH)

joblib.dump(
    gender_encoder,
    GENDER_ENCODER_PATH
)

joblib.dump(
    status_encoder,
    STATUS_ENCODER_PATH
)


print("\nModel trained successfully!")

print("Model saved to:")
print(MODEL_PATH)

print("\nEncoders saved successfully!")