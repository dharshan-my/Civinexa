@echo off
title CiviNexa AI - Civic Issue Reporting System
echo ============================================================
echo         Starting CiviNexa AI Civic Governance System
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [2/3] Verifying required libraries...
pip install -r requirements.txt

echo.
echo [3/3] Opening your browser to http://127.0.0.1:5000 ...
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000

echo.
echo ============================================================
echo   Application Running Live at: http://127.0.0.1:5000
echo   Admin Portal:   http://127.0.0.1:5000/admin/login
echo                   Username: admin  ^|  Password: admin123
echo   Citizen Portal: http://127.0.0.1:5000/login
echo                   Email: rahul.citizen@civinexa.org  ^|  Password: citizen123
echo.
echo   (Keep this window open while using the app. Press Ctrl+C to stop)
echo ============================================================
echo.

python app.py
pause
