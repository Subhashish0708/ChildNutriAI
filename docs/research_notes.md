# Research Notes — Review 2

Review 1 feedback: *"increase topic-specific research."* This organizes the literature survey around child malnutrition + AI + image analysis specifically, rather than general AI papers.

**Primary reference:** *NutriAI: AI-Powered Child Malnutrition Assessment in Low-Resource Environments*

## Research areas

**1. Child malnutrition assessment (traditional)**
How malnutrition is conventionally identified — height, weight, age, MUAC, and other anthropometric indicators. This is the baseline the project has to justify improving on.

**2. Image-based malnutrition detection**
Prior work using facial images, full-body images, computer vision, and deep learning for nutritional or health screening.

**3. Deep learning models**
CNN-based approaches generally, with ResNet, EfficientNet, and DenseNet as the specific architectures to read up on — these support the methodology choice of EfficientNet-B0 for the image branch.

**4. Multi-modal assessment** — *the core of the research gap*
Existing approaches tend to use *either* images *or* anthropometric measurements, not both together in one pipeline.

**5. Explainable AI**
Grad-CAM (image explanations) and SHAP (tabular/numerical explanations) — supports the explainability module in the architecture.

## Research gap

> Existing AI-based child malnutrition assessment approaches demonstrate the potential of computer vision and anthropometric analysis for nutritional screening. However, there is still scope for a unified system that combines image-derived visual features with anthropometric parameters while also providing explainable predictions and continuous child health monitoring.

## Proposed solution

ChildNutriAI combines image-based deep learning, anthropometric analysis, feature fusion, explainable AI, growth monitoring, and personalized nutrition support in a single platform.

## What to tell the panel (technical compatibility)

> For technical compatibility, we are using Python as the common environment for the AI pipeline. OpenCV and Pillow will handle image preprocessing, EfficientNet-B0 will extract visual features, and XGBoost will process anthropometric parameters. The outputs will then be combined through feature fusion and passed to a final classification layer. Therefore, all major AI components can be integrated within a single Python-based backend.

## What to build before Review 2 (in order)

1. **Dataset** — `dataset/images/` + `dataset/anthropometric/child_health_data.csv` with columns `child_id, age, height, weight, muac, malnutrition_status, image_path`. Clearly label as prototype/sample data, not an official dataset, unless a genuine research dataset has been obtained.
2. **Image preprocessing** — resize → normalize → quality check → model input, as a runnable script.
3. **Image model** — EfficientNet-B0 via transfer learning (not trained from scratch).
4. **Numerical model** — XGBoost on age/height/weight/MUAC, evaluated with accuracy, precision, recall, F1-score.
5. **Fusion** — concatenate the EfficientNet-B0 and XGBoost feature vectors and pass through a final classifier — this is the step that makes the project genuinely multi-modal rather than "just an image classifier."

Don't try to implement the full system (explainability, growth monitoring, reports) before Review 2 — steps 1–5 above are the demonstrable core.
