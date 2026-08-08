@echo off
echo ========================================
echo GeoTutor Brain API Startup
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Brain dependencies...
pip install -q -r requirements.txt

echo Installing parent dependencies (LanGraph, etc.)...
pip install -q -r ../requirements.txt

echo.
echo ========================================
echo Starting Brain API on port 8000...
echo ========================================
echo.

python main.py

pause
