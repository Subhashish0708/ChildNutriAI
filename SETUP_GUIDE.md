# ChildNutri AI — Universal Setup & Deployment Guide

> **Step-by-step instructions for setting up, installing dependencies, and running ChildNutri AI across Windows, macOS, and Linux.**

---

## 📋 Table of Contents
1. [System Prerequisites](#1-system-prerequisites)
2. [Quick Setup for Windows (1-Click)](#2-quick-setup-for-windows-1-click)
3. [Manual Setup for Windows (PowerShell / Command Prompt)](#3-manual-setup-for-windows-powershell--command-prompt)
4. [Quick Setup for macOS and Linux](#4-quick-setup-for-macos-and-linux)
5. [Tesseract OCR Setup (Optional for Health Card Scans)](#5-tesseract-ocr-setup-optional-for-health-card-scans)
6. [Demo Accounts & User Roles](#6-demo-accounts--user-roles)
7. [Running the Automated Verification Test Suite](#7-running-the-automated-verification-test-suite)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. System Prerequisites

Before beginning, ensure the computer has:
* **Operating System:** Windows 10/11, macOS 12+, or Ubuntu 20.04+ (or any modern Linux distro).
* **Python Version:** **Python 3.10, 3.11, or 3.12** installed.
  * Download from: [https://www.python.org/downloads/](https://www.python.org/downloads/)
  * ⚠️ **CRITICAL ON WINDOWS:** On the very first screen of the Python installer, make sure to check the box:
    > ☑ **"Add python.exe to PATH"** (or "Add Python to environment variables").

---

## 2. Quick Setup for Windows (1-Click)

We have provided automated batch scripts for Windows:

### Initial Setup:
1. Open the project folder `childnutri/` in Windows File Explorer.
2. Double-click **`setup.bat`**.
3. The script will automatically:
   * Verify your Python installation.
   * Create an isolated virtual environment (`venv`).
   * Upgrade `pip` and install all required libraries from `requirements.txt`.
   * Initialize database tables and seed verified clinical guides.
   * Run the automated clinical safety test suite.
   * Prompt you to launch the server immediately.

### Daily Launching:
After the initial setup is complete, you never need to re-run setup. Simply double-click:
* **`run.bat`**  
This activates the virtual environment, launches the FastAPI server at `http://127.0.0.1:8000`, and opens your default browser automatically.

---

## 3. Manual Setup for Windows (PowerShell / Command Prompt)

If you prefer using the command line on Windows:

### Step 1: Open PowerShell or Command Prompt
Navigate to the project root directory:
```powershell
cd C:\path\to\Child_nutri_AI\childnutri
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Using standard Python launcher
python -m venv venv

# Activate in PowerShell:
.\venv\Scripts\Activate.ps1
# (Or in Command Prompt cmd.exe):
venv\Scripts\activate.bat
```

> *Tip for PowerShell:* If you get an error saying `running scripts is disabled on this system`, run this once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 3: Install Required Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Seed Initial Clinical Knowledge Base
```powershell
python -c "from backend.app.services.seed_data import seed_articles; seed_articles()"
```

### Step 5: Start the Full-Stack Server
```powershell
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Now open your browser and go to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

---

## 4. Quick Setup for macOS and Linux

### Automated 1-Click Setup:
```bash
cd /path/to/Child_nutri_AI/childnutri
./setup.sh
```

### Daily Launch:
```bash
./run.sh
```

### Manual Commands:
```bash
cd /path/to/Child_nutri_AI/childnutri
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -c "from backend.app.services.seed_data import seed_articles; seed_articles()"
PYTHONPATH=. python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 5. Tesseract OCR Setup (Optional for Health Card Scans)

ChildNutri AI uses `pdfplumber` for vector clinic PDF summaries (which works out of the box with zero external tools).  
If you also wish to scan **raster photograph images of paper health cards**, install Tesseract OCR:

### On Windows:
1. Download the official Windows installer from UB-Mannheim:
   * [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. Add `C:\Program Files\Tesseract-OCR` to your Windows System `PATH`.

### On macOS:
```bash
brew install tesseract
```

### On Ubuntu/Debian Linux:
```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

---

## 6. Demo Accounts & User Roles

ChildNutri AI protects all clinical tools (Dashboard, Assessment Wizard, Photo AI Screening, OCR Document Scanner, and Resources Library). **Users must be logged in to access these features.**

Pre-seeded demo credentials ready for immediate use:

| Role | Email Address | Password | Permissions & Views |
| :--- | :--- | :--- | :--- |
| **Doctor / Clinician** | `dr.subha@childnutri.org` | `Doctor@123` | Full clinical z-score statistics (WAZ, HAZ, WHZ), NRC hospital emergency protocols, PDF report exports, patient management. |
| **Parent / Caregiver** | `priya.sharma@email.com` | `Parent@123` | Plain-language visual health cards, home-cooked food recommendations, Anganwadi appointment alerts. |

You can also click **"Create free account"** on the login page to register a new account anytime.

---

## 7. Running the Automated Verification Test Suite

ChildNutri AI includes 18 automated unit and clinical safety tests covering image suitability, clothing obstruction, supported pediatric age bounds, and WHO LMS classification.

### Run tests on Windows:
```powershell
# With venv activated:
$env:PYTHONPATH="."
pytest backend/tests/test_vision_screening.py backend/tests/test_core_flow.py -v
```

### Run tests on macOS / Linux:
```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests/test_vision_screening.py backend/tests/test_core_flow.py -v
```
All 18 tests will execute in approximately 3 to 5 seconds with a 100% pass rate.

---

## 8. Troubleshooting & FAQs

### Q1: "python is not recognized as an internal or external command" on Windows
* **Solution:** Python was installed without checking "Add python.exe to PATH". Re-run the Python installer, choose "Modify", and check the "Add to PATH" option.

### Q2: "Port 8000 is already in use"
* **Solution:** Another program or previous instance is using port 8000. Start the server on port 8001:
  ```bash
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
  ```
  Then access `http://127.0.0.1:8001`.

### Q3: "Cannot load Photo AI / redirects to login"
* **Reason:** By design, all diagnostic and screening features require an authenticated session to protect patient privacy. Log in using `dr.subha@childnutri.org` / `Doctor@123` or create an account.
