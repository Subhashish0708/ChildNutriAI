# ai/

Not yet implemented — reserved for the prediction pipeline.

**Two branches, fused into one classifier** (see architecture in root `README.md`):

## Image branch
1. **Preprocessing** — OpenCV/Pillow: resize, normalize, reduce noise, quality check; augmentation during training only.
2. **Feature extraction** — EfficientNet-B0 (transfer-learned), producing a visual feature vector. This is *not* image-to-image comparison — the model learns representative visual features, it doesn't match the child's photo against a reference set.

## Numerical branch
1. **Preprocessing** — clean and normalize age, height, weight, MUAC.
2. **Feature extraction** — XGBoost over the four anthropometric fields, producing a numerical feature vector.

Keep the parameter set to these four for the main prototype (age, height, weight, MUAC); BMI can be added later if it proves useful, but adding parameters just to look more comprehensive isn't recommended.

## Fusion + classification
- **Feature fusion** — concatenate the visual and numerical vectors.
- **Final classifier** — fully connected layer + softmax → Normal / Moderate / Severe.

## Explainability
- **Grad-CAM** — highlights which regions of the image influenced the prediction.
- **SHAP** — shows which anthropometric features influenced the prediction.

Together these let the dashboard explain *why* a class was predicted, not just report the class — this is what the recommendation and Growth Monitoring & Reports stages downstream consume.

## Suggested file layout (once implemented)

```
ai/
├── preprocessing/
│   ├── image_preprocessing.py    # resize, normalize, quality check
│   └── data_preprocessing.py     # clean/normalize anthropometric fields
├── models/
│   ├── image_model.py            # EfficientNet-B0 feature extractor
│   ├── numerical_model.py        # XGBoost model
│   └── fusion_classifier.py      # concatenation + FC + softmax
├── explainability/
│   ├── gradcam.py
│   └── shap_explainer.py
└── train.py
```

Training code and saved weights are not part of this milestone — the dashboard currently displays a hardcoded prediction. Trained weights should be saved to `../models/`, not committed here.
