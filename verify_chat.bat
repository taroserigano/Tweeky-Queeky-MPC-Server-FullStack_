@echo off
echo ============================================
echo    CHAT SYSTEM VERIFICATION TEST
echo ============================================
echo.

echo [1] Testing Backend Health...
curl -s http://localhost:5000/api/health > nul
if %errorlevel% == 0 (
    echo    OK - Backend is running
) else (
    echo    FAIL - Backend not responding
)

echo.
echo [2] Testing Backend Chat...
curl -s -X POST http://localhost:5000/api/agent/chat -H "Content-Type: application/json" -d "{\"message\":\"test\"}" > response.txt
findstr /C:"message" response.txt > nul
if %errorlevel% == 0 (
    echo    OK - Chat API working
) else (
    echo    FAIL - Chat API not working
)

echo.
echo [3] Testing Frontend...
curl -s http://localhost:3000 > nul
if %errorlevel% == 0 (
    echo    OK - Frontend is running
) else (
    echo    FAIL - Frontend not responding  
)

echo.
echo [4] Testing Frontend Proxy to Chat...
curl -s -X POST http://localhost:3000/api/agent/chat -H "Content-Type: application/json" -d "{\"message\":\"test\"}" > proxy_response.txt
findstr /C:"message" proxy_response.txt > nul
if %errorlevel% == 0 (
    echo    OK - Proxy chat working
) else (
    echo    FAIL - Proxy not working
)

echo.
echo ============================================
echo.
echo Backend response:
type response.txt
echo.
echo ============================================
del response.txt 2>nul
del proxy_response.txt 2>nul
