"""
Generate a professional 14-slide PowerPoint presentation for ChildNutri AI capstone project.
Theme: Premium Dark Emerald Green (#040d0a), Teal/Mint (#34d399), Cyan (#22d3ee), White text.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    DARK_BG = RGBColor(4, 13, 10)       # #040d0a
    CARD_BG = RGBColor(13, 40, 24)      # #0d2818
    CARD_BORDER = RGBColor(16, 185, 129)# #10b981
    TEAL_MINT = RGBColor(52, 211, 153)  # #34d399
    CYAN_ACCENT = RGBColor(34, 211, 238)# #22d3ee
    TEXT_WHITE = RGBColor(240, 253, 250)# #f0fdfa
    TEXT_MUTED = RGBColor(148, 163, 184)# #94a3b8
    CORAL_ALERT = RGBColor(248, 113, 113)# #f87171

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = DARK_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="CHILDNUTRI AI  |  B.TECH CAPSTONE DEFENSE"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = CYAN_ACCENT

        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = TEAL_MINT

    def add_card(slide, left, top, width, height, title, items, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT

        for item in items:
            p_item = tf.add_paragraph()
            p_item.text = f"•  {item}"
            p_item.font.size = Pt(11)
            p_item.font.color.rgb = TEXT_WHITE
            p_item.space_before = Pt(5)

    # ---------------- SLIDE 1: Title Slide ----------------
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)
    
    tb = slide1.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.3), Inches(5.5))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = "G.H. RAISONI COLLEGE OF ENGINEERING AND MANAGEMENT, PUNE"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    p = tf.add_paragraph()
    p.text = "Department of Computer Science & Engineering (AI & ML)"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    p = tf.add_paragraph()
    p.text = "ChildNutri AI: Malnourishment Identification in Infants Using AI"
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = TEAL_MINT
    p.space_before = Pt(20)

    p = tf.add_paragraph()
    p.text = "An Explainable Multimodal Healthcare Platform Combining Deep Learning Vision,\nDeterministic WHO Anthropometry, and Calibrated Machine Learning"
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(8)

    p = tf.add_paragraph()
    p.text = "Group No: O-33   |   Academic Year: 2025–2026\nProject Guide: Prof. Shridhar Venkatanarasimha"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT
    p.space_before = Pt(28)

    p = tf.add_paragraph()
    p.text = "Team Members: Kalpak Shende (L-09)  •  Subhashish Barik (L-33)  •  Vishweshwar Yadav (L-55)"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(8)

    # ---------------- SLIDE 2: Table of Contents ----------------
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "Presentation Outline & Key Agenda")
    add_card(slide2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Part 1: Motivation & System Core", [
        "Clinical Background: National & Global Pediatric Burden",
        "Problem Statement & Diagnostic Failure Modes in Existing AI",
        "Project Objectives & Proposed Multimodal Scope",
        "Literature Survey & Technical Comparative Benchmarks",
        "Core Architectural Breakthrough: The 3-Layer Clinical Hierarchy",
        "Predictive Machine Learning: LightGBM & TreeSHAP"
    ])
    add_card(slide2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Part 2: Vision, OCR, UX & Validation", [
        "Deep Learning Vision AI & Clinical Safety Gate (YCrCb Skin)",
        "Automated Ingestion: Hybrid Vector & Tesseract OCR Engine",
        "Zero-Latency Client-Side English / Hindi Translation Architecture",
        "Comprehensive Automated Regression Suite (18 Tests, 100% Pass)",
        "Case Study Walkthrough: Eliminating False SAM Predictions",
        "Conclusion, Public Health Impact & Future Scope"
    ])

    # ---------------- SLIDE 3: Introduction & Motivation ----------------
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "Clinical Background: The Silent Pediatric Emergency")
    add_card(slide3, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "The National Malnutrition Burden", [
        "India accounts for ~1/3 of global acute child malnutrition.",
        "NFHS-5 statistics reveal 35.5% stunting, 19.3% wasting, and 7.7% severe acute malnutrition (SAM).",
        "Malnutrition is an underlying risk factor in over 68% of under-5 child deaths nationwide."
    ])
    add_card(slide3, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "The 'First 1,000 Days' Window", [
        "Conception to 24 months represents the critical developmental window.",
        "Undetected growth faltering causes irreversible cognitive loss and stunted physical potential.",
        "Severe Acute Malnutrition (SAM) increases child mortality risk by 9x without urgent stabilization."
    ])
    add_card(slide3, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "Grassroots Delivery Bottlenecks", [
        "Frontline Anganwadi workers face heavy manual workload and uncalibrated analog hanging scales.",
        "Paper Mother-Child Protection (MCP) cards suffer from damaged or lost carbon copies.",
        "Lack of clinical decision support to explain subtle faltering signs before severe damage."
    ])

    # ---------------- SLIDE 4: Problem Statement ----------------
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "Problem Statement: Diagnostic Gaps & Unvalidated AI Overreach")
    add_card(slide4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Healthcare Delivery Failures", [
        "Late Detection: Current clinical screening detects malnutrition only after severe muscle wasting and tissue atrophy occur.",
        "Manual Transcription Friction: Frontline workers manually compute child ages in days and plot curves, yielding >25% human calculation errors.",
        "Paper Data Silos: Immunization and growth cards are isolated in physical files without longitudinal risk alerts."
    ])
    add_card(slide4, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "The 'Black-Box Vision Trap'", [
        "Unvalidated AI Overreach: Typical vision models mistake clothing collars, neckties, buttons, and backpack straps for exposed ribcage bones.",
        "Age Incompatibility: Models built for infants (<5 years) generate false SAM emergencies when given photos of school-aged children.",
        "Fabricated Precision: Applications output uncalibrated 98/100 rib scores without checking if the child's torso is even bare.",
        "Lack of Explainability: Clinicians reject opaque AI outputs that lack medical audit trails."
    ], border_color=CORAL_ALERT)

    # ---------------- SLIDE 5: Objectives & Scope ----------------
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "Project Objectives & Scope of ChildNutri AI")
    add_card(slide5, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "1. Deterministic Anthropometry", [
        "Implement exact WHO 2006 LMS standard deviation equations for WAZ, HAZ, WHZ, and BAZ.",
        "Zero rounding errors, achieving clinical grade parity with official WHO Anthro software.",
        "Enforce strict CMAM emergency criteria for bilateral oedema and MUAC < 11.5 cm."
    ])
    add_card(slide5, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "2. Predictive ML & Vision", [
        "Build a LightGBM future-risk engine forecasting faltering 3–6 months in advance.",
        "Isotonic probability calibration (ROC-AUC: 0.87, Brier: 0.143) with TreeSHAP explanations.",
        "Develop an Image Suitability & Safety Gate (YCrCb skin segmentation, Laplacian focus, age gate)."
    ])
    add_card(slide5, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "3. Automation & Usability", [
        "Hybrid OCR engine (pdfplumber + Tesseract 4) with automatic pediatric decimal recovery.",
        "Zero-latency client-side English / Hindi translation engine for grassroots Anganwadi workers.",
        "Downloadable medical PDF clinical reports and longitudinal growth trajectory charts."
    ])

    # ---------------- SLIDE 6: Literature Survey ----------------
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Literature Survey & Technical Comparative Benchmarking")
    add_card(slide6, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "Conventional Clinical Tools", [
        "WHO Anthro Software: Accurate LMS calculation but requires manual PC data entry with zero predictive risk forecasting.",
        "Analog MUAC Tapes: Rapid field triage, but subject to high observer variability and tension errors.",
        "Paper Health Cards: High loss rate, zero longitudinal automated alerting."
    ])
    add_card(slide6, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "Academic Vision AI Papers", [
        "Typical deep learning papers evaluate standard CNNs on small, clean datasets.",
        "Major vulnerability: Models learn spurious background correlations (school buses, dark shadows).",
        "Fails on clothed children: Models invent rib prominence from folded fabric and ties."
    ])
    add_card(slide6, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "ChildNutri AI Innovations", [
        "3-Layer Clinical Hierarchy: Visual screening is treated as preliminary; physical measurements strictly govern diagnosis.",
        "Image Suitability Gate: Refuses to guess on clothed children, setting confidence to 0.0% and biomarkers to N/A.",
        "Full Stack Integration: Connects photo triage, OCR, LightGBM future risk, and personalized diet plans."
    ])

    # ---------------- SLIDE 7: System Architecture ----------------
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "System Architecture: 3-Layer Clinical Decision Hierarchy")
    add_card(slide7, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "Layer 1: Visual Screening Gate", [
        "Input: Child Photo + Age (months)",
        "Image Quality Gate: Rejects blur (Laplacian < 25.0) and extreme illumination.",
        "Pediatric Age Gate: Enforces 0–59 months; rejects school-age children.",
        "Clothing Obstruction Check: Bare skin < 45% -> Inconclusive, 0.0% confidence, N/A scores.",
        "Multimodal ONNX Inference + Grad-CAM."
    ])
    add_card(slide7, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "Layer 2: Deterministic WHO Anthro", [
        "Input: Verified Weight, Height, Age, Sex, MUAC, Bilateral Oedema.",
        "Exact WHO 2006 LMS formulas compute WAZ, HAZ, WHZ standard deviations.",
        "Deterministic Emergency Triggers: Bilateral pitting oedema or WHZ < -3.0 SD immediately flags clinical SAM.",
        "Cannot be overridden by any photograph."
    ])
    add_card(slide7, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "Layer 3: Clinical Reconciliation", [
        "Discrepancy Resolution: If Photo = SAM but Physical = Normal, flags 'false_visual_alarm' and defers to physical diagnosis.",
        "Safety Invariant: If Physical = SAM, immediate hospital NRC referral is NEVER suppressed or delayed.",
        "Generates SHAP risk explanations, tailored 6-module diet plan, and PDF report."
    ])

    # ---------------- SLIDE 8: ML Pipeline ----------------
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "Machine Learning Pipeline: LightGBM Future-Risk Engine")
    add_card(slide8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Feature Engineering & Model Training", [
        "14 Multi-Domain Input Features: Child age, sex, 0–8 dietary diversity, meal frequency, breastfeeding, diarrhoea in last 14 days, fever, vaccines, maternal literacy, household wealth index, urban/rural.",
        "LightGBM Classifier: Gradient boosted decision trees optimized for high recall on the vulnerable minority class.",
        "Non-Parametric Isotonic Calibration: Calibrates raw tree logits to true empirical risk (Brier Score = 0.143, ROC-AUC = 0.87)."
    ])
    add_card(slide8, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Explainable AI (TreeSHAP) & Tiers", [
        "TreeSHAP Attribution: Quantifies exact marginal contribution of each lifestyle and biological risk factor.",
        "Example Output: '+28% risk due to zero protein intake, +19% from recent diarrhoea, +12% from mother literacy gap'.",
        "Clinical Risk Tiers: LOW (<25%), WATCH ZONE (25%–55%), HIGH RISK (>55%).",
        "Directly drives custom dietary intervention and Anganwadi home-visit schedules."
    ])

    # ---------------- SLIDE 9: Deep Learning Vision AI ----------------
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "Computer Vision: Multimodal ONNX & Clinical Safety Gate")
    add_card(slide9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Image Suitability & Safety Guardrails", [
        "Laplacian Focus Gate: Rejects motion blur with variance threshold sigma^2 >= 25.0.",
        "Illumination Gate: Rejects severe underexposure (<30) and blinding glare (>235).",
        "Pediatric Age Gate: Enforces 0–59 months; halts scoring for school-aged children.",
        "YCrCb Chrominance Skin Segmentation: Calculates bare skin ratio in thoracic ROI; if <45%, safely flags 'inconclusive_clothing_obstruction'."
    ])
    add_card(slide9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "ONNX Inference & Grad-CAM Heatmaps", [
        "ONNX Runtime Execution: 224x224 RGB tensor with ImageNet normalization and stable Softmax.",
        "Qualified Biomarkers: Directional Sobel vertical gradient density for ribs, orbital contrast for facial fat, and arm contour ratios.",
        "Meters show 'N/A (Obstructed by clothing)' when torso is covered.",
        "Grad-CAM Heatmap: Overlays JET colormap attention check, ensuring transparency for healthcare workers."
    ])

    # ---------------- SLIDE 10: OCR Engine ----------------
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Smart Health Card OCR: Automated Document Digitization")
    add_card(slide10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Hybrid Optical Processing Architecture", [
        "Vector PDF Route (pdfplumber): Direct embedded text stream extraction with 100% precision from clinic discharge summaries.",
        "Raster Scan Route (OpenCV + Tesseract 4): Grayscale conversion, Gaussian smoothing, Otsu adaptive binarization, and deskewing.",
        "Dual PSM Execution: Uses PSM 6 for structured tabular blocks and PSM 11 for sparse medical text fields."
    ])
    add_card(slide10, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Decimal Recovery & 1-Click Form Pre-Fill", [
        "Pediatric Decimal Recovery Engine: Automatically resolves dropped periods in faded carbon copies:",
        "  - Converts '95 kg' to biological '9.5 kg' infant weight.",
        "  - Converts '740 cm' to '74.0 cm' length.",
        "Multi-Pattern Regex: Extracts child name, DOB, weight, height, MUAC, and immunization marks.",
        "1-Click 'Use in Assessment': Prefills 6-step screening wizard in sessionStorage."
    ])

    # ---------------- SLIDE 11: Bilingual Engine & UI ----------------
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11)
    add_header(slide11, "Grassroots UX: Zero-Latency Client-Side English / Hindi Engine")
    add_card(slide11, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Zero-Latency Client-Side i18n Architecture", [
        "Pure Vanilla JavaScript: Zero external dependencies, zero API calls, and zero page reloads.",
        "Global Dictionary (/static/js/hi.js): Structured mirror translations for thousands of UI strings, medical terms, and clinical warnings.",
        "Declarative Markup: data-i18n for text nodes and data-i18n-placeholder for form inputs.",
        "Instant Single-Pass DOM Traversal: Switches entire interface language in <5 milliseconds.",
        "Persistent State: Remembers user preference across visits in browser localStorage."
    ])
    add_card(slide11, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Premium Field Dashboard UX", [
        "Theme: Accessible dark emerald-green and cyan palette (#040d0a, #34d399, #22d3ee).",
        "Dual Persona Views: Non-intimidating visual cards for parents vs. granular z-score metrics for doctors.",
        "Interactive Chart.js Growth Trajectories: Visualizes WAZ over time against WHO standard percentile curves.",
        "Downloadable Medical PDF Reports: Standardized clinical summaries generated via ReportLab."
    ])

    # ---------------- SLIDE 12: Testing & Results ----------------
    slide12 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide12)
    add_header(slide12, "Verification, Validation & Automated Clinical Safety Tests")
    add_card(slide12, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Automated Regression Test Suite (18 Tests)", [
        "100% Pass Rate across all 18 clinical unit & integration tests in 3.27 seconds.",
        "Test 1: Clothed school-aged child rejected (status: unsupported_age / clothing obstruction).",
        "Test 2: Healthy infant correctly evaluated within supported 0–59m age range.",
        "Test 3: Confirmed acute malnutrition correctly analyzed on exposed bare skin.",
        "Test 4: Laplacian focus check rejects motion blur and extreme glare.",
        "Test 5–8: Validates ONNX fallback, class index mapping, and RGB normalization."
    ])
    add_card(slide12, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Clinical Safety Invariants Verified", [
        "Test 9: Rejects incomplete clinical assessment payloads.",
        "Test 10: Discrepancy reconciliation flags 'false_visual_alarm' when physical anthropometry is normal.",
        "Test 11: Validates numerically stable Softmax bounds [0.0, 1.0].",
        "Test 12: Asserts confidence = 0.0% and biomarkers = N/A on obstructed photos.",
        "Test 13: Emergency Clinical Invariant: Confirms physical SAM or oedema hospital referral is NEVER suppressed.",
        "5 Core Flow Tests: Auth, CRUD, WHO classifications, OCR, and resource seeding."
    ])

    # ---------------- SLIDE 13: Case Studies (Before & After) ----------------
    slide13 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide13)
    add_header(slide13, "Case Study Demonstration: Eliminating False SAM Predictions")
    add_card(slide13, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Case 1: Clothed School Child (healthy_kid.jpg)", [
        "Previous Flawed Implementation:",
        "  - Verdict: Severe Acute Malnutrition (SAM)",
        "  - SAM Probability: 78% (Confidence: 77.9%)",
        "  - Ribcage Prominence: 98/100 (Fabric collar & buttons)",
        "  - Limb Wasting: 64/100 (Navy tie shadow)",
        "  - Action: Immediate hospital NRC emergency referral",
        "Corrected ChildNutri AI Pipeline:",
        "  - Status: Inconclusive (Clothing Obstruction) / Unsupported Age",
        "  - Confidence: 0.0% (Refuses false certainty)",
        "  - Rib Prominence & Arm Wasting: N/A (Torso covered)",
        "  - Action: Request standard physical measurements"
    ], border_color=CORAL_ALERT)
    add_card(slide13, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Case 2 & 3: Clinical Reconciliation & True SAM", [
        "Case 2: Image vs. Anthropometry Discrepancy:",
        "  - Photo predicted possible SAM, but physical measurements normal (WHZ >= -2.0, MUAC >= 12.5cm).",
        "  - System flags 'false_visual_alarm', explains clothing artifact, and normal clinical diagnosis takes precedence.",
        "Case 3: Genuine Infant Acute Malnutrition:",
        "  - Infant <59 months with bare torso (>70% skin exposure).",
        "  - Passes quality gate; visual triage indicates severe wasting.",
        "  - Physical measurements confirm WHZ < -3.0 SD -> Urgent NRC referral reinforced without delay."
    ])

    # ---------------- SLIDE 14: Conclusion & Future Scope ----------------
    slide14 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide14)
    add_header(slide14, "Conclusion, Future Roadmap & Primary References")
    add_card(slide14, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "Key Project Contributions", [
        "Engineered a clinically safe, explainable pediatric malnutrition screening platform.",
        "Resolved the critical vision false-positive bug with a 3-Layer Clinical Hierarchy.",
        "Enabled zero-latency English / Hindi field localization for rural frontline workers.",
        "Delivered a 100% passing automated clinical safety test suite."
    ])
    add_card(slide14, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "Future Development Roadmap", [
        "Clinical trials at district Nutrition Rehabilitation Centres (NRC) in collaboration with NHM.",
        "Edge mobile deployment using ONNX Runtime Mobile and WebAssembly for offline Anganwadi tablets.",
        "Direct API integration with the Government of India's Poshan Tracker system."
    ])
    add_card(slide14, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "Key Literature References", [
        "1. WHO Child Growth Standards: Length/height-for-age, weight-for-age, WHZ (World Health Organization, 2006).",
        "2. Ke, G., et al. 'LightGBM: A Highly Efficient Gradient Boosting Decision Tree' (NeurIPS 2017).",
        "3. Lundberg & Lee. 'A Unified Approach to Interpreting Model Predictions (SHAP)' (NeurIPS 2017).",
        "4. Selvaraju et al. 'Grad-CAM: Visual Explanations via Localization' (ICCV 2017)."
    ])

    output_path = "/Users/varadpendkar/Downloads/Child_nutri_AI/childnutri/childnutri_presentation.pptx"
    prs.save(output_path)
    # Also save to parent directory if accessible
    parent_path = "/Users/varadpendkar/Downloads/Child_nutri_AI/child.pptx"
    try:
        prs.save(parent_path)
    except Exception:
        pass
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_presentation()
