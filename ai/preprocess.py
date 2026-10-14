"""
=============================================================================
2. DATA PREPROCESSING PIPELINE - ChildNutri AI
=============================================================================
Matches the 4-step architectural specification:
  1. Image Preprocessing  (Resize, Normalize, Augment)
  2. Data Cleaning        (Handle Missing Values, Outlier Detection)
  3. Data Transformation  (Normalization, Feature Engineering, Encoding)
  4. Data Split           (Train / Validation / Test Stratified Split)
=============================================================================
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
from PIL import Image

# Scikit-learn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

# PyTorch / Torchvision for Image Preprocessing
try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# =============================================================================
# 1. IMAGE PREPROCESSING (Resize, Normalize, Augment)
# =============================================================================
class ImagePreprocessor:
    """
    Handles image resizing, normalization, and data augmentation for visual malnourishment assessment.
    """
    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        self.target_size = target_size
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]

        if TORCH_AVAILABLE:
            # Training Pipeline: Includes Data Augmentation
            self.train_transforms = T.Compose([
                T.Resize(self.target_size),
                T.RandomHorizontalFlip(p=0.5),
                T.RandomRotation(degrees=15),
                T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
                T.ToTensor(),
                T.Normalize(mean=self.mean, std=self.std)
            ])

            # Validation / Inference Pipeline: Deterministic Resize & Normalize
            self.val_transforms = T.Compose([
                T.Resize(self.target_size),
                T.ToTensor(),
                T.Normalize(mean=self.mean, std=self.std)
            ])

    def preprocess_image(self, img_input, is_training: bool = False) -> Any:
        """
        Preprocesses a single image (PIL Image, path, or NumPy array).
        Returns a normalized tensor ready for model inference/training.
        """
        if isinstance(img_input, str):
            if not os.path.exists(img_input):
                raise FileNotFoundError(f"Image not found at path: {img_input}")
            img = Image.open(img_input).convert("RGB")
        elif isinstance(img_input, np.ndarray):
            img = Image.fromarray(img_input).convert("RGB")
        elif isinstance(img_input, Image.Image):
            img = img_input.convert("RGB")
        else:
            raise TypeError("Unsupported image input type.")

        if TORCH_AVAILABLE:
            transform = self.train_transforms if is_training else self.val_transforms
            return transform(img)
        else:
            # Fallback pure NumPy/PIL normalization
            img_resized = img.resize(self.target_size)
            arr = np.array(img_resized, dtype=np.float32) / 255.0
            norm_arr = (arr - np.array(self.mean)) / np.array(self.std)
            return norm_arr.transpose(2, 0, 1)

    def batch_preprocess(self, image_paths: List[str], is_training: bool = False) -> Any:
        """Preprocesses a batch of image paths."""
        tensors = [self.preprocess_image(p, is_training=is_training) for p in image_paths]
        if TORCH_AVAILABLE:
            return torch.stack(tensors)
        return np.stack(tensors)


# =============================================================================
# 2. DATA CLEANING (Handle Missing Values, Outlier Removal)
# =============================================================================
class DataCleaner:
    """
    Cleans raw anthropometric data:
    - Handles missing values via robust median/mode imputation
    - Validates physiological boundaries
    - Removes duplicates and anomalies
    """
    def __init__(self):
        self.num_imputer = SimpleImputer(strategy="median")
        self.fitted = False

        # WHO physiological bounds (0 - 60 months)
        self.bounds = {
            "age_months": (0.0, 60.0),
            "weight": (1.5, 35.0),
            "height": (40.0, 130.0),
            "muac": (6.0, 25.0),
            "head_circumference": (28.0, 60.0)
        }

    def clean(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """Cleans dataframe and imputes missing values."""
        df_clean = df.copy()

        # 1. Remove exact duplicate rows if any
        if is_training:
            df_clean = df_clean.drop_duplicates().reset_index(drop=True)

        # 2. Clean and standardize categorical columns
        if "gender" in df_clean.columns:
            df_clean["gender"] = df_clean["gender"].astype(str).str.strip().str.capitalize()
            df_clean["gender"] = df_clean["gender"].replace({"M": "Male", "F": "Female"})
            df_clean["gender"] = df_clean["gender"].fillna("Male")

        # 3. Clean numeric columns & apply physiological boundary clipping
        num_cols = ["age_months", "weight", "height", "muac", "head_circumference"]
        for col in num_cols:
            if col not in df_clean.columns:
                df_clean[col] = np.nan
            else:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
                min_val, max_val = self.bounds[col]
                df_clean[col] = df_clean[col].clip(lower=min_val, upper=max_val)

        # 4. Handle Missing Values using Imputer
        if is_training:
            df_clean[num_cols] = self.num_imputer.fit_transform(df_clean[num_cols])
            self.fitted = True
        else:
            if self.fitted:
                df_clean[num_cols] = self.num_imputer.transform(df_clean[num_cols])
            else:
                df_clean[num_cols] = self.num_imputer.fit_transform(df_clean[num_cols])

        return df_clean

    def clean_single_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans a single anthropometric dictionary."""
        df = pd.DataFrame([record])
        df_clean = self.clean(df, is_training=False)
        return df_clean.iloc[0].to_dict()


