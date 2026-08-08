from pathlib import Path
import pickle
import torch


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "image_model.pt"
CLASS_NAMES_PATH = BASE_DIR / "models" / "image_class_names.pkl"


print("=" * 60)
print("        ChildNutri AI - Image Model Inspection")
print("=" * 60)


# --------------------------------------------------
# Check files
# --------------------------------------------------

print("\nChecking files...")

if not MODEL_PATH.exists():
    print(f"ERROR: Model file not found:")
    print(MODEL_PATH)
    raise SystemExit(1)

if not CLASS_NAMES_PATH.exists():
    print(f"ERROR: Class names file not found:")
    print(CLASS_NAMES_PATH)
    raise SystemExit(1)

print("Image model found:")
print(MODEL_PATH)

print("\nClass names file found:")
print(CLASS_NAMES_PATH)


# --------------------------------------------------
# Inspect class names
# --------------------------------------------------

print("\n" + "=" * 60)
print("CLASS NAMES")
print("=" * 60)

with open(CLASS_NAMES_PATH, "rb") as f:
    class_names = pickle.load(f)

print("Type:", type(class_names))
print("Classes:", class_names)

if isinstance(class_names, (list, tuple)):
    print("Number of classes:", len(class_names))


# --------------------------------------------------
# Load PyTorch checkpoint safely
# --------------------------------------------------

print("\n" + "=" * 60)
print("PYTORCH MODEL CHECKPOINT")
print("=" * 60)

try:
    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu",
        weights_only=True
    )

    print("Checkpoint loaded successfully.")
    print("Checkpoint type:", type(checkpoint))

except Exception as e:
    print("\nThe checkpoint could not be loaded using")
    print("weights_only=True.")
    print("This can happen if the file contains a full")
    print("PyTorch model object instead of only weights.")

    print("\nError:")
    print(e)

    print("\nNo unsafe loading will be performed automatically.")
    raise SystemExit(1)


# --------------------------------------------------
# Inspect checkpoint
# --------------------------------------------------

print("\n" + "=" * 60)
print("CHECKPOINT INFORMATION")
print("=" * 60)

if isinstance(checkpoint, dict):

    print("Checkpoint keys:")

    for key in checkpoint.keys():
        print(" -", key)

    print("\nNumber of checkpoint entries:", len(checkpoint))

    # Inspect tensor information
    print("\nTensor information:")

    tensor_count = 0

    for key, value in checkpoint.items():

        if torch.is_tensor(value):

            tensor_count += 1

            print(
                f"{key}: "
                f"shape={tuple(value.shape)}, "
                f"dtype={value.dtype}"
            )

        elif isinstance(value, dict):

            print(
                f"{key}: nested dictionary "
                f"({len(value)} entries)"
            )

        else:

            print(
                f"{key}: "
                f"type={type(value).__name__}"
            )

    print("\nTensor entries found:", tensor_count)

else:

    print("Checkpoint is not a dictionary.")
    print("Type:", type(checkpoint))


print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)