#!/bin/bash
# =============================================================
# Fuzzy Friend - Pet Health AI
# One-click startup script
# =============================================================

echo "🐾 Starting Fuzzy Friend - Pet Health AI..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is required but not installed."
    exit 1
fi

# Install backend dependencies if needed
echo "📦 Checking backend dependencies..."
cd "$SCRIPT_DIR/pet_triage"
if [ ! -f ".deps_installed" ]; then
    pip3 install -r requirements.txt -q
    touch .deps_installed
fi

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start backend server in background
echo ""
echo "🚀 Starting Backend Server (port 8000)..."
cd "$SCRIPT_DIR/pet_triage"
uvicorn api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend server
echo "🚀 Starting Frontend Server (port 3000)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "=============================================="
echo "✅ Fuzzy Friend is running!"
echo ""
echo "   🌐 Open in browser: http://localhost:3000"
echo "   📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "   Press Ctrl+C to stop all servers"
echo "=============================================="

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
