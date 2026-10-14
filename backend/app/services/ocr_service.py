"""
ChildNutri AI — OCR & Document Extraction Pipeline for Health Reports
Extracts: weight, height, MUAC, haemoglobin, head circumference, age/DOB, vaccines, date,
feeding practices, health history, and home context.

Architecture (sustainable hybrid pipeline):
1. Vector PDFs (e.g., ReportLab, clinic EMR exports):
   Direct digital text extraction via pdfplumber (with PyMuPDF fallback).
   Extracts pristine text without OCR distortion.
2. Scanned / Image PDFs:
   Converts PDF pages to high-res images via pdf2image (with PyMuPDF pixmap fallback).
   Preprocesses with OpenCV (normalized grayscale) and runs Tesseract OCR.
3. Image uploads (JPEG, PNG):
   Preprocesses with OpenCV and runs Tesseract OCR (with PIL fallback).
4. Regex extraction & clinical sanity checks.
"""
from __future__ import annotations
import os
import re
import math
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from pdf2image import convert_from_bytes, convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


# ── Image preprocessing ───────────────────────────────────────────────────────

def _preprocess_image(path: str) -> "np.ndarray":
    """Load and normalize image for OCR without destructive thresholding."""
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if max(h, w) < 1600:
        scale = 1600 / max(h, w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    return gray


def _pdf_to_images(pdf_path: str, out_dir: str) -> list[str]:
    """Convert PDF pages to image files on disk."""
    images = []

    # Strategy 1: pdf2image (poppler)
    if HAS_PDF2IMAGE:
        try:
            with open(pdf_path, "rb") as f:
                pil_imgs = convert_from_bytes(f.read(), dpi=200)
            for i, pimg in enumerate(pil_imgs):
                dest = os.path.join(out_dir, f"page_{i}.png")
                pimg.save(dest, "PNG")
                images.append(dest)
            if images:
                return images
        except Exception:
            images = []

    # Strategy 2: PyMuPDF pixmaps (self-contained, no poppler binary needed)
    if HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                dest = os.path.join(out_dir, f"page_{i}.png")
                pix.save(dest)
                images.append(dest)
        except Exception:
            pass

    return images


def _extract_vector_pdf_text(pdf_path: str) -> str:
    """Extract digital text directly from vector PDF if available."""
    # Try pdfplumber first
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = [p.extract_text() or "" for p in pdf.pages]
                full = "\n".join(pages_text).strip()
                if len(full) >= 20:
                    return full
        except Exception:
            pass

    # Try PyMuPDF fallback
    if HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            pages_text = [p.get_text() or "" for p in doc]
            full = "\n".join(pages_text).strip()
            if len(full) >= 20:
                return full
        except Exception:
            pass

    return ""


# ── Field extraction rules ────────────────────────────────────────────────────

_SANITY = {
    "weight_kg": (1.5, 30.0),
    "height_cm": (40.0, 130.0),
    "muac_cm": (7.0, 25.0),
    "head_circ_cm": (25.0, 55.0),
    "hb_gdl": (4.0, 20.0),
    "age_months": (0, 60),
}


def _parse_health_card_text(text: str) -> dict:
    """
    Robust health card & clinic report text parser.
    Extracts core anthropometry, feeding practices, health history, and home context.
    """
    data: dict = {}
    text_lower = text.lower()

    # Child name
    m = re.search(r'child\s*name\s*[:\-=]\s*([A-Za-z\s]+?)(?=\s+(?:registration|reg|dob|date|sex|age|father|mother|\n|$))', text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if len(name) >= 2:
            data['child_name'] = name.title()

    # Age in months
    m = re.search(r'age\s*(?:\(months?\))?\s*[:\-=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1))
            if 0 <= val <= 72:
                data['age_months'] = val
        except ValueError:
            pass
    if 'age_months' not in data:
        # Check patterns like "12 mo" or "12 months"
        m2 = re.search(r'\b(\d{1,2})\s*(?:months?|mo\b)', text, re.IGNORECASE)
        if m2:
            data['age_months'] = float(m2.group(1))

    # Measurement date
    m = re.search(r'(?:date\s*of\s*measurement|measurement\s*date|assessment\s*date|date)\s*[:\-=]?\s*(\d{1,2})\s*[\/\-\.]\s*(\d{1,2})\s*[\/\-\.]\s*(\d{2,4})', text, re.IGNORECASE)
    if m:
        d, mon, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = '20' + y
        data['measurement_date'] = f'{y}-{int(mon):02d}-{int(d):02d}'
    else:
        # ISO format: YYYY-MM-DD
        m_iso = re.search(r'\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b', text)
        if m_iso:
            y, mon, d = m_iso.group(1), m_iso.group(2), m_iso.group(3)
            data['measurement_date'] = f'{y}-{int(mon):02d}-{int(d):02d}'

    # Weight (kg) — Avoid "birth weight" if regular weight is available
    m_wt = re.search(r'(?<!birth\s)\b(?:weight|wt)\b[^\d\n]*?(\d+\.?\d*)\s*(?:kg|kgs)?', text, re.IGNORECASE)
    if m_wt:
        try:
            w = float(m_wt.group(1))
            if _SANITY['weight_kg'][0] <= w <= _SANITY['weight_kg'][1]:
                data['weight_kg'] = w
            elif 30.0 < w <= 300.0:  # Decimal point omitted in OCR, e.g. 95 -> 9.5
                data['weight_kg'] = round(w / 10.0, 2)
        except ValueError:
            pass
    if 'weight_kg' not in data:
        # Fallback to birth weight if nothing else
        m_bwt = re.search(r'birth\s*weight[^\d\n]*?(\d+\.?\d*)', text, re.IGNORECASE)
        if m_bwt:
            try:
                w = float(m_bwt.group(1))
                if 1.5 <= w <= 10.0:
                    data['weight_kg'] = w
            except ValueError:
                pass

    # Height / Length (cm)
    m_ht = re.search(r'\b(?:height|length|ht|len)\b[^\d\n]*?(\d+\.?\d*)\s*(?:cm)?', text, re.IGNORECASE)
    if m_ht:
        try:
            h = float(m_ht.group(1))
            if _SANITY['height_cm'][0] <= h <= _SANITY['height_cm'][1]:
                data['height_cm'] = h
            elif 400.0 <= h <= 1300.0:  # Decimal point omitted, e.g. 760 -> 76.0
                data['height_cm'] = round(h / 10.0, 1)
        except ValueError:
            pass

    # MUAC (cm)
    m_muac = re.search(r'\b(?:muac|mid[\s-]?upper[\s-]?arm)\b[^\d\n]*?(\d+\.?\d*)\s*(?:cm)?', text, re.IGNORECASE)
    if m_muac:
        try:
            val = float(m_muac.group(1))
            if _SANITY['muac_cm'][0] <= val <= _SANITY['muac_cm'][1]:
                data['muac_cm'] = val
        except ValueError:
            pass

    # Head Circumference (cm)
    m_hc = re.search(r'\b(?:head\s*circumference|hc)\b[^\d\n]*?(\d+\.?\d*)\s*(?:cm)?', text, re.IGNORECASE)
    if m_hc:
        try:
            val = float(m_hc.group(1))
            if _SANITY['head_circ_cm'][0] <= val <= _SANITY['head_circ_cm'][1]:
                data['head_circ_cm'] = val
        except ValueError:
            pass

    # Haemoglobin (g/dL)
    m_hb = re.search(r'\b(?:hb|haemoglobin|hemoglobin)\b\s*[:\-=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if m_hb:
        try:
            val = float(m_hb.group(1))
            if _SANITY['hb_gdl'][0] <= val <= _SANITY['hb_gdl'][1]:
                data['hb_gdl'] = val
        except ValueError:
            pass

    # Sex
    m_sex = re.search(r'\bsex\s*[:\-=]?\s*(male|female|boy|girl)\b', text, re.IGNORECASE)
    if m_sex:
        data['sex'] = 'Male' if 'm' in m_sex.group(1).lower() else 'Female'

    # Breastfed
    m_bf = re.search(r'breastfeed(?:ing)?\??\s*[:\-=]?\s*(yes|no|true|false)\b', text, re.IGNORECASE)
    if m_bf:
        data['breastfed'] = m_bf.group(1).lower() in ('yes', 'true')

    # Appetite
    m_app = re.search(r'appetite\s*[:\-=]?\s*(good|poor|refuses?|normal)\b', text, re.IGNORECASE)
    if m_app:
        val = m_app.group(1).lower()
        data['appetite'] = 'good' if val in ('good', 'normal') else ('poor' if 'poor' in val else 'refuses')

    # Food groups eaten yesterday (0–8)
    m_fg = re.search(r'food\s*groups?[^:\d\n]*?(?:\([^\)]*\))?\s*[:\-=]?\s*(\d+)', text, re.IGNORECASE)
    if m_fg:
        try:
            val = int(m_fg.group(1))
            if 0 <= val <= 8:
                data['food_groups_yesterday'] = val
        except ValueError:
            pass

    # Meals per day
    m_mpd = re.search(r'meals\s*(?:per\s*day)?[^:\d\n]*?(?:\([^\)]*\))?\s*[:\-=]?\s*(\d+)', text, re.IGNORECASE)
    if m_mpd:
        try:
            val = int(m_mpd.group(1))
            if 0 <= val <= 10:
                data['meals_per_day'] = val
        except ValueError:
            pass

    # Diarrhoea in last 2 weeks
    m_diar = re.search(r'diarrh(?:oea|ea)[^\n]*?(yes|no)\b', text, re.IGNORECASE)
    if m_diar:
        data['diarrhoea_2w'] = (m_diar.group(1).lower() == 'yes')

    # Fever in last 2 weeks
    m_fev = re.search(r'fever[^\n]*?(yes|no)\b', text, re.IGNORECASE)
    if m_fev:
        data['fever_2w'] = (m_fev.group(1).lower() == 'yes')

    # Vaccination status
    if 'fully vaccinated' in text_lower or 'full' in text_lower:
        data['vaccination_status'] = 'full'
    elif 'partially vaccinated' in text_lower or 'partial' in text_lower:
        data['vaccination_status'] = 'partial'
    elif 'no vaccination' in text_lower or 'unvaccinated' in text_lower:
        data['vaccination_status'] = 'none'

    # Mother / caregiver education
    if 'no formal education' in text_lower or 'illiterate' in text_lower:
        data['mother_education'] = 'none'
    elif 'primary' in text_lower:
        data['mother_education'] = 'primary'
    elif 'secondary' in text_lower or '10th' in text_lower:
        data['mother_education'] = 'secondary'
    elif 'higher' in text_lower or 'graduate' in text_lower:
        data['mother_education'] = 'higher'

    # Mother age
    m_mage = re.search(r'mother\s*age[^\d\n]*?(\d+)', text, re.IGNORECASE)
    if m_mage:
        try:
            val = int(m_mage.group(1))
            if 14 <= val <= 60:
                data['mother_age'] = val
        except ValueError:
            pass

    # Household wealth score (1–5)
    m_ws = re.search(r'wealth\s*score[^:\d\n]*?(?:\([^\)]*\))?\s*[:\-=]?\s*(\d+)', text, re.IGNORECASE)
    if m_ws:
        try:
            val = int(m_ws.group(1))
            if 1 <= val <= 5:
                data['wealth_score'] = val
        except ValueError:
            pass

    # Area type (Urban / Rural)
    m_area = re.search(r'area\s*(?:type)?[^\w\n]*?(urban|rural)\b', text, re.IGNORECASE)
    if m_area:
        data['rural_urban'] = m_area.group(1).title()

    # Bilateral Oedema
    if 'oedema' in text_lower or 'edema' in text_lower:
        if 'absent' in text_lower or 'no' in text_lower:
            data['bilateral_edema'] = False
        elif 'present' in text_lower or 'yes' in text_lower:
            data['bilateral_edema'] = True

    # How measured
    if 'doctor' in text_lower or 'nurse' in text_lower:
        data['how_measured'] = 'doctor'
    elif 'anganwadi' in text_lower or 'aww' in text_lower:
        data['how_measured'] = 'anganwadi'

    # Food preference
    if 'non-vegetarian' in text_lower or 'non-veg' in text_lower:
        data['food_preference'] = 'non-veg'
    elif 'vegetarian' in text_lower or 'veg' in text_lower:
        data['food_preference'] = 'veg'

    return data


def _has_hindi_pack() -> bool:
    """Check if Hindi Tesseract language pack is installed."""
    if not HAS_OCR:
        return False
    try:
        langs = pytesseract.get_languages()
        return "hin" in langs
    except Exception:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def extract_from_report(file_path: str, temp_dir: str = "/tmp") -> dict:
    """
    Main extraction function for reports (PDF or images).
    Sustainable hybrid approach:
    - If vector PDF: pdfplumber / fitz text extraction directly.
    - If scanned PDF / images: image conversion + OpenCV + Tesseract OCR.
    """
    all_text = ""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # 1. Try vector text extraction first
        vector_text = _extract_vector_pdf_text(file_path)
        if len(vector_text.strip()) >= 20:
            all_text = vector_text
        else:
            # 2. Scanned PDF: convert to images and OCR
            if not HAS_OCR:
                return {
                    "status": "no_ocr",
                    "fields": {},
                    "full_text": "",
                    "raw_text": "",
                    "review_required": True,
                    "message": "Scanned PDF requires Tesseract OCR and pytesseract.",
                }

            image_paths = _pdf_to_images(file_path, temp_dir)
            for img_path in image_paths:
                try:
                    processed = _preprocess_image(img_path)
                    text = pytesseract.image_to_string(
                        processed,
                        lang="eng+hin" if _has_hindi_pack() else "eng",
                        config="--psm 6"
                    )
                    all_text += "\n" + text
                except Exception:
                    try:
                        img = Image.open(img_path)
                        text = pytesseract.image_to_string(img)
                        all_text += "\n" + text
                    except Exception:
                        pass
                finally:
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except OSError:
                            pass
    else:
        # Standard image file (JPG, PNG)
        if not HAS_OCR:
            return {
                "status": "no_ocr",
                "fields": {},
                "full_text": "",
                "raw_text": "",
                "review_required": True,
                "message": "OCR not available. Install tesseract-ocr and pytesseract.",
            }

        try:
            processed = _preprocess_image(file_path)
            text = pytesseract.image_to_string(
                processed,
                lang="eng+hin" if _has_hindi_pack() else "eng"
            )
            all_text = text
        except Exception:
            try:
                img = Image.open(file_path)
                all_text = pytesseract.image_to_string(img)
            except Exception as e:
                return {
                    "status": "error",
                    "fields": {},
                    "full_text": "",
                    "raw_text": "",
                    "review_required": True,
                    "message": str(e)
                }

    # Extract all structured and clinical fields
    parsed_fields = _parse_health_card_text(all_text)

    # Convert to structured fields dict for backward compatibility
    fields = {}
    for k, v in parsed_fields.items():
        fields[k] = {"value": v, "confidence": "high" if k in ("weight_kg", "height_cm", "muac_cm") else "medium"}

    # Mark anaemia flag
    hb = parsed_fields.get("hb_gdl")
    if hb is not None:
        fields["anaemia_flag"] = {
            "value": hb < 11.0,
            "confidence": "high",
            "note": "Hb < 11 g/dL = anaemia (WHO)",
        }

    raw_clean = all_text.strip()[:3500]

    # Return structured dict + flattened convenience properties for direct UI access
    response = {
        "status": "success",
        "fields": fields,
        "full_text": raw_clean,
        "raw_text": raw_clean if raw_clean else "—",
        "review_required": True,
        "field_count": len(parsed_fields),
        "child_name": parsed_fields.get("child_name"),
        "measurement_date": parsed_fields.get("measurement_date"),
        "weight_kg": parsed_fields.get("weight_kg"),
        "height_cm": parsed_fields.get("height_cm"),
        "age_months": parsed_fields.get("age_months"),
        "muac_cm": parsed_fields.get("muac_cm"),
        "head_circ_cm": parsed_fields.get("head_circ_cm"),
        "hb_gdl": parsed_fields.get("hb_gdl"),
        "sex": parsed_fields.get("sex"),
        "breastfed": parsed_fields.get("breastfed"),
        "appetite": parsed_fields.get("appetite"),
        "food_groups_yesterday": parsed_fields.get("food_groups_yesterday"),
        "meals_per_day": parsed_fields.get("meals_per_day"),
        "diarrhoea_2w": parsed_fields.get("diarrhoea_2w"),
        "fever_2w": parsed_fields.get("fever_2w"),
        "vaccination_status": parsed_fields.get("vaccination_status"),
        "mother_education": parsed_fields.get("mother_education"),
        "mother_age": parsed_fields.get("mother_age"),
        "wealth_score": parsed_fields.get("wealth_score"),
        "rural_urban": parsed_fields.get("rural_urban"),
        "bilateral_edema": parsed_fields.get("bilateral_edema"),
        "how_measured": parsed_fields.get("how_measured"),
        "food_preference": parsed_fields.get("food_preference"),
    }
    return response
