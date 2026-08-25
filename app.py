"""
=============================================================================
ChildNutri AI - Application Server Launcher (app.py)
=============================================================================
Single-command launcher for running the complete ChildNutri AI platform:
  • Web Interface (Landing, Parent Dashboard, Health Worker Dashboard)
  • FastAPI RESTful Backend & Database Engine
  • Multi-Modal AI Suite (Soft-Voting Ensemble, EfficientNet-B0, 1285-D Fusion)
  • Interactive API Documentation (Swagger & Redoc)

Usage:
  python app.py
  python app.py --port 8080 --reload
  python app.py --open
=============================================================================
"""

import os
import sys
import argparse
import webbrowser
import threading
import time
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.database import engine, Base
from backend.main import app

def print_banner(host: str, port: int):
    url = f"http://{host}:{port}" if host != "0.0.0.0" else f"http://127.0.0.1:{port}"
    local_url = f"http://localhost:{port}"
    
    print("\n" + "=" * 70)
    print("   🍼  CHILDNUTRI AI - PEDIATRIC MALNUTRITION SCREENING PLATFORM")
    print("   🤖  Multi-Modal AI System (XGBoost + LightGBM + RF + EfficientNet-B0)")
    print("=" * 70)
    print(f"  [+] Web Dashboard URL:       {local_url}")
    print(f"  [+] Network Address:         {url}")
    print(f"  [+] Interactive Swagger API: {local_url}/docs")
    print(f"  [+] ReDoc Documentation:     {local_url}/redoc")
    print("-" * 70)
    print("  [DEMO ACCOUNTS]")
    print("   • Parent Account:        kalpak@gmail.com / Kalpak@123")
    print("   • Health Worker Account: priya.sharma@email.com / Priya@123")
    print("-" * 70)
    print("  [ACTIVE AI & CLINICAL ENGINES]")
    print("   * 1285-D Multimodal Fusion Network & Modality Gating")
    print("   * Soft-Voting Ensemble (XGBoost 40% + LightGBM 35% + Random Forest 25%)")
    print("   * EfficientNet-B0 Deep CNN Visual Screener & Grad-CAM")
    print("   * SHAP (SHapley Additive Explanations) Feature Attribution")
    print("   * WHO LMS Z-Score Engine (Exact HAZ, WAZ, WHZ, BAZ)")
    print("   * Longitudinal Growth-Velocity Early-Warning Deterioration Engine")
    print("   * IMCI / CMAM Deterministic Safety Triage")
    print("=" * 70)
    print("  Press Ctrl+C to stop the server.\n")


def open_browser_delayed(url: str, delay_seconds: float = 1.2):
    time.sleep(delay_seconds)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Run ChildNutri AI Web & API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reloading on file change")
    parser.add_argument("--open", action="store_true", help="Automatically open web browser on startup")
    parser.add_argument("--public", action="store_true", help="Bind to 0.0.0.0 for LAN access")

    args = parser.parse_args()

    host = "0.0.0.0" if args.public else args.host
    port = args.port

    # 1. Initialize Database Schema
    Base.metadata.create_all(bind=engine)

    # 2. Ensure Directories
    os.makedirs(os.path.join(BASE_DIR, "uploads", "children"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "uploads", "ai"), exist_ok=True)

    # 3. Print Startup Banner
    print_banner(host, port)

    # 4. Optional Browser Auto-Launch
    if args.open:
        target_url = f"http://localhost:{port}"
        threading.Thread(target=open_browser_delayed, args=(target_url,), daemon=True).start()

    # 5. Start Uvicorn Server
    if args.reload:
        uvicorn.run("backend.main:app", host=host, port=port, reload=True)
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
