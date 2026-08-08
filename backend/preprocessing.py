import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "anthropometric"
    / "child_health_data.csv"
)


def load_dataset():
    print("Loading dataset...")

    df = pd.read_csv(DATASET_PATH)

    print("\nDataset loaded successfully!")
    print("Shape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    return df


def check_dataset(df):
    print("\n--- Dataset Information ---")

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nMalnutrition classes:")
    print(df["malnutrition_status"].value_counts())

    print("\nData types:")
    print(df.dtypes)


def prepare_features(df):
    print("\n--- Preparing Numerical Features ---")

    # Features used by the numerical branch
    feature_columns = [
        "age",
        "height",
        "weight",
        "muac",
        "gender"
    ]

    X = df[feature_columns].copy()

    # Encode gender
    gender_encoder = LabelEncoder()
    X["gender"] = gender_encoder.fit_transform(X["gender"])

    # Target variable
    y = df["malnutrition_status"]

    print("\nFeatures:")
    print(X)

    print("\nTarget:")
    print(y)

    print("\nGender encoding:")
    for original, encoded in zip(
        gender_encoder.classes_,
        gender_encoder.transform(gender_encoder.classes_)
    ):
        print(f"{original} -> {encoded}")

    return X, y, gender_encoder


if __name__ == "__main__":

    data = load_dataset()

    check_dataset(data)

    X, y, gender_encoder = prepare_features(data)

    print("\nPreprocessing completed successfully!")