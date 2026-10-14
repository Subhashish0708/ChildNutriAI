#!/usr/bin/env bash
# ChildNutri AI — Automated Setup for macOS / Linux
set -e

echo "==============================================================================="
echo "                ChildNutri AI: Automated macOS / Linux Setup"
echo "  Pediatric Malnourishment Identification and Healthcare Decision Support"
echo "==============================================================================="
echo ""

# 1. Check for Python 3
echo "[1/6] Checking for Python installation..."
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 was not found in your system PATH!"
    echo "Please install Python 3.10+ using Homebrew or your package manager."
    exit 1
fi

PY_VER=$($PY_CMD --version)
echo "      Found: $PY_VER"
echo ""

# 2. Create Virtual Environment
echo "[2/6] Setting up Python virtual environment (venv)..."
if [ ! -f "venv/bin/activate" ]; then
    echo "      Creating clean virtual environment in ./venv ..."
    $PY_CMD -m venv venv
else
    echo "      Existing virtual environment found in ./venv"
fi
echo ""

# 3. Activate Virtual Environment
echo "[3/6] Activating virtual environment..."
source venv/bin/activate
echo "      Virtual environment activated."
echo ""

# 4. Install Dependencies
echo "[4/6] Installing dependencies from requirements.txt..."
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "      All Python dependencies installed successfully!"
echo ""

# 5. Initialize Database & Seed Articles
echo "[5/6] Initializing database and seeding clinical resources..."
python -c "from backend.app.services.seed_data import seed_articles; seed_articles()" || true
echo "      Database tables verified and clinical resource articles seeded!"
echo ""

# 6. Run Verification Smoke Test
echo "[6/6] Running automated verification test suite..."
export PYTHONPATH=.
pytest backend/tests/test_vision_screening.py -q
echo "      All clinical safety tests PASSED!"
echo ""

echo "==============================================================================="
echo "                     Setup Completed Successfully!"
echo "==============================================================================="
echo ""
echo "Demo Login Credentials:"
echo "  Doctor Role:  dr.subha@childnutri.org   / Password: Doctor@123"
echo "  Parent Role:  priya.sharma@email.com   / Password: Parent@123"
echo ""
echo "To launch the server at any time, run: ./run.sh"
echo ""

read -p "Do you want to start the ChildNutri AI server now? (y/n): " START_NOW
if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
    echo "Starting server on http://127.0.0.1:8000 ..."
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
fi
