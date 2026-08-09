# ChildNutriAI

An AI-assisted child malnutrition screening tool. A health worker registers a child, uploads two photos, and receives a nutritional-risk prediction with recommendations — intended for use in community health centers and field screening camps.

**Status:** Milestone 2 — frontend flow complete (7 pages) with a hardcoded prediction. Architecture below reflects the Review 2 multi-modal design; `backend/` and `ai/` are not yet implemented.

## Folder structure

```
ChildNutriAI/
│
├── frontend/       # Static HTML/CSS/JS — home, register, upload, processing, dashboard, about, contact
├── backend/        # (planned) API layer — not yet implemented
├── ai/             # (planned) preprocessing + prediction pipeline — not yet implemented
├── dataset/        # (planned) training images + labels
├── models/         # (planned) trained model weights
├── uploads/        # (planned) runtime storage for uploaded photos
├── reports/        # (planned) generated per-child PDF/HTML reports
├── docs/           # research notes, review prep
└── README.md
```

## Running the frontend

No build step needed — it's plain HTML/CSS/JS.

```bash
cd frontend
python3 -m http.server 8000
# then open http://localhost:8000
```

Or just double-click `frontend/index.html` to open it directly in a browser (image upload, the processing redirect, and the dashboard's localStorage handoff all work without a server).

## Page flow

```
Home Page
  ↓
Register Child
  ↓
Upload Child Image
  ↓
AI Processing (Loading)
  ↓
Dashboard
```

## What's built in this milestone

1. **Home** (`frontend/index.html`) — project intro and the 5-step pipeline overview.
2. **Register child** (`frontend/register.html`) — name, age, gender, height, weight, MUAC, parent name.
3. **Upload images** (`frontend/upload.html`) — face + full-body photo, previewed client-side, Upload then Next buttons.
4. **AI processing** (`frontend/processing.html`) — animated loading state that auto-redirects to the dashboard after ~4 seconds.
5. **Dashboard** (`frontend/dashboard.html`) — hardcoded prediction (Moderate Malnutrition, 94% confidence, Medium risk, Healthy progress) with a Download report button, clearly flagged as placeholder data.
6. **About** (`frontend/about.html`) — project introduction, objectives, technologies, algorithms.
7. **Contact** (`frontend/contact.html`) — project guide / student / email / department placeholders.

## System architecture

**Status:** this is the Review 2 architecture — a multi-modal fusion pipeline replacing the earlier single-path diagram. It exists to answer two panel questions directly: *is this technically compatible as one buildable system*, and *what is actually being compared/predicted*.

```
                    CHILD DATA
                       │
          ┌────────────┴────────────┐
          │                         │
     CHILD IMAGE              HEALTH DATA
   (face + full body)      (age, height, weight, MUAC)
          │                         │
          ▼                         ▼
  Image Preprocessing       Data Cleaning /
  (resize, normalize,        Normalization
   noise reduction,                │
   quality check)                  │
          │                        │
          ▼                        ▼
    EfficientNet-B0              XGBoost
   (feature extraction)   (anthropometric analysis)
          │                        │
          ▼                        ▼
   Visual Feature Vector    Numerical Feature Vector
          │                        │
          └────────────┬───────────┘
                        ▼
                 FEATURE FUSION
                  (concatenation)
                        │
                        ▼
         Fully Connected Layer + Softmax
              (final classifier)
                        │
          ┌─────────────┼─────────────┐
          ▼              ▼             ▼
       Normal        Moderate        Severe
                        │
                        ▼
                 Explainable AI
              ┌──────────┴──────────┐
              ▼                     ▼
          Grad-CAM                SHAP
      (why the image           (why the numbers
       drove this call)         drove this call)
              │                     │
              └──────────┬──────────┘
                         ▼
             Nutrition Recommendation
                         │
                         ▼
             Growth Monitoring & Reports
                         │
                         ▼
                     Dashboard
```

**Why this isn't just "compare the image to other images":** the image branch never does image-to-image matching. EfficientNet-B0 extracts a learned visual feature vector from the child's photo; XGBoost separately turns age/height/weight/MUAC into a numerical feature vector after cleaning and normalization. The two vectors are concatenated (feature fusion) and passed through one classification layer. So the system is doing:

```
Visual representation + health measurements → prediction
```

not `Image A vs Image B`.

### Recommended technology mapping

| Component | Technology / Algorithm | Purpose |
|---|---|---|
| Image processing | OpenCV + Pillow | Resize, crop, normalize |
| Image feature extraction | EfficientNet-B0 | Extract visual features |
| Numerical data | XGBoost | Analyze anthropometric parameters |
| Feature fusion | Concatenation | Combine image + numerical features |
| Classification | Fully connected layer + Softmax | Final nutritional class |
| Explainability (image) | Grad-CAM | Explain which image regions drove the prediction |
| Explainability (numerical) | SHAP | Explain which measurements drove the prediction |
| Backend | Python | Connects all AI modules in one environment |
| Database | MongoDB | Store child records |
| Frontend | HTML/CSS/JS | User interface |

Python is the common environment for the whole AI pipeline, which is what makes this technically compatible as a single backend: OpenCV/Pillow handle preprocessing, EfficientNet-B0 and XGBoost both run natively in Python, and their outputs are just numeric vectors that can be concatenated and fed to a small classifier without switching languages or frameworks anywhere in the chain.

### Stage-by-stage

**Child image** — face + full-body photo captured through the upload page.

**Health data** — age, height, weight, and MUAC entered at registration. (BMI can be added later if useful, but the recommendation for the main prototype is to keep just these four — adding more parameters doesn't make the project stronger.)

**Preprocessing (image)** — resize, normalize, reduce noise, check image quality, and (during training only) augment the dataset.

**Preprocessing (health data)** — clean and normalize the four numerical fields before they reach XGBoost.

**Feature extraction** — EfficientNet-B0 (image branch) and XGBoost (numerical branch) each produce a feature vector independently.

**Feature fusion** — the two vectors are concatenated into one combined representation.

**Final classifier** — a fully connected layer + softmax maps the fused vector to Normal / Moderate / Severe.

**Explainable AI** — Grad-CAM highlights which parts of the image influenced the call; SHAP shows which measurements influenced it. Together these let the dashboard say *why*, not just *what*.

**Nutrition recommendation** — the predicted class drives rule-based dietary guidance, not free-text generation, so advice stays clinically consistent.

**Growth monitoring & reports** — each assessment is stored against the child's record so repeat visits build a longitudinal growth trend, and a report can be generated per visit.

**Dashboard** — the health worker's view: measurements, prediction, confidence, explanation, recommendation, and (eventually) growth trend, all in one screen.

## Research gap (for Review 2)

> Existing AI-based child malnutrition assessment approaches demonstrate the potential of computer vision and anthropometric analysis for nutritional screening. However, there is still scope for a unified system that combines image-derived visual features with anthropometric parameters while also providing explainable predictions and continuous child health monitoring.

**Proposed solution:** ChildNutriAI combines image-based deep learning, anthropometric analysis, feature fusion, explainable AI, growth monitoring, and personalized nutrition support in a single platform.

Primary reference: *NutriAI: AI-Powered Child Malnutrition Assessment in Low-Resource Environments*. Supporting literature should be organized around five areas — traditional anthropometric assessment, image-based malnutrition detection, deep learning models (ResNet/EfficientNet/CNNs), multi-modal assessment (the actual gap this project fills), and explainable AI (Grad-CAM/SHAP) — rather than general AI papers, per the Review 1 feedback to increase topic-specific research. See `docs/research_notes.md` for the full breakdown and pre-Review-2 build order.

## Roadmap

- [x] Frontend scaffold (home, register, upload, processing, dashboard, about, contact) with dummy data
- [ ] Backend API (`backend/`) in Python to persist children, images, and predictions to MongoDB
- [ ] Image preprocessing (OpenCV/Pillow) + EfficientNet-B0 feature extraction (`ai/`)
- [ ] Anthropometric preprocessing + XGBoost model (`ai/`), trained on `dataset/`
- [ ] Feature fusion + final classifier (fully connected layer + softmax)
- [ ] Grad-CAM and SHAP explainability outputs
- [ ] Replace hardcoded dashboard values with live predictions
- [ ] Growth monitoring — trend charts across repeat visits
- [ ] PDF report generation (`reports/`)

**Note on the dataset:** until a genuine research dataset is obtained, label whatever CSV/images are in `dataset/` clearly as prototype/sample data when presenting — not an official WHO or clinical dataset.
