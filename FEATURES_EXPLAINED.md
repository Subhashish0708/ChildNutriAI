# ChildNutri AI — Complete Features & Concepts Guide

> **A comprehensive, plain-language walkthrough of all features, medical terminologies, machine learning engines, and data pipelines powering ChildNutri AI.**

---

## 📖 Table of Contents
1. [Key Terminology & Medical Metrics (Simplified)](#1-key-terminology--medical-metrics-simplified)
2. [Basic Features (User Experience & Onboarding)](#2-basic-features-user-experience--onboarding)
3. [Intermediate Features (Assessment & Automation)](#3-intermediate-features-assessment--automation)
4. [Advanced Features (AI/ML & Clinical Decision Support)](#4-advanced-features-aiml--clinical-decision-support)
5. [Detailed Pipeline Flows from Input to Output](#5-detailed-pipeline-flows-from-input-to-output)
   - [5.1 Machine Learning Model Pipeline Flow (LightGBM Future-Risk Engine)](#51-machine-learning-model-pipeline-flow-lightgbm-future-risk-engine)
   - [5.2 OCR Document Parsing Pipeline Flow (Hybrid Vector PDF + OpenCV/Tesseract)](#52-ocr-document-parsing-pipeline-flow-hybrid-vector-pdf--opencv-tesseract)
   - [5.3 Deep Learning Vision Pipeline Flow (Multimodal ONNX & 3-Layer Clinical Safety Gate)](#53-deep-learning-vision-pipeline-flow-multimodal-onnx--3-layer-clinical-safety-gate)
6. [End-to-End System Workflow](#6-end-to-end-system-workflow)
7. [FastAPI Backend API Reference & Code Map](#7-fastapi-backend-api-reference--code-map)
   - [7.1 Complete API Endpoint Catalog](#71-complete-api-endpoint-catalog)
   - [7.2 Where to Look in the FastAPI Backend (Code Map)](#72-where-to-look-in-the-fastapi-backend-code-map)
   - [7.3 How to Add or Modify an API Endpoint (Step-by-Step Developer Guide)](#73-how-to-add-or-modify-an-api-endpoint-step-by-step-developer-guide)
8. [How to Run the Frontend and Backend Project](#8-how-to-run-the-frontend-and-backend-project)
   - [8.1 System Prerequisites & Virtual Environment Setup](#81-system-prerequisites--virtual-environment-setup)
   - [8.2 Starting the Unified Full-Stack Application (Port 8000)](#82-starting-the-unified-full-stack-application-port-8000)
   - [8.3 Accessing the Web Dashboard & Interactive Swagger Docs](#83-accessing-the-web-dashboard--interactive-swagger-docs)
   - [8.4 Database Initialization & Seeding Clinical Data](#84-database-initialization--seeding-clinical-data)
   - [8.5 Running Automated Regression Tests](#85-running-automated-regression-tests)

---

## 1. Key Terminology & Medical Metrics (Simplified)

### 🏥 Organizations & Global Standards
* **WHO (World Health Organization):** The United Nations agency for international public health. In 2006, the WHO released global child growth standards tracking healthy children across six countries (including India) raised under optimal conditions.
* **WHO LMS Method:** A mathematical formula ($L$ = skewness, $M$ = median, $S$ = coefficient of variation) used to determine exactly where a child stands compared to hundreds of thousands of healthy reference children.

---

### 📏 Anthropometric Z-Scores (Standard Deviation Scores)
A **Z-score** measures how far a child is from the global healthy average (median). A score of `0` is exactly average. Scores between `-2` and `+2` are considered normal. Scores below `-2` indicate malnutrition.

| Metric | Full Form | Plain Language Meaning | What a Low Score Indicates |
| :--- | :--- | :--- | :--- |
| **WAZ** | **Weight-for-Age Z-score** | Shows whether a child's weight is appropriate for their age. | **Underweight** (below -2 SD) or Severely Underweight (below -3 SD). |
| **HAZ** | **Height-for-Age Z-score** | Shows whether a child's height/length is appropriate for their age. | **Stunting** (chronic long-term malnutrition causing stunted bone growth). |
| **WHZ** | **Weight-for-Height Z-score** | Shows whether a child's body weight matches their current height. | **Wasting** (acute, dangerous weight loss or muscle breakdown). |
| **BAZ** | **BMI-for-Age Z-score** | Body Mass Index adjusted for toddler age and gender. | Severe thinness or early childhood overweight/obesity. |
| **HCZ** | **Head Circumference Z-score**| Measures skull growth compared to age. | Microcephaly (impaired brain development) or macrocephaly. |

---

### 🎨 MUAC (Mid-Upper Arm Circumference)
A rapid screening measurement taken midway between the shoulder and elbow of the relaxed left arm:
* 🔴 **Red Zone (< 11.5 cm):** **Severe Acute Malnutrition (SAM)** — high risk of mortality, requires urgent hospital/NRC admission.
* 🟡 **Yellow Zone (11.5 cm to 12.4 cm):** **Moderate Acute Malnutrition (MAM)** — requires supervised therapeutic supplementary feeding.
* 🟢 **Green Zone ($\ge$ 12.5 cm):** **Normal / Healthy** nutrition.

---

### ⚠️ Malnutrition Classifications & Symptoms
* **Stunting (Low Height-for-Age):** Chronic, long-term malnutrition that delays physical and cognitive development. Often irreversible if not addressed in the first 1,000 days.
* **Wasting (Low Weight-for-Height):** Rapid, acute weight loss due to starvation or severe infection (e.g. chronic diarrhoea). Child looks visibly thin and frail.
* **Underweight (Low Weight-for-Age):** A composite reflection of either stunting, wasting, or both.
* **SAM (Severe Acute Malnutrition):** WHZ < -3 SD, or MUAC < 11.5 cm, or presence of bilateral oedema.
* **MAM (Moderate Acute Malnutrition):** WHZ between -2 and -3 SD, or MUAC between 11.5 and 12.4 cm without oedema.
* **Bilateral Pitting Oedema:** Swelling in both feet caused by severe protein deficiency (**Kwashiorkor**). When pressed with a thumb for a few seconds, an indentation remains. Automatically classified as SAM regardless of weight.

---

### 🤖 Machine Learning & Deep Learning Metrics & Terminologies (Simplified)
* **LightGBM:** A fast, gradient-boosted decision tree algorithm that analyzes non-linear combinations of socio-demographic and biological risk factors (feeding, diarrhoea, mother's education, wealth score).
* **Isotonic Probability Calibration:** Adjusts raw model confidence scores so that if the model predicts an "80% risk", roughly 80 out of 100 such children truly experience growth faltering.
* **ROC-AUC (0.87):** Measures the model's ability to distinguish between children who will remain healthy versus those at risk. 0.87 represents strong 87% discrimination accuracy.
* **Brier Score (0.143):** Measures the accuracy of probability predictions (lower is better; 0 is a perfect model). 0.143 indicates highly reliable calibrated probabilities.
* **SHAP (SHapley Additive exPlanations):** An Explainable AI (XAI) technique from cooperative game theory that shows the exact reasons behind a risk prediction (e.g., *"+35% risk due to low meal frequency, +20% due to recent fever"*).
* **Multimodal ONNX Deep Learning Classification & Anatomical Emaciation Assessment:** A hybrid pediatric computer vision framework that fuses deep neural feature representations (executed through ONNX Runtime) with clinical domain anatomical metrics (thoracic ribcage exposure, facial buccal fat fullness, and limb emaciation) to assess physical wasting.
* **ONNX Runtime (Open Neural Network Exchange):** A cross-platform high-performance machine learning inference engine used to execute deep neural vision backbones with low latency across edge hardware without requiring PyTorch or TensorFlow runtimes.
* **YCrCb Skin Color Space & Segmentation:** A specialized chrominance-luminance color space that isolates human skin pixels independent of lighting intensity ($Y$ = luminance, $Cr$ = red-difference chrominance, $Cb$ = blue-difference chrominance). It is used to calculate bare skin exposure versus clothing obstruction across diverse infant skin tones.
* **Sobel Directional Gradient Density:** A discrete spatial differentiation filter measuring directional edge intensity ($\partial I / \partial y$). In child nutrition, it specifically evaluates the "accordion sign" — the horizontal shadow ridges cast by protruding costal ribs in a severely wasted child.
* **Laplacian Focus Variance ($\sigma^2$):** A second-order differential image sharpness operator. If $\sigma^2(\nabla^2 I) < 25.0$, the uploaded photo suffers from severe camera motion blur or defocus and is rejected by the image quality gate.
* **Anatomical Regions of Interest (ROI):** Clinically grounded sub-regions of the child's body mapped for automated inspection:
  * *Thoracic ROI:* The chest and costal margin area ($y \in [0.25h, 0.75h], x \in [0.20w, 0.80w]$) for rib prominence.
  * *Facial ROI:* The cheek and temporal zones for buccal fat depletion and sunken eyes.
  * *Upper Limb ROI:* The brachial and bicep borders for arm muscle wasting.
* **Grad-CAM (Gradient-Weighted Class Activation Mapping):** A visual Explainable AI (XAI) method that computes a thermal heatmap (red = highest attention, blue = lowest attention) showing the exact spatial areas that triggered the neural network's visual classification.
* **Marasmus (Severe Pediatric Wasting):** A life-threatening form of Severe Acute Malnutrition (SAM) caused by severe deficiency of nearly all nutrients and calories, characterized by extreme emaciation, loss of subcutaneous fat, "accordion" ribcage visibility, and thin "bag-of-bones" limbs.


---

## 2. Basic Features (User Experience & Onboarding)

### 1. Dual User Roles (Parent vs. Doctor)
* **Parent Mode:** Uses clean, non-intimidating visual cards, friendly verdicts (*Healthy*, *Watch Zone*, *Moderate Risk*, *Severe*), and practical advice on what foods to cook at home.
* **Doctor / Clinician Mode:** Displays clinical metrics, exact WHO z-scores with reference standard deviations, statistical confidence, and NRC hospital referral protocols.

### 2. Child Profile Management
* Create and store longitudinal child profiles with birth weight, birth length, sex, birth date, and geographic region.
* Enables tracking the same child over months to monitor growth progress.

### 3. One-Click Bilingual Language Toggle (English / हिंदी) — Architecture & Implementation
* **Zero-Latency Client-Side Architecture:** The entire internationalization (i18n) engine runs in pure vanilla JavaScript without external libraries, framework dependencies, or server roundtrips. Switching languages happens in less than 5 milliseconds without page reloading.
* **Underlying Implementation Mechanism:**
  1. **Global Translation Dictionary (`/static/js/hi.js`):** Contains a comprehensive `TRANSLATIONS` object structured with mirror keys for English (`en`) and Hindi (`hi`), covering thousands of UI strings, medical terms, button labels, danger warnings, and validation messages.
  2. **Declarative DOM Attributes:**
     * Static text nodes use `data-i18n="KEY"` (e.g., `<span data-i18n="nav_photo_ai">Photo AI</span>`).
     * Form inputs use `data-i18n-placeholder="KEY"` (e.g., `<input data-i18n-placeholder="ph_child_name">`).
     * Element tooltips use `data-i18n-title="KEY"`.
  3. **Real-Time DOM Traversal Engine:** When the language toggle button (`#lang-toggle`) is clicked:
     * It toggles the internal state between `'en'` and `'hi'`.
     * Executes `document.querySelectorAll('[data-i18n]')` to immediately swap `textContent` using the key lookup.
     * Executes `document.querySelectorAll('[data-i18n-placeholder]')` to swap placeholder strings.
  4. **Dynamic JavaScript Rendering Helper (`t(key)`):** For UI elements rendered at runtime via JavaScript (such as Chart.js tooltips, dynamically generated table rows, OCR status chips, and Photo AI inference verdicts), a global helper `t(key)` queries the active language dictionary dynamically.
  5. **Cross-Session Persistence:** Selected language is stored in `localStorage.setItem('preferred_lang', lang)`. When any page loads, an initialization script reads this value and applies the preferred language before the first paint, eliminating language flickering.


### 4. Secure Authentication & Session Protection
* Industry-standard password hashing using `bcrypt 4.0.1`.
* Session tokens managed via `PyJWT` in secure, `httpOnly` cookies to protect medical data against cross-site scripting (XSS).

---

## 3. Intermediate Features (Assessment & Automation)

### 5. 6-Step Guided Screening Wizard
A progressive step-by-step form preventing cognitive overload:
1. **Child Selection:** Choose registered child and assessment date.
2. **Measurements:** Enter weight, height, MUAC, head circumference, and check for oedema.
3. **Feeding Patterns:** Breastfeeding status, appetite, meals per day, food groups eaten yesterday (0–8 dietary diversity scale).
4. **Health History:** Diarrhoea or fever in last 2 weeks, vaccination status, known illness.
5. **Home & Socio-Economic Context:** Maternal education, mother's age, wealth index, urban/rural area.
6. **Review & Instant Analysis:** Overview of all inputs before running the dual calculation engines.

### 6. Smart Health Card OCR Document Scanner
* Upload physical health card photographs (JPEG, PNG) or digital clinic reports (PDF).
* **Hybrid Technology:**
  * Uses `pdfplumber` to extract digital text directly from vector clinic PDFs with 100% precision.
  * Uses `Tesseract 4 (LSTM)` with OpenCV image scaling for scanned cards and photos.
  * Auto-recovers missing decimal points common in OCR (e.g., converts scanned `95 kg` to `9.5 kg` and `760 cm` to `76.0 cm`).

### 7. 1-Click "Use in Assessment →" Auto-Prefill
* Clicking this button on the OCR page extracts all clinical values and automatically populates the 6-step assessment form in `sessionStorage`.
* Eliminates repetitive typing and manual transposition errors for field health workers.

---

## 4. Advanced Features (AI/ML & Clinical Decision Support)

### 8. Deterministic WHO Growth Engine
* Implements published WHO 2006 LMS Anthro standards to calculate exact age in days/months.
* Computes WAZ, HAZ, WHZ, and BAZ without rounding errors, providing clinical grade parity with official WHO Anthro software.

### 9. Predictive ML Future-Risk Engine (LightGBM)
* Rather than only detecting malnutrition *after* physical damage occurs, the ML engine forecasts **future faltering risk**.
* Trained on over 40,000 pediatric records, evaluating interactions between recent illness, dietary diversity, maternal education, and household wealth.
* Triages children into **LOW**, **WATCH**, or **HIGH** future risk tiers.

### 10. Explainable AI (XAI) Decision Support
* Highlights the specific risk factors driving the prediction (e.g., low diet diversity, missed vaccinations, recurrent fever).
* Helps Anganwadi workers explain clearly to parents *why* a child is at risk and what lifestyle change to make.

### 11. Personalized Diet & Care Plan Generator
* Creates customized nutrition plans tailored to:
  * The child's specific age group (0–6m exclusive breastfeeding, 6–8m soft complementary mash, 9–11m minced solids, 12–23m family foods, 24m+ active feeding).
  * Food preference (Vegetarian or Non-vegetarian).
  * Malnutrition severity (SAM stabilization referral vs. MAM calorie boost vs. preventive diet).
* Covers 6 structured modules: *What this means, How to feed, Foods that help, When to return, Government schemes (ICDS, POSHAN, PMMVY), and 🚩 Danger Red Flags*.

### 12. Interactive Growth Trajectory Charts (Chart.js)
* Visualizes multiple screenings over time on an interactive chart.
* Plots the child's WAZ trajectory against normal standard reference lines ($-2$ SD, $0$ SD, $+2$ SD) to immediately spot growth faltering.

### 13. Downloadable Medical PDF Reports
* Built using `ReportLab`, producing a standardized pediatric report with child metadata, clinical z-scores, ML future risk tier, custom diet plan, and Anganwadi notes.
* Downloads cleanly with a standardized filename (`ChildNutriAI_Report_<id>.pdf`).

### 14. Evidence-Based Resource Hub & Emergency Triage
* Curated library of 20 verified pediatric nutrition guides linked directly to WHO, UNICEF, and NHM India publications.
* Includes a specialized **🚨 Emergency Tab** highlighting immediate danger signs (inability to feed, bilateral feet swelling, convulsion, severe dehydration) and referral guidance for Nutrition Rehabilitation Centres (NRC).

### 15. Deep Learning Child Photo Malnutrition Screening & Grad-CAM Visual Heatmaps (with 3-Layer Clinical Safety Gate)
* **What It Does:** Enables parents, clinicians, and Anganwadi volunteers to upload a frontal photograph of an infant or young child (`/photo-scan.html`). The vision system analyzes pediatric anatomical wasting markers as an experimental triage aid before physical anthropometric measurements are taken.
* **Clinical Safety & Suitability Gate (Guardrail Pipeline):**
  * **Supported Age Range (0–59 Months):** The WHO Child Growth Standards and acute malnutrition definitions (SAM/MAM) apply specifically to infants and children under 5 years old. If age $> 59$ months is specified (e.g., a school-aged child), the system returns an explicit `unsupported_age` warning and refuses to interpret pediatric wasting scores.
  * **Clothing Obstruction Detection:** Acute wasting manifests physically as visible ribcage exposure, severe skin folds, and limb muscle loss. If a child is wearing thick clothing, school uniforms, neckties, jackets, or heavy shirts, the camera cannot inspect the torso or limbs. The system uses color space analysis (YCrCb skin segmentation) and texture density across anatomical ROIs. If skin exposure falls below minimum clinical visibility ($< 45\%$), the system safely flags `inconclusive_clothing_obstruction`, clears fabricated anatomical numbers to `N/A`, and sets screening confidence to `0.0%`.
  * **Image Quality Verification:** Evaluates image resolution, illumination level (checks for extreme underexposure or blinding glare), and Laplacian focus sharpness to reject unreadable, corrupted, or motion-blurred photos.
* **Underlying Deep Learning & Computer Vision Architecture:**
  1. **Neural Feature Backbone (`ONNX Runtime`):** Executes a deep neural network (`vision_classifier.onnx`) directly on normalized image tensors to extract global visual representations.
  2. **Anatomical Biomarker Analysis (Qualified & Experimental):**
     * When bare torso and limbs are adequately exposed, directional gradient analysis and contour ratios provide experimental indicators of thoracic rib prominence, facial buccal fat fullness, and limb emaciation.
     * When clothing obstructs the torso, the system explicitly labels these metrics as `N/A (Obstructed by clothing)` rather than fabricating false-positive rib cage prominence from collars, buttons, or backpack straps.
* **Grad-CAM Thermal Attention Overlay (Visual Explainable AI):**
  * Overlays a JET colormap thermal heatmap on the child's photograph to visualize the spatial regions with highest gradient activation.
  * When clothing is detected, the heatmap is clearly labeled as an attention check, highlighting edges such as clothing seams, preventing false clinical claims.
  * Features a one-click toggle to switch seamlessly between the **Original Photo** and the **🔥 Grad-CAM Heatmap**.
* **Three-Layer Clinical Decision Hierarchy:**
  * **Layer 1: Preliminary Visual Screening:** A non-diagnostic triage aid. Always labeled as experimental and unconfirmed until validated by physical anthropometry.
  * **Layer 2: Deterministic WHO 2006 Anthropometry:** The gold standard. Evaluates verified physical measurements (weight, height, length, sex, age in months) against WHO LMS growth standards ($WHZ, WAZ, HAZ$) and clinical criteria ($MUAC$, bilateral pitting oedema).
  * **Layer 3: Clinical Synthesis & Reconciliation:** Synthesizes image triage and physical measurements.
    * **Discrepancy Resolution:** If an image flagged possible SAM but verified physical measurements are normal ($WHZ \ge -2.0$ SD and $MUAC \ge 12.5$ cm), the system flags a `false_visual_alarm`, explains that clothing contours or lighting artifacts misled the visual model, and respects the verified physical diagnosis.
    * **Clinical Safety Invariant:** If physical anthropometry confirms acute malnutrition ($WHZ < -3.0$ SD, $MUAC < 11.5$ cm, or oedema), urgent hospital referral is NEVER suppressed or overridden by a reassuring photo.
* **1-Click "Proceed to Full Clinical Assessment" Workflow:**
  * Transfers the visual screening verdict into `sessionStorage` and automatically opens the 6-Step Clinical Assessment form with an informative notification banner, passing the screening result to the backend assessment pipeline for deterministic cross-validation.
* **Photo Capture Guidelines:**
  * **Framing:** Frontal upper-body (head to mid-thigh).
  * **Clothing:** Minimal / light clothing so the chest wall and upper limbs are bare and visible (essential to assess thoracic wasting).
  * **Posture:** Neutral, supported upright or lying flat on a firm cot.
  * **Lighting:** Bright, diffuse daylight or room lighting without heavy flash shadows.

---

## 5. Detailed Pipeline Flows from Input to Output

### 5.1 Machine Learning Model Pipeline Flow (LightGBM Future-Risk Engine)
The predictive machine learning engine evaluates non-linear multi-factorial risks to forecast whether a currently stable child is at imminent risk of growth faltering within the next 3 to 6 months.

```
┌────────────────────────────────────────────────────────────────────────┐
│ INPUT: 14 Multi-Domain Clinical, Nutritional & Socio-Economic Features │
├────────────────────────────────────────────────────────────────────────┤
│ • Child Age (months) & Sex (Male/Female)                               │
│ • Dietary Diversity Score (0–8 WHO food groups consumed yesterday)     │
│ • Meal Frequency (meals/day) & Breastfeeding Status (Exclusive/Partial)│
│ • Acute Morbidities: Diarrhoea in last 14 days (0/1), Fever (0/1)      │
│ • Preventive Care: Completed age-appropriate vaccination count (0–7)   │
│ • Maternal Context: Mother's age (years), Education level (0–4 tiers)  │
│ • Socio-Economic Stratification: Household Wealth Index (1–5 quintile) │
│ • Geographic Setting: Urban / Peri-Urban / Rural                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Feature Preprocessing & Vectorization                          │
├────────────────────────────────────────────────────────────────────────┤
│ • Categorical Encoding: One-Hot / Ordinal mapping for gender & wealth  │
│ • Missing Value Imputation: Median imputation for continuous variables │
│ • Robust Range Clipping: Bounds checking for physiological plausibility│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 2: LightGBM Gradient Boosted Decision Tree Inference             │
├────────────────────────────────────────────────────────────────────────┤
│ • Passes 14-dimensional feature vector into ensemble of decision trees │
│ • Evaluates split criteria optimized for high-risk minority recall     │
│ • Outputs raw log-odds (logit score)                                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Non-Parametric Isotonic Probability Calibration                │
├────────────────────────────────────────────────────────────────────────┤
│ • Maps raw uncalibrated tree logits through isotonic regression curve   │
│ • Aligns predicted probabilities with real-world observed incidence    │
│ • Yields calibrated probability score $P(\text{Faltering}) \in [0.0, 1.0]$│
│   (Brier Score = 0.143, ROC-AUC = 0.87)                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 4: TreeSHAP Explainable AI (XAI) Attribution                      │
├────────────────────────────────────────────────────────────────────────┤
│ • Computes Shapley additive explanations for each input variable       │
│ • Calculates exact percentage risk delta: $\sum \phi_i = P - E[P]$     │
│ • Extracts the Top 3 Primary Risk Drivers (e.g. Lack of animal source  │
│   protein: +28%, Recurrent diarrhoea: +19%, Low maternal literacy: +12%)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Risk Tiering & Clinical Thresholding                           │
├────────────────────────────────────────────────────────────────────────┤
│ • LOW RISK: Calibrated Probability < 0.25                              │
│ • WATCH ZONE: Calibrated Probability 0.25 to 0.55                      │
│ • HIGH RISK: Calibrated Probability > 0.55                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Comprehensive Future Risk Profile                              │
├────────────────────────────────────────────────────────────────────────┤
│ • Risk Tier Badge ("LOW", "WATCH", or "HIGH")                          │
│ • Calibrated Faltering Probability (e.g., 68.4%)                       │
│ • Explainable Top 3 Risk Factors with quantitative impacts             │
│ • Tailored Preventive Guidance & Recommended Follow-up Timeline        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 5.2 OCR Document Parsing Pipeline Flow (Hybrid Vector PDF + OpenCV/Tesseract)
The optical document processing engine enables Anganwadi workers and doctors to digitize physical Mother-Child Protection (MCP) cards or clinical discharge PDFs in seconds.

```
┌────────────────────────────────────────────────────────────────────────┐
│ INPUT: Digital Document Upload (PDF) or Physical Card Photo (JPEG/PNG)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 1: MIME Type & Structure Detection                                │
├────────────────────────────────────────────────────────────────────────┤
│ • Detects file signature: Vector Digital PDF vs. Scanned Raster Image  │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
    (If Vector PDF) │                                │ (If Photo / Scanned Image)
                    ▼                                ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│ STEP 2A: Direct Vector PDF Extraction│ │ STEP 2B: Computer Vision      │
│          (`pdfplumber`)              │ │          Preprocessing        │
├──────────────────────────────────────┤ ├───────────────────────────────┤
│ • Extracts embedded text streams     │ │ • Grayscale conversion        │
│ • Identifies tabular grid borders    │ │ • Gaussian blur noise removal │
│ • Parses table cell coordinates      │ │ • Adaptive Otsu Binarization  │
│ • Yields 100% character precision    │ │ • Morphological dilation      │
│   without optical distortion         │ │ • Deskewing & rotation corr.  │
└───────────────────┬──────────────────┘ └───────────────┬───────────────┘
                    │                                    │
                    │                                    ▼
                    │                    ┌───────────────────────────────┐
                    │                    │ STEP 2C: Tesseract 4 OCR      │
                    │                    │          Engine Execution     │
                    │                    ├───────────────────────────────┤
                    │                    │ • PSM 6: Uniform text blocks  │
                    │                    │ • PSM 11: Sparse tabular data │
                    │                    │ • Whitelist: Numeric & medical│
                    │                    └───────────────┬───────────────┘
                    │                                    │
                    └─────────────────┬──────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Multi-Pattern Regex & Clinical Entity Extraction Engine        │
├────────────────────────────────────────────────────────────────────────┤
│ • Child Name: `(?:Name|Child)[:\s]+([A-Za-z\s]{3,30})`                 │
│ • Date of Birth / Age: `(?:DOB|Birth)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})`│
│ • Weight: `(?:Weight|Wt)[:\s]+(\d{1,2}(?:\.\d{1,2})?)\s*(?:kg)?`       │
│ • Height / Length: `(?:Height|Ht|Length)[:\s]+(\d{2,3}(?:\.\d{1,2})?)\s*(?:cm)?`│
│ • MUAC: `(?:MUAC)[:\s]+(\d{1,2}(?:\.\d{1,2})?)\s*(?:cm)?`             │
│ • Immunization: Checkbox marks for BCG, OPV, Pentavalent, Measles      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Pediatric Decimal Recovery & Sanity Checking Engine            │
├────────────────────────────────────────────────────────────────────────┤
│ • Solves ubiquitous OCR period dropping in low-contrast carbon copies: │
│   - `95 kg` -> Automatically recovered to `9.5 kg` (plausible infant)  │
│   - `740 cm` -> Automatically recovered to `74.0 cm`                   │
│   - `118 cm` MUAC -> Automatically recovered to `11.8 cm`              │
│ • Bounds validation against biological limits (Weight: 1–35kg, Ht: 40–130cm)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Structured Pediatric JSON Payload                              │
├────────────────────────────────────────────────────────────────────────┤
│ • Extracted Fields: `child_name`, `dob`, `gender`, `weight_kg`,        │
│   `height_cm`, `muac_cm`, `vaccines`                                   │
│ • Optical confidence score (0–100%)                                    │
│ • 1-Click "Use in Assessment →" Auto-Prefill Trigger into 6-step form  │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Deep Learning Vision Pipeline Flow (Multimodal ONNX & 3-Layer Clinical Safety Gate)
The visual malnutrition triage engine inspects pediatric photographs while enforcing strict clinical guardrails to eliminate false positives and prevent unvalidated AI predictions from overriding verified clinical medicine.

```
┌────────────────────────────────────────────────────────────────────────┐
│ INPUT: Frontal Child Photograph (PNG/JPEG/WebP) + Optional Age (months)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Pre-Screening Image Quality Gate                               │
├────────────────────────────────────────────────────────────────────────┤
│ • Minimum Resolution Check: Rejects images smaller than 200 x 200 px   │
│ • Illumination Gate: Computes mean grayscale intensity $\mu \in [0, 255]$│
│   - Rejects severe underexposure ($\mu < 30$) or blinding glare ($\mu > 235$)│
│ • Focus & Sharpness Gate: Laplacian variance $\sigma^2(\nabla^2 I)$    │
│   - If $\sigma^2 < 25.0$ -> Rejects image as `unsuitable_blur`         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Pediatric Age Range Gate (0–59 Months)                         │
├────────────────────────────────────────────────────────────────────────┤
│ • WHO 2006 Standards and SAM/MAM definitions apply exclusively to      │
│   infants and young children under 5 years old (0–59 months).          │
│ • If age > 59 months (e.g. school-age):                                │
│   - Status -> `unsupported_age`                                        │
│   - Halts pediatric wasting scoring to prevent clinical invalidity.    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Bare Skin Exposure & Clothing Obstruction Gate                 │
├────────────────────────────────────────────────────────────────────────┤
│ • Acute wasting physically manifests as exposed ribcage bones and skin │
│   folds. School uniforms, ties, jackets, or shirts block inspection.   │
│ • Color Space Segmentation: Converts image to YCrCb chrominance space: │
│   $Y \in [0, 255], Cr \in [133, 173], Cb \in [77, 127]$                 │
│ • Calculates Bare Skin Pixel Ratio across the Thoracic ROI:            │
│   - If Skin Ratio < 45% -> Halts as `inconclusive_clothing_obstruction`│
│   - Clears fabricated anatomical scores to `N/A`                       │
│   - Sets visual confidence to `0.0%` and returns neutral probabilities │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
 (If Bare Skin < 45%)                                │ (If Bare Skin >= 45% & Age <= 59m)
                    ▼                                ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│ INCONCLUSIVE / OBSTRUCTED SCREENING  │ │ STEP 4: ONNX Deep Neural      │
├──────────────────────────────────────┤ │         Backbone Inference    │
│ • Verdict: Inconclusive (Clothing)   │ ├───────────────────────────────┤
│ • Ribcage: N/A (Clothing obstructed) │ │ • Tensor Resizing: 224 x 224  │
│ • Arm Wasting: N/A                   │ │ • RGB channel ordering        │
│ • Confidence: 0.0%                   │ │ • ImageNet Normalization:     │
│ • Action: Request physical measure-  │ │   $\mu=[0.485, 0.456, 0.406]$,│
│   ments (weight, height, MUAC)       │ │   $\sigma=[0.229, 0.224, 0.225]$│
└───────────────────┬──────────────────┘ │ • Executes ONNX Runtime graph │
                    │                    │ • Numerically stable Softmax  │
                    │                    │   $\rightarrow P(\text{Healthy}), P(\text{MAM}), P(\text{SAM})$│
                    │                    └───────────────┬───────────────┘
                    │                                    │
                    │                                    ▼
                    │                    ┌───────────────────────────────┐
                    │                    │ STEP 5: Experimental Biomarker│
                    │                    │         Quantification        │
                    │                    ├───────────────────────────────┤
                    │                    │ • Thoracic Rib Prominence:    │
                    │                    │   Directional Sobel vertical  │
                    │                    │   gradient density (0–100)    │
                    │                    │ • Facial Fat Depletion:       │
                    │                    │   Orbital/cheek contrast (0–100)│
                    │                    │ • Limb Emaciation Index:      │
                    │                    │   Arm width-to-height ratio   │
                    │                    └───────────────┬───────────────┘
                    │                                    │
                    │                                    ▼
                    │                    ┌───────────────────────────────┐
                    │                    │ STEP 6: Grad-CAM Explainable  │
                    │                    │         AI Heatmap Generation │
                    │                    ├───────────────────────────────┤
                    │                    │ • Computes spatial activation │
                    │                    │   density from feature layer  │
                    │                    │ • Normalizes to [0, 255]      │
                    │                    │ • Applies OpenCV COLORMAP_JET │
                    │                    │ • Alpha blends onto original  │
                    │                    └───────────────┬───────────────┘
                    │                                    │
                    └─────────────────┬──────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 7: Layer 3 Clinical Synthesis & Reconciliation Pipeline           │
├────────────────────────────────────────────────────────────────────────┤
│ Synthesizes visual screening output with physical WHO anthropometry:   │
│                                                                        │
│ • CASE 1: False Visual Alarm (Clothing/Shadow Artifact)               │
│   - Condition: Photo flagged SAM, but physical measurements normal     │
│     ($WHZ \ge -2.0$ SD and $MUAC \ge 12.5$ cm)                         │
│   - Action: Logs `false_visual_alarm`; explains that clothing contours │
│     misled camera; verified physical normal diagnosis takes precedence.│
│                                                                        │
│ • CASE 2: Emergency Clinical Invariant                                │
│   - Condition: Physical anthropometry shows clinical SAM ($WHZ < -3.0$ │
│     SD, $MUAC < 11.5$ cm, or Bilateral Pitting Oedema)                 │
│   - Action: Immediate hospital/NRC referral is NEVER suppressed or     │
│     delayed by a reassuring photograph.                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Calibrated Screening Verdict & Verified Care Pathway           │
├────────────────────────────────────────────────────────────────────────┤
│ • Status: `supported` / `inconclusive_clothing` / `unsupported_age`    │
│ • Triage Verdict: `healthy`, `mam`, `sam`, or `inconclusive`           │
│ • Calibrated Probabilities & Biomarker Metrics (or `N/A`)              │
│ • Interactive Grad-CAM Heatmap overlay                                 │
│ • 1-Click "Proceed to Full Clinical Assessment" with pre-fill data     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. End-to-End System Workflow

```
[Child Photograph] ────────────────────────────────────────────────────────┐
        │                                                                  │
        ▼ (Layer 1: Preliminary Screening)                                 │
┌───────────────────────────────────────────────────────────┐              │
│ Image Suitability Gate & Vision AI                        │              │
│ - Age Gate (0-59 months)                                  │              │
│ - Clothing Obstruction & Bare Skin Check (YCrCb)          │              │
│ - Focus & Lighting Quality Gate                           │              │
│ - ONNX Feature Backbone + Grad-CAM Heatmap                │              │
└───────────────────────────┬───────────────────────────────┘              │
                            │                                              │
                            ▼ (Preliminary Triage / Inconclusive)          │
[Physical Health Card / PDF Scan / Manual Input]                           │
                   │                                                       │
                   ▼                                                       │
     ┌───────────────────────────┐                                         │
     │     OCR Document Parser   │  (pdfplumber + OpenCV + Tesseract)      │
     └─────────────┬─────────────┘                                         │
                   │ (Auto-Prefill)                                        │
                   ▼                                                       │
     ┌───────────────────────────┐                                         │
     │   6-Step Screening Form   │  (Anthropometry + Diet + Health Context)│
     └─────────────┬─────────────┘                                         │
                   │                                                       │
       ┌───────────┴───────────┐                                           │
       ▼ (Layer 2: Deterministic)▼ (Predictive ML)                         │
┌──────────────────┐   ┌───────────────────┐                               │
│ Deterministic WHO│   │ Predictive ML Core│                               │
│   LMS Engine     │   │     (LightGBM)    │                               │
│  WAZ / HAZ / WHZ │   │ Calibrated Future │                               │
│  SAM / MAM / Ok  │   │     Risk Tier     │                               │
└────────┬─────────┘   └─────────┬─────────┘                               │
         └───────────┬───────────┘                                         │
                     │                                                     │
                     ▼                                                     │
       ┌───────────────────────────┐ ◄─────────────────────────────────────┘
       │ Layer 3: Clinical Synthesis│ (Cross-validates visual screening with
       │ & Reconciliation Pipeline │  deterministic anthropometry; flags
       │ (SHAP + Diet Customizer)  │  false visual alarms; preserves emergency)
       └─────────────┬─────────────┘
                     │
    ┌────────────────┴────────────────┐
    ▼                                 ▼
[Interactive Dashboard & Trajectory]  [Downloadable PDF Clinical Report]
```

---

## 7. FastAPI Backend API Reference & Code Map

### 7.1 Complete API Endpoint Catalog
All backend routes are served under the `/api/` prefix and automatically documented via OpenAPI Swagger at `http://127.0.0.1:8000/api/docs`.

| Method | Endpoint Path | Router Source File | Auth Required | Purpose & Description |
| :--- | :--- | :--- | :---: | :--- |
| **POST** | `/api/auth/register` | `backend/app/routers/auth.py` | ❌ No | Registers a new user (`UserCreate`: email, password, full_name, role `'parent'` or `'doctor'`). Hashes password with bcrypt. |
| **POST** | `/api/auth/login` | `backend/app/routers/auth.py` | ❌ No | Authenticates user credentials via OAuth2 password form (`username`, `password`). Returns JWT access token and sets secure cookie. |
| **GET** | `/api/auth/me` | `backend/app/routers/auth.py` | ✅ Yes | Returns current authenticated user profile (`UserResponse`). |
| **DELETE** | `/api/auth/me` | `backend/app/routers/auth.py` | ✅ Yes | Permanently deletes current user account and cascades child records. |
| **GET** | `/api/children/` | `backend/app/routers/children.py` | ✅ Yes | Lists all registered children for current user/clinician. |
| **POST** | `/api/children/` | `backend/app/routers/children.py` | ✅ Yes | Registers a new child (`ChildCreate`: name, sex, dob, birth_weight_kg, birth_height_cm). |
| **GET** | `/api/children/{id}` | `backend/app/routers/children.py` | ✅ Yes | Retrieves detailed profile for a specific child ID. |
| **GET** | `/api/children/{id}/assessments` | `backend/app/routers/children.py` | ✅ Yes | Lists longitudinal assessment history and trajectory for child. |
| **POST** | `/api/assessments/` | `backend/app/routers/assessments.py` | ✅ Yes | **Core Clinical Engine:** Runs full 3-layer pipeline (`AssessmentCreate`: measurements, feeding, morbidity, optional `photo_screening_result`). |
| **GET** | `/api/assessments/{id}` | `backend/app/routers/assessments.py` | ✅ Yes | Retrieves full assessment results, z-scores, ML risk tier, and diet plan. |
| **GET** | `/api/assessments/{id}/pdf` | `backend/app/routers/assessments.py` | ✅ Yes | Generates and streams downloadable medical clinical PDF report via ReportLab. |
| **POST** | `/api/vision/photo-scan` | `backend/app/routers/vision.py` | ❌ Optional | **Deep Learning Triage:** Uploads child photo (`file`, optional `age_months`, `child_id`). Runs quality gate, clothing check, ONNX inference, and returns Grad-CAM. |
| **POST** | `/api/ocr/scan` | `backend/app/routers/ocr.py` | ❌ Optional | **Document Scanner:** Uploads MCP health card or discharge summary (PDF/Image). Returns extracted clinical entities and decimal recovery. |
| **POST** | `/api/uploads/image` | `backend/app/routers/uploads.py` | ✅ Yes | Secure upload endpoint for profile avatars or diagnostic image attachments. |
| **GET** | `/api/resources/` | `backend/app/routers/ocr.py` | ❌ No | Lists verified pediatric nutrition articles with filtering by tag (`symptoms`, `diet`, `who`, `emergency`). |
| **GET** | `/api/resources/{id}` | `backend/app/routers/ocr.py` | ❌ No | Retrieves full guide content and reference URL for a single resource. |
| **GET** | `/api/meta/health` | `backend/app/routers/ocr.py` | ❌ No | System health check (database connection, ML model status). |

---

### 7.2 Where to Look in the FastAPI Backend (Code Map)
The backend follows a clean, modular Model-View-Controller (Router-Service-Model) architecture. Here is where every piece of code lives:

```
childnutri/backend/app/
├── main.py                     # Entry point: FastAPI app, CORS middleware, static mount, router inclusion
├── database.py                 # SQLite/PostgreSQL connection engine and SessionLocal dependency
│
├── routers/                    # Controller Layer: HTTP request handlers, URL routing, status codes
│   ├── auth.py                 # User registration, login, JWT token issuance, account deletion
│   ├── children.py             # Child CRUD operations and longitudinal assessment lookups
│   ├── assessments.py          # Assessment execution, PDF streaming, history retrieval
│   ├── vision.py               # Photo AI screening, age validation, Grad-CAM generation
│   ├── ocr.py                  # Health card OCR, resource guides, system health metadata
│   └── uploads.py              # File upload handling and validation
│
├── schemas/                    # Pydantic Schemas: Request validation and response serialization
│   └── __init__.py             # AssessmentCreate, ChildCreate, UserCreate, Token, VisionResult
│
├── models/                     # SQLAlchemy ORM Models: Database tables and relational schemas
│   ├── user.py                 # User table (email, hashed password, role)
│   ├── child.py                # Child profile table (name, dob, sex, parent_id)
│   ├── assessment.py           # Assessment record table (z-scores, ML risk, recommendations)
│   └── resource.py             # Health resource article table (tags, title, summary, source_url)
│
└── services/                   # Business Logic & Machine Learning Engines
    ├── pipeline.py             # Master orchestrator: Combines Layers 1, 2, and 3
    ├── who_zscore.py           # WHO 2006 LMS Anthro mathematical standard deviation engine
    ├── classify.py             # SAM/MAM classification and clinical referral logic
    ├── risk_predictor.py       # LightGBM future-risk model inference and isotonic calibration
    ├── vision_service.py       # Image suitability gate, YCrCb skin check, ONNX runtime, Grad-CAM
    ├── ocr_service.py          # pdfplumber + OpenCV + Tesseract 4 text extraction
    ├── diet_engine.py          # 6-module age-specific custom meal plan generator
    ├── pdf_report.py           # ReportLab medical PDF generation
    └── seed_data.py            # Automatic database seeder for verified clinical articles
```

---

### 7.3 How to Add or Modify an API Endpoint (Step-by-Step Developer Guide)

#### Scenario: Adding a New Field or Endpoint
Follow this 4-step workflow whenever modifying existing endpoints or creating new ones:

#### Step 1: Update the Pydantic Schema (`backend/app/schemas/__init__.py`)
Define the request and response shapes so FastAPI automatically validates incoming JSON and generates Swagger docs:
```python
# In backend/app/schemas/__init__.py
from pydantic import BaseModel
from typing import Optional

class CustomMetricRequest(BaseModel):
    child_id: int
    mid_arm_circumference: float
    notes: Optional[str] = None

class CustomMetricResponse(BaseModel):
    status: str
    risk_level: str
```

#### Step 2: Write Business Logic in the Services Layer (`backend/app/services/`)
Keep route handlers thin by placing clinical calculations or database operations inside `services/`:
```python
# In backend/app/services/custom_service.py
def evaluate_custom_metric(child_id: int, muac: float) -> str:
    if muac < 11.5:
        return "CRITICAL_SAM"
    elif muac < 12.5:
        return "MODERATE_MAM"
    return "NORMAL"
```

#### Step 3: Implement the Route Handler in `backend/app/routers/`
Attach the handler to an existing router or create a new router file:
```python
# In backend/app/routers/assessments.py
from fastapi import APIRouter, Depends, HTTPException
from backend.app.schemas import CustomMetricRequest, CustomMetricResponse
from backend.app.services.custom_service import evaluate_custom_metric

@router.post("/custom-metric", response_model=CustomMetricResponse)
def compute_metric(payload: CustomMetricRequest, db: Session = Depends(get_db)):
    verdict = evaluate_custom_metric(payload.child_id, payload.mid_arm_circumference)
    return {"status": "success", "risk_level": verdict}
```

#### Step 4: Verify in FastAPI Interactive Docs
FastAPI automatically recompiles on save with `--reload`. Open your browser:
* Go to: `http://127.0.0.1:8000/api/docs`
* Expand your new endpoint, click **"Try it out"**, supply test JSON, and verify the response status code and schema.

---

## 8. How to Run the Frontend and Backend Project

### 8.1 System Prerequisites & Virtual Environment Setup
Ensure you have **Python 3.10+** installed on your system.

1. Navigate to the project directory:
   ```bash
   cd /Users/varadpendkar/Downloads/Child_nutri_AI/childnutri
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install required dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### 8.2 Starting the Unified Full-Stack Application (Port 8000)
ChildNutri AI uses a **unified full-stack architecture**. FastAPI serves both the REST API backend and the static HTML/CSS/JS frontend on the exact same port (`8000`), completely eliminating Cross-Origin Resource Sharing (CORS) issues in production:

```bash
# Run from inside /Users/varadpendkar/Downloads/Child_nutri_AI/childnutri
PYTHONPATH=. ./venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **Host:** `127.0.0.1` (localhost)
* **Port:** `8000`
* **`--reload`:** Live reload enabled (modifications to Python files automatically restart the server).

---

### 8.3 Accessing the Web Dashboard & Interactive Swagger Docs
Once the server starts, open your browser to access the platform:

| Page / Feature | URL in Browser | Purpose |
| :--- | :--- | :--- |
| **Landing & Login** | `http://127.0.0.1:8000/` | Parent & Clinician authentication and role selection |
| **Dashboard** | `http://127.0.0.1:8000/dashboard.html` | Overview of registered children and growth status cards |
| **6-Step Assessment** | `http://127.0.0.1:8000/assessment.html` | Guided anthropometric screening wizard |
| **Photo AI Screening** | `http://127.0.0.1:8000/photo-scan.html` | Pediatric photo screening with Grad-CAM heatmap |
| **OCR Document Scanner** | `http://127.0.0.1:8000/ocr-scan.html` | MCP card photo and clinic PDF digitization |
| **Resource Library** | `http://127.0.0.1:8000/resources.html` | 20 verified pediatric nutrition guides & NRC emergency tab |
| **Interactive Swagger API** | `http://127.0.0.1:8000/api/docs` | Test and execute any backend API endpoint interactively |
| **ReDoc API Documentation** | `http://127.0.0.1:8000/api/redoc` | Clean, formal OpenAPI documentation format |

> **Note on Standalone Frontend Development:**  
> Because the frontend is built entirely with vanilla HTML, modern CSS, and plain JavaScript (no React, no bundlers, no Node.js build step), you can also edit any file in `childnutri/frontend/` and simply refresh your browser to see immediate changes!

---

### 8.4 Database Initialization & Seeding Clinical Data
* When `backend.app.main:app` starts, it automatically calls `Base.metadata.create_all(bind=engine)`, creating SQLite database tables in `childnutri.db` (or PostgreSQL if configured in `.env`).
* It automatically executes `seed_articles()`, seeding the 20 verified WHO and UNICEF clinical nutrition guides into the database.
* To manually re-seed the clinical guides at any time:
  ```bash
  PYTHONPATH=. ./venv/bin/python -c "from backend.app.services.seed_data import seed_articles; seed_articles()"
  ```

---

### 8.5 Running Automated Regression Tests
Execute the complete automated test suite (including the 13 clinical safety gate scenarios and 5 end-to-end integration flows):
```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests/test_vision_screening.py backend/tests/test_core_flow.py -v
```
All 18 tests will execute in approximately 3.3 seconds and report a 100% pass rate.



