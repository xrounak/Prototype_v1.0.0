@echo off
echo ===================================================
echo Starting Electronic Warfare Simulation Backend...
echo ===================================================

cd /d "%~dp0\.."

if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    echo Installing backend dependencies...
    call .\.venv\Scripts\pip install -r backend\requirements.txt
)

echo Activating virtual environment and launching FastAPI gateway...
call .\.venv\Scripts\uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
