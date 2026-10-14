# ChildNutri AI — Academic Presentation Deck (Slide-by-Slide Guide)

**Project Title:** ChildNutri AI: Malnourishment Identification in Infants Using AI  
**Degree / Program:** Final-Year B.Tech Capstone Project Defense  
**Institution:** G.H. Raisoni College of Engineering and Management, Wagholi, Pune  
**Department:** Computer Science & Engineering (Artificial Intelligence & Machine Learning)  
**Group Number:** O-33  
**Project Guide:** Prof. Shridhar Venkatanarasimha  

### 👥 Project Team Members
| Name | Roll Number | Role |
| :--- | :--- | :--- |
| **Kalpak Shende** | L-09 | Deep Learning, Computer Vision & Safety Gate Architect |
| **Subhashish Barik** | L-33 | Tabular Machine Learning, WHO LMS Engine & LightGBM |
| **Vishweshwar Yadav** | L-55 | Full-Stack Platform, OCR Document Pipeline & Bilingual UX |

---

## 📑 Slide Structure Overview

* **Slide 1:** Title Slide (Institutional & Team Information)
* **Slide 2:** Table of Contents / Presentation Outline
* **Slide 3:** Introduction & Clinical Motivation (Global & National Malnutrition Burden)
* **Slide 4:** Problem Statement & Limitations of Existing Systems
* **Slide 5:** Project Objectives & Proposed Solution
* **Slide 6:** Literature Review & Comparative Technical Benchmark
* **Slide 7:** Overall System Architecture & 3-Layer Clinical Decision Hierarchy
* **Slide 8:** Machine Learning Pipeline: LightGBM Future-Risk Engine & TreeSHAP
* **Slide 9:** Deep Learning & Computer Vision Pipeline: Multimodal ONNX & Clinical Safety Gate
* **Slide 10:** Smart Health Card OCR Engine: Hybrid Vector PDF & OpenCV/Tesseract
* **Slide 11:** Zero-Latency Client-Side Bilingual System (English / हिंदी) & Web Dashboard
* **Slide 12:** Experimental Results, Model Calibration & Automated Clinical Safety Tests
* **Slide 13:** Case Studies & Before-and-After Analysis (Clothed School Child vs. Bare Infant)
* **Slide 14:** Conclusion, Ethical AI Considerations, Future Roadmap & References

---

### Slide 1 — Title Slide
* **Slide Title:** ChildNutri AI: Malnourishment Identification in Infants Using AI
* **Subtitle:** An Explainable Multimodal Healthcare Platform Combining Computer Vision, Deterministic WHO Anthropometry, and Calibrated Machine Learning
* **Institution:** G.H. Raisoni College of Engineering and Management, Wagholi, Pune
* **Department:** Department of Computer Science and Engineering (AI & ML)
* **Project Group:** Group O-33
* **Project Guide:** Prof. Shridhar Venkatanarasimha
* **Team Members:**
  * Kalpak Shende (Roll No: L-09)
  * Subhashish Barik (Roll No: L-33)
  * Vishweshwar Yadav (Roll No: L-55)
* **Academic Year:** 2025–2026
* **Visual Theme:** Premium Dark Emerald Green (`#040d0a`) with Bright Mint/Teal Accent (`#34d399` / `#22d3ee`).
* **Speaker Notes:**
  > *"Good morning respected evaluators, Head of Department, and our project guide Prof. Shridhar Venkatanarasimha. We are Group O-33 representing the Department of CSE (AI & ML) at G.H. Raisoni College of Engineering and Management. Today, we present 'ChildNutri AI' — an explainable, clinically grounded multimodal platform designed to detect, forecast, and triage infant malnutrition across resource-constrained healthcare environments."*

---

