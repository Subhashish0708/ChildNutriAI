from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "image_model.pt"


# --------------------------------------------------
# Device
# --------------------------------------------------

DEVICE = torch.device("cpu")


# --------------------------------------------------
# Load checkpoint
# --------------------------------------------------

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=True
)


# --------------------------------------------------
# Create EfficientNet-B0
# --------------------------------------------------

model = models.efficientnet_b0(
    weights=None
)


# Replace classifier with the number
# of classes used during training
model.classifier[1] = nn.Linear(
    model.classifier[1].in_features,
    checkpoint["num_classes"]
)


# Load trained weights
model.load_state_dict(
    checkpoint["state_dict"]
)


model = model.to(DEVICE)
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
# Extract visual features
# --------------------------------------------------

def extract_visual_features(image_path):

    image = Image.open(image_path).convert("RGB")

    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0)

    image_tensor = image_tensor.to(DEVICE)

    with torch.no_grad():

        features = feature_extractor(
            image_tensor
        )

    return features.squeeze(0)


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("       ChildNutri AI - Visual Feature Extraction")
    print("=" * 60)

    # Test image from the dataset
    image_path = (
    BASE_DIR.parent
    / "dataset"
    / "images"
    / "normal"
    / "child1.png"
)

    print("\nImage:")
    print(image_path)

    if not image_path.exists():

        print("\nERROR: Test image not found.")

        print("\nExpected location:")
        print(image_path)

        raise SystemExit(1)

    features = extract_visual_features(
        image_path
    )

    print("\nImage preprocessing:")
    print("Resize:", checkpoint["img_size"], "x",
          checkpoint["img_size"])

    print("\nArchitecture:")
    print(checkpoint["architecture"])

    print("\nVisual feature vector shape:")
    print(features.shape)

    print("\nNumber of visual features:")
    print(features.numel())

    print("\nVisual feature extraction completed!")

    print("=" * 60)