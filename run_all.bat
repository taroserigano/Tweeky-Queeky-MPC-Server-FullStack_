@echo off
echo Starting all services...

start "MCP Server" cmd /k "cd services\mcp_server && python main.py"
echo MCP Server started on port 7001

timeout /t 2 /nobreak > nul

start "RAG Service" cmd /k "cd services\rag_service && python main.py"
echo RAG Service started on port 7002

timeout /t 2 /nobreak > nul

start "Agent Gateway" cmd /k "cd services\agent_gateway && python main.py"
echo Agent Gateway started on port 7000

echo.
echo ============================================
echo All services running!
echo ============================================
echo Agent Gateway:  http://localhost:7000
echo MCP Server:     http://localhost:7001
echo RAG Service:    http://localhost:7002
echo ============================================
echo.
echo Press any key to exit...
pause