### Slide 2 — Table of Contents / Outline
* **Slide Header:** Agenda & Presentation Outline
* **Sections:**
  1. **Clinical Context & Problem Statement:** Why early infant screening is a critical public health emergency.
  2. **Technical Objectives:** Building a safe, non-invasive, deterministic, and predictive platform.
  3. **Core Architectural Innovation:** The 3-Layer Clinical Decision Pipeline separating screening from diagnosis.
  4. **Machine Learning Core:** Predictive future-risk modeling with LightGBM, Isotonic Calibration & TreeSHAP.
  5. **Computer Vision & Safety Guardrails:** Multimodal ONNX inference, YCrCb skin segmentation, and Grad-CAM.
  6. **Automated Document Digitize:** Hybrid OCR for Mother-Child Protection (MCP) health cards.
  7. **Inclusive Field Accessibility:** Pure client-side zero-latency English/Hindi localization.
  8. **Empirical Validation & Testing:** Results of 18 automated clinical regression tests and field case studies.
* **Speaker Notes:**
  > *"Our presentation walks through the complete engineering and clinical lifecycle of ChildNutri AI, from public health motivations to deep learning architectures, rigorous clinical safety testing, and real-time field deployments."*

---

### Slide 3 — Introduction & Clinical Motivation
* **Slide Header:** Clinical Background: The Silent Pediatric Crisis
* **Key Bullet Points:**
  * **Global & National Scale:** According to NFHS-5 and WHO reports, India accounts for nearly one-third of the global burden of child malnutrition: ~35.5% stunting, ~19.3% wasting, and ~7.7% severe acute malnutrition (SAM).
  * **The "First 1,000 Days" Window:** Nutritional deprivation from conception to age two results in irreversible physical stunting, neurodevelopmental deficits, and significantly increased under-5 mortality.
  * **Critical Classifications:**
    * **Severe Acute Malnutrition (SAM):** Weight-for-Height $Z$-score (WHZ) $< -3$ SD, MUAC $< 11.5$ cm, or presence of bilateral pitting oedema (Kwashiorkor). Carries a 9x increased risk of death.
    * **Moderate Acute Malnutrition (MAM):** WHZ between $-2$ and $-3$ SD, or MUAC $11.5$–$12.4$ cm. Requires supervised supplementary feeding.
    * **Chronic Stunting:** Height-for-Age $Z$-score (HAZ) $< -2$ SD.
  * **Grassroots Bottlenecks:** Frontline Anganwadi workers face uncalibrated analog scales, paper-based Mother-Child Protection (MCP) cards, heavy cognitive workload, and lack of pediatric diagnostic support.
* **Speaker Notes:**
  > *"Acute malnutrition is not merely a weight problem — it is an acute medical emergency. An infant with Severe Acute Malnutrition is up to nine times more likely to die from common infections like diarrhoea or pneumonia. Yet, frontline workers in rural sub-centres are often armed with nothing more than worn-out spring scales and faded paper cards."*

---

### Slide 4 — Problem Statement & Limitations of Existing Systems
* **Slide Header:** Problem Statement: The Diagnostic Gap
* **Current Realities & Failure Modes:**
  * **Late Diagnosis:** Conventional systems only identify malnutrition *after* severe tissue breakdown has occurred. There is no predictive early warning before physical damage.
  * **Manual Transcription Errors:** Anganwadi workers manually compute ages and plot growth curves on physical charts, leading to human calculation and transcription errors exceeding 25%.
  * **The "Black-Box Vision Trap" (Unvalidated AI Overreach):**
    * Uploading photographs of clothed children often causes computer vision models to mistake high-contrast clothing seams, ties, and backpack straps for skeletal rib exposure.
    * Models uncalibrated for age groups attempt to diagnose school-aged children using infant wasting thresholds, generating false-positive emergencies.
  * **Lack of Clinical Explainability:** Healthcare practitioners rightfully reject black-box neural networks that output confident verdicts without biological justification or attention heatmaps.
* **Speaker Notes:**
  > *"The major failure mode in existing healthcare AI apps is unvalidated overreach. When a computer vision model sees a child in a school uniform, high-contrast neckties and folded collars are miscalculated as protruding ribs, generating false SAM alarms. Our project directly confronts and solves this critical safety failure."*

---

