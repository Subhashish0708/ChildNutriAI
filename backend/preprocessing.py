import pandas as pd
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "anthropometric" / "child_health_data.csv"


def load_dataset():
    print("Loading dataset...")

    df = pd.read_csv(DATASET_PATH)

    print("\nDataset loaded successfully!")
    print("Shape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nDataset:")
    print(df)

    return df


def check_dataset(df):
    print("\n--- Dataset Information ---")

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nMalnutrition classes:")
    print(df["malnutrition"].value_counts())

    print("\nData types:")
    print(df.dtypes)


if __name__ == "__main__":
    data = load_dataset()
    check_dataset(data)