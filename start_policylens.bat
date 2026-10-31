@echo off
title PolicyLens Prototype Starter
echo =====================================================================
echo              PolicyLens - Local Prototype Launcher
echo    Intelligent Insurance Policy Understanding & Risk Navigator
echo =====================================================================
echo.

set BASE_DIR=%~dp0
cd /d "%BASE_DIR%"

echo [1/3] Checking Backend Python Environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo Virtual environment not found in backend\venv!
    echo Creating virtual environment...
    py -m venv backend\venv
    call backend\venv\Scripts\activate.bat
    python -m pip install -r backend\requirements.txt
) else (
    echo Backend virtual environment detected.
)

echo.
echo [2/3] Starting Backend API Server (FastAPI on http://127.0.0.1:8001)...
start "PolicyLens Backend Server" cmd /k "cd /d %BASE_DIR%backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

echo Waiting for backend server to initialize...
timeout /t 3 /nobreak > nul

echo.
echo [3/3] Starting Frontend Dev Server (Vite on http://localhost:5173)...
start "PolicyLens Frontend Server" cmd /k "cd /d %BASE_DIR%frontend && npm run dev"

echo.
echo =====================================================================
echo PolicyLens is launching!
echo Access the application at: http://localhost:5173
echo Backend API Docs at:       http://127.0.0.1:8001/docs
echo.
echo For evaluation, click 'Instant Demo Login' on the login screen.
echo =====================================================================
timeout /t 4 /nobreak > nul
start http://localhost:5173