### Slide 5 — Project Objectives & Scope
* **Slide Header:** Project Objectives & Functional Scope
* **Core Technical Objectives:**
  1. **Deterministic WHO LMS Growth Engine:** Implement mathematically exact 2006 WHO growth standards for WAZ, HAZ, WHZ, and BAZ without rounding errors.
  2. **Predictive Future-Risk Engine:** Develop a gradient-boosted LightGBM classifier with isotonic calibration to forecast growth faltering 3 to 6 months in advance.
  3. **Explainable AI (XAI):** Provide biological interpretability via TreeSHAP for tabular risk factors and Grad-CAM thermal heatmaps for visual screening.
  4. **Smart Optical Document Scanner (OCR):** Create a hybrid pipeline using `pdfplumber` and `Tesseract 4` with automatic decimal recovery to digitize physical health cards.
  5. **Safety-Guarded Deep Learning Vision System:** Build a 3-layer clinical decision pipeline with YCrCb bare-skin segmentation, Laplacian focus checks, and strict pediatric age gating (0–59 months).
  6. **Zero-Latency Bilingual Field Usability:** Implement pure client-side English/Hindi switching for rural Anganwadi adoption.
* **Speaker Notes:**
  > *"Our primary design objective was to build a system that clinicians can actually trust. That meant establishing strict boundaries: an image cannot diagnose a child without physical anthropometry, and AI must explain its reasoning in transparent medical terms."*

---

### Slide 6 — Literature Survey & Comparative Technical Benchmark
* **Slide Header:** Literature Survey & State-of-the-Art Comparison
* **Comparative Matrix:**

| Feature / Metric | Conventional Hospital Systems | Typical Academic Mobile Apps | ChildNutri AI (Our Platform) |
| :--- | :--- | :--- | :--- |
| **Growth Standards** | WHO Anthro (Desktop/Manual) | Simplified static tables | **Exact WHO 2006 LMS Engine (WAZ/HAZ/WHZ)** |
| **Future Risk Forecasting** | None (Post-event only) | Simple linear regression | **LightGBM + Isotonic Calibration (ROC-AUC: 0.87)** |
| **Clinical Explainability** | None | Raw probability percentage | **TreeSHAP Feature Attribution + Grad-CAM Heatmap** |
| **Document Digitization** | Manual data entry | Basic camera OCR (high error rate) | **Hybrid `pdfplumber` + Tesseract + Decimal Recovery** |
| **Computer Vision Safety** | None | Naive CNN (prone to clothing false SAM) | **Image Suitability Gate (YCrCb Skin + Blur + Age)** |
| **Decision Hierarchy** | Clinical only | Image overrides clinical | **3-Layer Clinical Hierarchy (Anthropometry Precedence)** |
| **Language Support** | English only | Requires server reload | **Zero-Latency Client-Side English / Hindi Toggle** |

* **Speaker Notes:**
  > *"In literature, we observed two extremes: rigid legacy software like WHO Anthro that offers no automated digitization, and naive deep learning apps that try to diagnose malnutrition from photos without verifying clothing or age. ChildNutri AI bridges this gap with hybrid intelligence."*

---

### Slide 7 — Overall System Architecture & 3-Layer Clinical Hierarchy
* **Slide Header:** System Architecture & 3-Layer Clinical Decision Hierarchy
* **System Hierarchy Diagram:**
  * **Layer 1: Preliminary Visual Screening (Adjuvant Triage Aid):**
    * Focus & Illumination Gate ($\sigma^2 \ge 25.0$, $30 < \mu < 235$).
    * Pediatric Age Gate ($0 \le \text{age} \le 59$ months).
    * Bare Skin & Clothing Obstruction Gate: Bare skin $\ge 45\%$ via YCrCb space.
    * ONNX Deep Learning Inference $\rightarrow$ Labeled strictly as *preliminary triage*.
  * **Layer 2: Deterministic Anthropometric Assessment (Clinical Gold Standard):**
    * Verified physical measurements: Weight, Height/Length, Sex, Exact Age, MUAC.
    * WHO LMS mathematical standard deviation calculation.
    * Clinical Emergency Check: Bilateral pitting oedema and severe wasting ($WHZ < -3$).
  * **Layer 3: Clinical Synthesis & Reconciliation Pipeline:**
    * Discrepancy Reconciliation: If visual AI predicts SAM but physical measurements are normal, logs `false_visual_alarm` and suppresses the false alarm.
    * **Clinical Safety Invariant:** Physical emergency signs (oedema or $WHZ < -3.0$) are **never** hidden or overridden by a reassuring photo.
