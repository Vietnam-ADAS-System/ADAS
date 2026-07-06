@echo off
REM ADAS Full Stack Start Script for Windows
REM Chạy: scripts\start-all.bat

echo ========================================
echo   ADAS FULL STACK - Starting...
echo ========================================
echo.

cd /d "%~dp0.."

REM Config
set HOST=127.0.0.1
set BACKEND_PORT=3000
set AI_PORT=8765
set FRONTEND_PORT=5173

echo [1/3] Starting Node.js Backend Server...
start "ADAS Node Server" cmd /c "cd backend\node-server && node server.js && pause"
timeout /t 2 /nobreak >nul

echo [2/3] Starting AI Backend (Python)...
start "ADAS AI Backend" cmd /c "cd backend\ai-service && call venv\Scripts\activate.bat 2>nul & python run_unified.py --webcam --fps 15 && pause"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend...
start "ADAS Frontend" cmd /c "cd frontend && npm run dev && pause"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   ADAS FULL STACK - RUNNING
echo ========================================
echo.
echo   Dashboard:    http://localhost:%FRONTEND_PORT%
echo   Node API:     http://%HOST%:%BACKEND_PORT%/api/health
echo   AI WebSocket: ws://%HOST%:%AI_PORT%
echo.
echo   Press any key to exit (this will NOT stop the servers)
pause >nul
