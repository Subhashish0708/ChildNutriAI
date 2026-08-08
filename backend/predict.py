from pathlib import Path
import joblib
import pandas as pd


# Project paths
BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "numerical_model.pkl"
GENDER_ENCODER_PATH = BASE_DIR / "models" / "gender_encoder.pkl"
STATUS_ENCODER_PATH = BASE_DIR / "models" / "status_encoder.pkl"


# Load trained model and encoders
model = joblib.load(MODEL_PATH)
gender_encoder = joblib.load(GENDER_ENCODER_PATH)
status_encoder = joblib.load(STATUS_ENCODER_PATH)


print("===================================")
print("      ChildNutri AI Prediction")
print("===================================")

# Get child information
age = float(input("Enter age: "))
height = float(input("Enter height (cm): "))
weight = float(input("Enter weight (kg): "))
muac = float(input("Enter MUAC (cm): "))
gender = input("Enter gender (Male/Female): ").strip()


# Validate gender
if gender not in gender_encoder.classes_:
    print("\nInvalid gender.")
    print("Available options:", list(gender_encoder.classes_))
    exit()


# Encode gender
gender_encoded = gender_encoder.transform([gender])[0]


# Create input DataFrame
input_data = pd.DataFrame([{
    "age": age,
    "height": height,
    "weight": weight,
    "muac": muac,
    "gender": gender_encoded
}])


# Make prediction
prediction = model.predict(input_data)[0]

# Convert prediction back to class name
predicted_status = status_encoder.inverse_transform([prediction])[0]


print("\n===================================")
print("Prediction Result")
print("===================================")
print("Malnutrition Status:", predicted_status)
print("===================================")