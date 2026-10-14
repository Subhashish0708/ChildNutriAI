@echo off
title ChildNutri AI Server (Windows)

echo ===============================================================================
echo                      Launching ChildNutri AI Server
echo ===============================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'venv' was not found!
    echo Please run setup.bat first to install all requirements.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Opening browser at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000

echo Starting FastAPI server with Uvicorn (Press Ctrl+C to stop)...
set PYTHONPATH=.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
