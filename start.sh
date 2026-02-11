#!/bin/bash

echo "========================================"
echo "Starting TweekySqueeky E-Commerce App"
echo "========================================"
echo ""

# Kill any existing processes on ports 5000 and 3000
echo "Cleaning up ports..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 2

# Get the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start Backend API
echo ""
echo "[1/2] Starting Backend API on port 5000..."
cd "$DIR"
python -m uvicorn main:app --reload --port 5000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Start Frontend
echo "[2/2] Starting Frontend on port 3000..."
cd "$DIR/frontend"
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
sleep 3

echo ""
echo "========================================"
echo "Services Started!"
echo "========================================"
echo "Backend API:  http://localhost:5000"
echo "API Docs:     http://localhost:5000/docs"
echo "Frontend:     http://localhost:3000"
echo "========================================"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  backend.log"
echo "  Frontend: frontend.log"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Opening browser in 10 seconds..."
sleep 10

# Try to open browser
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
else
    echo "Please open http://localhost:3000 in your browser"
fi
