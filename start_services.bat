@echo off
echo ===============================================
echo Starting 3-Service Architecture
echo ===============================================
echo.

echo [1/3] Starting MCP Server (Port 7001)...
start "MCP Server" cmd /k "cd services\mcp_server && python main.py"
timeout /t 3 /nobreak > nul

echo [2/3] Starting RAG Service (Port 7002)...
start "RAG Service" cmd /k "cd services\rag_service && python main.py"
timeout /t 3 /nobreak > nul

echo [3/3] Starting Agent Gateway (Port 5001)...
start "Agent Gateway" cmd /k "cd services\agent_gateway && python main.py"
timeout /t 3 /nobreak > nul

echo.
echo ===============================================
echo All services started!
echo MCP Server:     http://localhost:7001
echo RAG Service:    http://localhost:7002  
echo Agent Gateway:  http://localhost:5001
echo ===============================================
echo.
echo Press any key to run tests...
pause > nul

python test_full_system.py

echo.
echo Press any key to exit...
pause > nul
