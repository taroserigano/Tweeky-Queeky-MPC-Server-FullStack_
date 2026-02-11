#!/bin/bash

echo "========================================"
echo "Starting 3-Service Architecture"
echo "========================================"

# Kill any existing services
echo "Stopping existing services..."
taskkill //F //IM python.exe //FI "WINDOWTITLE eq MCP*" 2>/dev/null
taskkill //F //IM python.exe //FI "WINDOWTITLE eq RAG*" 2>/dev/null
taskkill //F //IM python.exe //FI "WINDOWTITLE eq Agent*" 2>/dev/null

sleep 2

# Start MCP Server
echo "[1/3] Starting MCP Server (Port 7001)..."
cd services/mcp_server
python main.py &
MCP_PID=$!
cd ../..
sleep 3

# Start RAG Service
echo "[2/3] Starting RAG Service (Port 7002)..."
cd services/rag_service
python main.py &
RAG_PID=$!
cd ../..
sleep 3

# Start Agent Gateway
echo "[3/3] Starting Agent Gateway (Port 5001)..."
cd services/agent_gateway
python main.py &
AGENT_PID=$!
cd ../..
sleep 3

echo ""
echo "========================================"
echo "All services started!"
echo "MCP Server:     http://localhost:7001  (PID: $MCP_PID)"
echo "RAG Service:    http://localhost:7002  (PID: $RAG_PID)"
echo "Agent Gateway:  http://localhost:5001  (PID: $AGENT_PID)"
echo "========================================"
echo ""
echo "Services are running in background."
echo "To stop them: kill $MCP_PID $RAG_PID $AGENT_PID"
echo ""
echo "Testing in 5 seconds..."
sleep 5

python quick_test.py
