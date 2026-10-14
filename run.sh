#!/usr/bin/env bash
# ChildNutri AI Server Launcher for macOS / Linux
set -e

if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment 'venv' was not found!"
    echo "Please run ./setup.sh first."
    exit 1
fi

source venv/bin/activate
export PYTHONPATH=.

echo "==============================================================================="
echo "Starting ChildNutri AI on http://127.0.0.1:8000 (Press Ctrl+C to stop)..."
echo "==============================================================================="

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