* **Speaker Notes:**
  > *"Slide 7 represents our core architectural breakthrough: the 3-Layer Decision Pipeline. Layer 1 screens photos under strict optical guardrails. Layer 2 executes deterministic WHO anthropometry. Layer 3 synthesizes both, ensuring that a camera artifact can never trigger a false hospital admission, and a clean photo can never hide a real clinical emergency."*

---

### Slide 8 — Machine Learning Pipeline: LightGBM & TreeSHAP
* **Slide Header:** Machine Learning: Predictive Growth Faltering Core
* **Pipeline Flow:**
  * **Input Vector (14 features):** Child Age, Sex, Dietary Diversity Score (0–8 food groups), Meal Frequency, Exclusive Breastfeeding, Diarrhoea in last 14 days, Fever, Completed Vaccinations (0–7), Maternal Education, Mother's Age, Household Wealth Index (1–5), Urban/Rural residence.
  * **Feature Processing:** One-hot encoding, physiological range clipping, robust median imputation.
  * **LightGBM Ensemble:** Gradient boosted decision trees trained on 40,000+ pediatric records, optimizing high-risk minority class recall.
  * **Isotonic Probability Calibration:** Maps raw logits into calibrated probabilities where predicted risk matches true incidence ($\text{Brier Score} = 0.143$, $\text{ROC-AUC} = 0.87$).
  * **Explainable AI with TreeSHAP:** Mathematically isolates feature contributions:
    * *Example:* $+28\%$ risk from zero dairy/protein intake, $+19\%$ from recurrent diarrhoea, $+12\%$ from maternal literacy gap.
  * **Risk Tiers:** **LOW** ($< 25\%$), **WATCH ZONE** ($25\%–55\%$), **HIGH RISK** ($> 55\%$).
* **Speaker Notes:**
  > *"Instead of waiting for a child to suffer acute wasting, our LightGBM model looks ahead 3 to 6 months. By coupling gradient boosting with non-parametric isotonic calibration and TreeSHAP, we tell the health worker exactly which dietary intervention will reverse the risk trajectory."*

---

### Slide 9 — Deep Learning & Computer Vision: Multimodal ONNX & Safety Gate
* **Slide Header:** Deep Learning Vision AI & Anatomical Biomarker Triage
* **Technical Components:**
  * **Image Suitability & Safety Gate:**
    * *Laplacian Variance ($\sigma^2$):* Rejects motion-blurred images ($\sigma^2 < 25.0$).
    * *Illumination Gate:* Rejects underexposed ($\mu < 30$) or blinding overexposure ($\mu > 235$).
    * *Pediatric Age Bound:* Blocks non-infant subjects ($> 59$ months) with `unsupported_age`.
  * **YCrCb Skin Segmentation & Clothing Obstruction Detection:**
    * Segments human skin pixels in chrominance space ($Cr \in [133, 173], Cb \in [77, 127]$).
    * If bare skin exposure in the thoracic ROI is $< 45\%$, flags `inconclusive_clothing_obstruction`, sets confidence to $0.0\%$, and displays `N/A (Obstructed by clothing)`.
  * **Multimodal ONNX Runtime Inference:**
    * Normalized tensor ($224 \times 224 \times 3$, ImageNet mean/std).
    * High-efficiency cross-platform inference with numerically stable Softmax distribution.
  * **Grad-CAM Attention Overlay:**
    * Visual explainability heatmaps using OpenCV JET colormap to highlight activation regions for clinical verification.
* **Speaker Notes:**
  > *"When an infant is brought for screening, the camera first evaluates optical viability. By converting the image to YCrCb chrominance space, we isolate bare skin. If the child is wearing a thick shirt, jacket, or school uniform, the system refuses to guess, reporting 'Inconclusive due to clothing' rather than inventing false wasting scores."*

---

