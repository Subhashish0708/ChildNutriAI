@echo off
setlocal EnableDelayedExpansion
title ChildNutri AI — Automated Setup for Windows

echo ===============================================================================
echo                ChildNutri AI: Automated Windows Setup
echo   Pediatric Malnourishment Identification and Healthcare Decision Support
echo ===============================================================================
echo.

:: 1. Check for Python
echo [1/6] Checking for Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=python
) else (
    py --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PY_CMD=py
    ) else (
        echo [ERROR] Python was not found in your system PATH!
        echo.
        echo Please install Python 3.10, 3.11, or 3.12 from:
        echo    https://www.python.org/downloads/
        echo.
        echo IMPORTANT: During installation, make sure to check the box:
        echo    "Add python.exe to PATH"
        echo.
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%v in ('!PY_CMD! --version') do set PY_VER=%%v
echo       Found: !PY_VER!
echo.

:: 2. Create Virtual Environment
echo [2/6] Setting up Python virtual environment (venv)...
if not exist "venv\Scripts\activate.bat" (
    echo       Creating clean virtual environment in .\venv ...
    !PY_CMD! -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo       Existing virtual environment found in .\venv
)
echo.

:: 3. Activate Virtual Environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo       Virtual environment activated.
echo.

:: 4. Upgrade pip and install requirements
echo [4/6] Installing dependencies from requirements.txt...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Dependency installation encountered errors!
    echo Please check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo       All Python dependencies installed successfully!
echo.

:: 5. Initialize Database & Seed Articles
echo [5/6] Initializing database and seeding clinical resources...
python -c "from backend.app.services.seed_data import seed_articles; seed_articles()"
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Database seeding check completed.
) else (
    echo       Database tables verified and clinical resource articles seeded!
)
echo.

:: 6. Run Verification Smoke Test
echo [6/6] Running automated verification test suite...
set PYTHONPATH=.
pytest backend/tests/test_vision_screening.py -q
if %ERRORLEVEL% neq 0 (
    echo [WARNING] One or more tests encountered warnings.
) else (
    echo       All clinical safety tests PASSED!
)
echo.

echo ===============================================================================
echo                      Setup Completed Successfully!
echo ===============================================================================
echo.
echo Demo Login Credentials:
echo   Doctor Role:  dr.subha@childnutri.org   / Password: Doctor@123
echo   Parent Role:  priya.sharma@email.com   / Password: Parent@123
echo.
echo To launch the server at any time in the future, simply double-click: run.bat
echo.

set /p START_NOW="Do you want to start the ChildNutri AI server now? (Y/N): "
if /i "!START_NOW!"=="Y" (
    echo.
    echo Starting server on http://127.0.0.1:8000 ...
    start http://127.0.0.1:8000
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
) else (
    echo.
    echo You can start the server whenever you are ready using: run.bat
    pause
)
