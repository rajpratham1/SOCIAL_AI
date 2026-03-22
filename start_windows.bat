@echo off
echo ============================================
echo   SocialAI Backend — Windows Startup
echo ============================================

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install deps
echo Installing dependencies...
pip install -r requirements.txt -q

:: Set API key if provided as argument
if not "%1"=="" (
    set ANTHROPIC_API_KEY=%1
    echo Anthropic API key set.
)

:: Run
echo.
echo Starting server...
python app.py

pause