### Slide 10 — Smart Health Card OCR Engine
* **Slide Header:** Automated Document Ingestion: Hybrid OCR Pipeline
* **Dual Architecture:**
  * **Vector PDF Path (`pdfplumber`):** Extracts digital table structures and character streams from electronic clinic summaries with 100% optical fidelity.
  * **Raster Scan / Photo Path (OpenCV + Tesseract 4):**
    * Preprocessing: Grayscale conversion, Gaussian noise smoothing, Otsu adaptive thresholding, and morphological deskewing.
    * Execution: Dual PSM modes (`--psm 6` for tabular records, `--psm 11` for sparse text).
  * **Multi-Pattern Clinical Regex Parser:** Extracts Child Name, DOB, Age in months, Gender, Weight, Height, MUAC, and Vaccination checks.
  * **Pediatric Decimal Recovery Engine:**
    * Automatically resolves dropped decimal points in low-contrast carbon copies (e.g. `95 kg` $\rightarrow$ `9.5 kg`, `740 cm` $\rightarrow$ `74.0 cm`, `118 cm` $\rightarrow$ `11.8 cm`).
  * **1-Click Clinical Auto-Prefill:** Bridges scanned documents directly into the 6-Step Clinical Assessment form via `sessionStorage`.
* **Speaker Notes:**
  > *"In primary health centres, MCP growth cards are often carbon copies where decimal points fade out. Our OCR pipeline features a specialized decimal recovery engine that converts an impossible 95 kg reading into a biologically validated 9.5 kg infant weight, pre-filling the assessment form in a single click."*

---

### Slide 11 — Zero-Latency Bilingual Engine & Web Dashboard
* **Slide Header:** Grassroots Accessibility: Pure Client-Side English / Hindi Architecture
* **Implementation Details:**
  * **Zero-Latency Performance:** Instantaneous language toggling ($< 5$ ms) without server roundtrips, API calls, or page reloads.
  * **Architecture:**
    * Complete dictionary `/static/js/hi.js` containing `TRANSLATIONS = { en: {...}, hi: {...} }`.
    * Declarative HTML attributes: `data-i18n` for UI text, `data-i18n-placeholder` for form inputs.
    * Dynamic translation helper `t(key)` for runtime elements (Chart.js tooltips, triage badges, OCR status).
    * Cross-session state persistence in browser `localStorage`.
  * **UI/UX Design Standards:**
    * Clean, dark emerald-green and cyan palette (`#040d0a`, `#34d399`, `#22d3ee`).
    * Role-based interfaces: Simple visual triage cards for parents vs. granular z-score metrics for medical officers.
    * Interactive growth velocity trajectories using Chart.js against WHO reference percentiles.
* **Speaker Notes:**
  > *"For an AI tool to work in rural Maharashtra or Bihar, language cannot be a barrier. We built a pure client-side bilingual translation engine in vanilla JavaScript. A single click flips the entire platform between English and Hindi in under 5 milliseconds with zero internet overhead."*

---

### Slide 12 — Experimental Results & Automated Clinical Safety Tests
* **Slide Header:** Verification, Validation & Test Suite Execution
* **Automated Regression Suite (18 Tests, 100% Pass Rate):**
  * `test_1_healthy_school_aged_child_not_flagged_as_sam`: Rejects school-aged child from infant model (`unsupported_age` / clothing obstruction).
  * `test_2_healthy_child_within_supported_age`: Correctly processes healthy infant within 0–59m.
  * `test_3_confirmed_acute_malnutrition_image`: Validates genuine wasting on exposed bare skin.
  * `test_4_unsuitable_lighting_and_extreme_blur`: Laplacian filter correctly rejects motion blur.
  * `test_5_missing_or_corrupted_image`: Graceful 400 Bad Request error handling.
  * `test_6_unavailable_onnx_model_fallback`: Stable fallback when neural weights are missing.
  * `test_7_class_index_mapping`: Confirms exact index mapping (`0: Healthy, 1: MAM, 2: SAM`).
  * `test_8_input_normalization_and_channels`: Verifies RGB ImageNet normalization tensor.
  * `test_9_missing_required_fields_handling`: Rejects incomplete clinical assessment payloads.
  * `test_10_screening_discrepancy_handled_correctly`: Flags `false_visual_alarm` when measurements normal.
  * `test_11_out_of_range_model_outputs`: Verifies numerically stable Softmax bounds.
  * `test_12_no_fabricated_confidence_on_inconclusive`: Asserts `confidence = 0.0%` on obstructed photos.
  * `test_13_urgent_clinical_danger_never_hidden`: Guarantees physical emergency referral is never suppressed.
  * `test_core_flow.py` (5 tests): End-to-end auth, CRUD, WHO classification, OCR, and resources.
