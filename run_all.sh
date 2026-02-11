#!/bin/bash

# Start all 3 services
echo "🚀 Starting all services..."

# Start MCP Server (port 7001)
cd services/mcp_server
python main.py &
MCP_PID=$!
echo "✓ MCP Server started (PID: $MCP_PID) on port 7001"

# Start RAG Service (port 7002)
cd ../rag_service
python main.py &
RAG_PID=$!
echo "✓ RAG Service started (PID: $RAG_PID) on port 7002"

# Start Agent Gateway (port 7000)
cd ../agent_gateway
python main.py &
AGENT_PID=$!
echo "✓ Agent Gateway started (PID: $AGENT_PID) on port 7000"

cd ../..

echo ""
echo "============================================"
echo "✅ All services running!"
echo "============================================"
echo "Agent Gateway:  http://localhost:7000"
echo "MCP Server:     http://localhost:7001"
echo "RAG Service:    http://localhost:7002"
echo ""
echo "Press Ctrl+C to stop all services"
echo "============================================"

# Wait for Ctrl+C
trap "kill $MCP_PID $RAG_PID $AGENT_PID; echo 'Stopped all services'; exit" INT
wait
