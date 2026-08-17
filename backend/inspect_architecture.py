from pathlib import Path
import torch

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "image_model.pt"

print("=" * 60)
print("       ChildNutri AI - Architecture Information")
print("=" * 60)

if not MODEL_PATH.exists():
    print("ERROR: image_model.pt not found!")
    print("Expected location:")
    print(MODEL_PATH)
    raise SystemExit(1)

checkpoint = torch.load(
    MODEL_PATH,
    map_location="cpu",
    weights_only=True
)

print("\nArchitecture:")
print(checkpoint["architecture"])

print("\nNumber of classes:")
print(checkpoint["num_classes"])

print("\nImage size:")
print(checkpoint["img_size"])

print("\nNormalization mean:")
print(checkpoint["normalize_mean"])

print("\nNormalization standard deviation:")
print(checkpoint["normalize_std"])

print("\n" + "=" * 60)
print("Architecture inspection completed.")
print("=" * 60)