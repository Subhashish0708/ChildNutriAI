from pathlib import Path
import torch
import pandas as pd
import joblib
from torchvision import models
import torch.nn as nn
from PIL import Image
from torchvision import transforms


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "image_model.pt"

DATASET_PATH = (
    BASE_DIR.parent
    / "dataset"
    / "anthropometric"
    / "child_health_data.csv"
)

IMAGE_BASE_DIR = (
    BASE_DIR.parent
    / "dataset"
)


# --------------------------------------------------
# Load image model
# --------------------------------------------------

print("Loading image model...")

checkpoint = torch.load(
    MODEL_PATH,
    map_location="cpu",
    weights_only=True
)

model = models.efficientnet_b0(weights=None)

model.classifier[1] = nn.Linear(
    model.classifier[1].in_features,
    checkpoint["num_classes"]
)

model.load_state_dict(checkpoint["state_dict"])

model.eval()


# --------------------------------------------------
# Image preprocessing
# --------------------------------------------------

transform = transforms.Compose([
    transforms.Resize(
        (checkpoint["img_size"], checkpoint["img_size"])
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=checkpoint["normalize_mean"],
        std=checkpoint["normalize_std"]
    )
])


# --------------------------------------------------
# Feature extractor
# --------------------------------------------------

feature_extractor = nn.Sequential(
    model.features,
    model.avgpool,
    nn.Flatten()
)

feature_extractor.eval()


# --------------------------------------------------
# Load dataset
# --------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Records:", len(df))


# --------------------------------------------------
# Select first child for testing
# --------------------------------------------------

child = df.iloc[0]

print("\nChild information:")
print(child)


# --------------------------------------------------
# Numerical features
# --------------------------------------------------

age = float(child["age"])
height = float(child["height"])
weight = float(child["weight"])
muac = float(child["muac"])


# Encode gender
gender_encoder = joblib.load(
    BASE_DIR / "models" / "gender_encoder.pkl"
)

gender = child["gender"]

gender_encoded = gender_encoder.transform(
    [gender]
)[0]


numerical_features = torch.tensor(
    [
        age,
        height,
        weight,
        muac,
        gender_encoded
    ],
    dtype=torch.float32
)


# --------------------------------------------------
# Find child image
# --------------------------------------------------

image_relative_path = str(
    child["image_path"]
)

image_path = IMAGE_BASE_DIR / image_relative_path

print("\nImage path:")
print(image_path)


if not image_path.exists():

    print("\nERROR: Image not found!")

    raise SystemExit(1)


# --------------------------------------------------
# Extract visual features
# --------------------------------------------------

print("\nExtracting visual features...")

image = Image.open(
    image_path
).convert("RGB")

image_tensor = transform(image)

image_tensor = image_tensor.unsqueeze(0)


with torch.no_grad():

    visual_features = feature_extractor(
        image_tensor
    ).squeeze(0)


print("Visual feature size:")
print(visual_features.shape)


# --------------------------------------------------
# Feature Fusion
# --------------------------------------------------

print("\nPerforming feature fusion...")

numerical_features = numerical_features.flatten()
visual_features = visual_features.flatten()

fused_features = torch.cat(
    [
        visual_features,
        numerical_features
    ]
)


# --------------------------------------------------
# Display result
# --------------------------------------------------

print("\n" + "=" * 60)
print("             FEATURE FUSION RESULT")
print("=" * 60)

print("\nVisual features:")
print(visual_features.shape[0])

print("Numerical features:")
print(numerical_features.shape[0])

print("Total fused features:")
print(fused_features.shape[0])

print("\nExpected:")
print("1280 + 5 = 1285")

print("\nFeature fusion completed successfully!")

print("=" * 60)