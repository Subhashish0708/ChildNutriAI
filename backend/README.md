# backend/

## Status

| File | Status |
|---|---|
| `preprocessing.py` | ✅ Implemented — load/clean/normalize the CSV, encode gender & labels, prepare image input (function ready, not yet called by anything) |
| `numerical_model.py` | ✅ Implemented — Random Forest baseline over age/height/weight/MUAC/gender |
| `train_model.py` | ✅ Implemented — trains the numerical model, saves it + the scaler to `models/` |
| `predict.py` | ✅ Implemented — loads the saved model, scores a new child from measurements alone |
| `app.py` | ✅ Implemented (partial) — `/health` and `/predict` (numerical-only) routes only |
| `image_model.py` | ⏳ Not yet implemented — Step 5 (EfficientNet-B0) |
| `fusion_model.py` | ⏳ Not yet implemented — Step 6 (feature fusion + final classifier) |
| `explainability.py` | ⏳ Not yet implemented — Step 7 (Grad-CAM + SHAP) |
| Database persistence | ⏳ Not yet implemented — no `/children` routes yet, no MongoDB connection |

## Running it

```bash
cd backend
pip install -r requirements.txt

python train_model.py     # trains on dataset/anthropometric/child_health_data.csv, saves to models/
python predict.py         # smoke-tests a single prediction
python app.py             # starts the API on http://localhost:5000
```

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"age":3,"height":78,"weight":8,"muac":10.5,"gender":"Female"}'
```

**Important caveat:** the dataset currently has 3 rows. `train_model.py` runs end-to-end and produces a model, but the accuracy/precision/recall/F1 it reports are a pipeline smoke test, not a real evaluation — there's no meaningful train/test split with this few examples. Don't quote these metrics as if they reflect model quality; the number that matters right now is "does the pipeline run," not "how good is the model."

## Build order (don't build all of this at once)

1. ✅ `preprocessing.py` — clean and normalize the anthropometric data
2. ✅ `numerical_model.py` + `train_model.py` + `predict.py` — Random Forest baseline, working end-to-end on measurements alone
3. ⏳ `image_model.py` — EfficientNet-B0 (transfer learning) on `dataset/images/`
4. ⏳ `fusion_model.py` — concatenate visual + numerical features, FC layer + softmax
5. ⏳ `explainability.py` — Grad-CAM (image) + SHAP (numerical)
6. ⏳ Persistence — `/children` routes + a database (MongoDB, per the architecture doc)
7. ⏳ Swap the Random Forest baseline for XGBoost once the pipeline is proven

## Stack

- **Language:** Python end-to-end — same environment as `ai/`-style preprocessing (OpenCV/Pillow), EfficientNet-B0, and the tree-based numerical model.
- **Framework:** Flask (already in use in `app.py`); FastAPI would work equally well if preferred later.
- **Database:** MongoDB — a natural fit since each child record mixes structured fields (age, height, weight, MUAC) with nested/variable data (prediction history, explanation artifacts, image paths) that don't need a rigid relational schema. Not yet connected — `app.py` doesn't persist anything yet.

**Reminder:** this is a research/decision-support prototype, not a diagnostic tool. Real deployment would require a much larger, clinically validated dataset and professional oversight.
