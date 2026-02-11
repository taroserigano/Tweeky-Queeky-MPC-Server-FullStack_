@echo off
echo ========================================
echo Starting TweekySqueeky E-Commerce App
echo ========================================
echo.

REM Kill any existing processes on ports 5000 and 3000
echo Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
timeout /t 2 /nobreak >nul

REM Start Backend API
echo.
echo [1/2] Starting Backend API on port 5000...
start "Backend API" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --reload --port 5000"
timeout /t 3 /nobreak >nul

REM Start Frontend (suppress React auto-open, we open browser once below)
echo [2/2] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd /d %~dp0frontend && set BROWSER=none && npm start"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Services Starting!
echo ========================================
echo Backend API:  http://localhost:5000
echo API Docs:     http://localhost:5000/docs
echo Frontend:     http://localhost:3000
echo ========================================
echo.
echo Wait 10-15 seconds for services to fully start...
echo Then open: http://localhost:3000
echo.
echo Press any key to exit (this will NOT stop the servers)
pause >nul