# =============================================================================
# 3. DATA TRANSFORMATION (Normalization, Feature Engineering, Encoding)
# =============================================================================
class DataTransformer:
    """
    Transforms clean anthropometric data:
    - Feature Engineering: BMI, Weight-for-Height ratio, MUAC-to-Height ratio, WHO deviation approximations
    - Feature Normalization / Scaling using StandardScaler
    - Categorical Encoding (LabelEncoder for classes, binary encoding for gender)
    """
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.fitted = False
        self.feature_names: List[str] = []

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates clinically significant derived features."""
        df_feat = df.copy()

        # BMI = weight (kg) / (height (m))^2
        height_m = df_feat["height"] / 100.0
        df_feat["bmi"] = df_feat["weight"] / (height_m ** 2)

        # Anthropometric Ratios
        df_feat["weight_to_height_ratio"] = df_feat["weight"] / df_feat["height"]
        df_feat["muac_to_height_ratio"] = df_feat["muac"] / df_feat["height"]
        df_feat["head_to_height_ratio"] = df_feat["head_circumference"] / df_feat["height"]

        # WHO Reference Expected Values
        age = df_feat["age_months"]
        expected_ht = 50.0 + 25.0 * (age / 12.0) ** 0.62
        expected_wt = 3.3 + 6.2 * (age / 12.0) ** 0.72

        df_feat["height_deficit_ratio"] = (df_feat["height"] - expected_ht) / expected_ht
        df_feat["weight_deficit_ratio"] = (df_feat["weight"] - expected_wt) / expected_wt

        # Gender encoding
        if "gender" in df_feat.columns:
            df_feat["gender_code"] = df_feat["gender"].map({"Male": 1, "Female": 0}).fillna(1).astype(int)

        return df_feat

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Fits scalers and encoders, then transforms features and target."""
        df_feat = self.engineer_features(df)

        numeric_features = [
            "age_months", "gender_code", "weight", "height", "muac", "head_circumference",
            "bmi", "weight_to_height_ratio", "muac_to_height_ratio", "head_to_height_ratio",
            "height_deficit_ratio", "weight_deficit_ratio"
        ]
        self.feature_names = numeric_features

        X_raw = df_feat[numeric_features].values
        X_scaled = self.scaler.fit_transform(X_raw)

        y_encoded = None
        if "label" in df.columns:
            y_encoded = self.label_encoder.fit_transform(df["label"].astype(str))

        self.fitted = True

        metadata = {
            "feature_names": self.feature_names,
            "classes": self.label_encoder.classes_.tolist() if y_encoded is not None else []
        }
        return X_scaled, y_encoded, metadata

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transforms new unseen data using fitted scaler."""
        if not self.fitted:
            raise RuntimeError("DataTransformer must be fitted before calling transform().")
        df_feat = self.engineer_features(df)
        X_raw = df_feat[self.feature_names].values
        return self.scaler.transform(X_raw)

    def get_feature_names(self) -> List[str]:
        """Returns the list of 12 engineered feature names."""
        if hasattr(self, "feature_names") and self.feature_names:
            return self.feature_names
        return [
            "age_months", "gender_code", "weight", "height", "muac", "head_circumference",
            "bmi", "weight_to_height_ratio", "muac_to_height_ratio", "head_to_height_ratio",
            "height_deficit_ratio", "weight_deficit_ratio"
        ]

    def transform_single_record(self, record: Dict[str, Any]) -> np.ndarray:
        """Transforms a single anthropometric record dictionary into a (1, 12) scaled feature vector."""
        df = pd.DataFrame([record])
        return self.transform(df)


# =============================================================================
# 4. DATA SPLIT (Train / Validation / Test)
# =============================================================================
class DataSplitter:
    """
    Performs stratified 70% Train / 15% Validation / 15% Test split.
    """
    def __init__(self, train_size: float = 0.70, val_size: float = 0.15, test_size: float = 0.15, random_state: int = 42):
        assert abs((train_size + val_size + test_size) - 1.0) < 1e-5, "Split fractions must sum to 1.0"
        self.train_size = train_size
        self.val_size = val_size
        self.test_size = test_size
        self.random_state = random_state

    def split(self, df: pd.DataFrame, stratify_col: Optional[str] = "label") -> Dict[str, pd.DataFrame]:
        """
        Splits dataframe into train, val, and test sets with stratification.
        """
        stratify_val = df[stratify_col] if stratify_col and stratify_col in df.columns else None

        # Step 1: Split train vs temp (val + test)
        temp_ratio = self.val_size + self.test_size
        df_train, df_temp = train_test_split(
            df,
            test_size=temp_ratio,
            random_state=self.random_state,
            stratify=stratify_val
        )

        # Step 2: Split temp into validation and test
        stratify_temp = df_temp[stratify_col] if stratify_col and stratify_col in df_temp.columns else None
        test_relative_ratio = self.test_size / temp_ratio

        df_val, df_test = train_test_split(
            df_temp,
            test_size=test_relative_ratio,
            random_state=self.random_state,
            stratify=stratify_temp
        )

        return {
            "train": df_train.reset_index(drop=True),
            "val": df_val.reset_index(drop=True),
            "test": df_test.reset_index(drop=True)
        }


# =============================================================================
# COMPLETE PREPROCESSING PIPELINE RUNNER
# =============================================================================
def run_full_preprocessing_pipeline(dataset_csv_path: str, output_dir: str) -> Dict[str, Any]:
    print("=" * 60)
    print(">> 2. DATA PREPROCESSING PIPELINE STARTING")
    print("=" * 60)

    # 1. Load Raw Dataset
    print(f"[Step 0] Loading raw dataset from: {dataset_csv_path}")
    raw_df = pd.read_csv(dataset_csv_path)
    print(f"         Total records loaded: {len(raw_df)}")

    # 2. Data Cleaning
    print("\n[Step 1] [Data Cleaning] Imputing missing values & boundary checking...")
    cleaner = DataCleaner()
    cleaned_df = cleaner.clean(raw_df, is_training=True)
    print(f"         Missing values after cleaning: {cleaned_df.isnull().sum().sum()}")

    # 3. Data Split
    print("\n[Step 2] [Data Split] Stratifying into Train (70%), Val (15%), Test (15%)...")
    splitter = DataSplitter(train_size=0.70, val_size=0.15, test_size=0.15, random_state=42)
    splits = splitter.split(cleaned_df, stratify_col="label")
    print(f"         Train set:      {len(splits['train'])} samples ({len(splits['train'])/len(cleaned_df)*100:.1f}%)")
    print(f"         Validation set: {len(splits['val'])} samples ({len(splits['val'])/len(cleaned_df)*100:.1f}%)")
    print(f"         Test set:       {len(splits['test'])} samples ({len(splits['test'])/len(cleaned_df)*100:.1f}%)")

    # 4. Data Transformation
    print("\n[Step 3] [Data Transformation] Feature engineering, Normalization & Encoding...")
    transformer = DataTransformer()
    X_train, y_train, meta = transformer.fit_transform(splits["train"])
    X_val = transformer.transform(splits["val"])
    y_val = transformer.label_encoder.transform(splits["val"]["label"].astype(str))
    X_test = transformer.transform(splits["test"])
    y_test = transformer.label_encoder.transform(splits["test"]["label"].astype(str))

    print(f"         Features generated ({len(meta['feature_names'])}): {meta['feature_names']}")
    print(f"         Target classes ({len(meta['classes'])}): {meta['classes']}")

    # 5. Image Preprocessor Setup
    print("\n[Step 4] [Image Preprocessing] Initializing Resize (224x224), Normalization & Augmentation...")
    img_preprocessor = ImagePreprocessor(target_size=(224, 224))
    print(f"         Transforms: Resize(224,224), RandomFlip, RandomRotation(15deg), ColorJitter, Normalize")

    # Save artifacts
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(cleaner, os.path.join(output_dir, "cleaner.pkl"))
    joblib.dump(transformer, os.path.join(output_dir, "transformer.pkl"))
    joblib.dump(transformer.scaler, os.path.join(output_dir, "scaler.pkl"))
    joblib.dump(transformer.label_encoder, os.path.join(output_dir, "label_encoder.pkl"))
    joblib.dump(img_preprocessor, os.path.join(output_dir, "image_preprocessor.pkl"))

    # Save split CSVs
    splits_dir = os.path.join(output_dir, "splits")
    os.makedirs(splits_dir, exist_ok=True)
    splits["train"].to_csv(os.path.join(splits_dir, "train.csv"), index=False)
    splits["val"].to_csv(os.path.join(splits_dir, "val.csv"), index=False)
    splits["test"].to_csv(os.path.join(splits_dir, "test.csv"), index=False)

    print(f"\n[OK] All preprocessing artifacts and splits saved to: {output_dir}")
    print("=" * 60)

    return {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val,     "y_val": y_val,
        "X_test": X_test,   "y_test": y_test,
        "meta": meta,
        "cleaner": cleaner,
        "transformer": transformer,
        "img_preprocessor": img_preprocessor
    }

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_path = os.path.join(base, "dataset", "anthropometric_data.csv")
    out_dir = os.path.join(base, "ai", "models")
    run_full_preprocessing_pipeline(ds_path, out_dir)
