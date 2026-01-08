@echo off
echo ========================================
echo PQ Analysis Engine - MVP Server
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Flask server...
echo Frontend URL: http://localhost:8501
echo API URL: http://localhost:8501/api/health
echo.

python server.py