* **Speaker Notes:**
  > *"Safety in healthcare AI requires exhaustive automated regression testing. We wrote and verified 18 automated test suites covering 13 critical failure scenarios. All 18 tests execute in under 3.5 seconds with zero failures."*

---

### Slide 13 — Case Studies & Before-and-After Analysis
* **Slide Header:** Field Demonstration: Eliminating False Severe Alarms
* **Visual Case Comparison:**

| Screening Scenario | Previous Flawed Implementation | Corrected ChildNutri AI Pipeline |
| :--- | :--- | :--- |
| **Case 1: Healthy School Child (`healthy_kid.jpg`)** | • Verdict: 🔴 **Severe (SAM)**<br>• SAM Probability: **78%**<br>• Rib Prominence: **98/100** (Uniform collar)<br>• Limb Wasting: **64/100** (Navy tie shadow)<br>• Action: Immediate hospital referral | • Status: ⚪ **Inconclusive (Clothing Obstruction)**<br>• Confidence: **0.0%** (Refuses false certainty)<br>• Rib Prominence: **`N/A`** (Torso covered)<br>• Limb Wasting: **`N/A`**<br>• Action: Perform physical anthropometry |
| **Case 2: Discrepancy Reconciliation** | • Visual prediction overwrote clinical diagnosis | • Layer 3 detects discrepancy: flags `false_visual_alarm`<br>• Verified normal WHO measurements take precedence |
| **Case 3: Genuine Bare-Torso Infant Wasting** | • Often confused with background shadows | • Passes suitability gate ($>70\%$ bare skin)<br>• Triage highlights wasting; physical SAM confirmed |

* **Speaker Notes:**
  > *"Here is the direct comparison. Previously, a healthy school-aged girl in uniform was flagged as 78% SAM with an urgent hospital transfer order because her necktie was miscalculated as exposed ribs. Today, our system safely flags clothing obstruction, zeros out fabricated confidence, and asks for verified physical measurements."*

---

### Slide 14 — Conclusion, Future Scope & References
* **Slide Header:** Conclusion, Future Roadmap & References
* **Key Takeaways:**
  * Successfully developed an end-to-end, explainable pediatric malnutrition screening platform.
  * Solved the critical false-positive vision bug by implementing a 3-Layer Decision Hierarchy and Image Suitability Gate.
  * Delivered zero-latency bilingual accessibility for grassroots Anganwadi workers.
* **Future Scope:**
  * Real-world clinical validation trials across district NRC centers in collaboration with public health agencies.
  * Edge deployment on mobile Android devices (ONNX Runtime Mobile & WebAssembly).
  * Direct integration with the Government of India's Poshan Tracker API.
* **Primary References:**
  1. *WHO Child Growth Standards: Length/height-for-age, weight-for-age, weight-for-length, weight-for-height and body mass index-for-age.* World Health Organization, 2006.
  2. Ke, G., et al. *"LightGBM: A Highly Efficient Gradient Boosting Decision Tree."* NeurIPS 2017.
  3. Lundberg, S. M., & Lee, S. I. *"A Unified Approach to Interpreting Model Predictions (SHAP)."* NeurIPS 2017.
  4. Selvaraju, R. R., et al. *"Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization."* ICCV 2017.
* **Speaker Notes:**
  > *"In conclusion, ChildNutri AI demonstrates that AI in pediatric healthcare must be conservative, explainable, and accountable. By anchoring deep learning within deterministic clinical guardrails, we ensure technology serves clinicians without manufacturing false emergencies. Thank you. We now welcome questions from the committee."*
