#!/bin/bash

# Start Backend Server (FastAPI on port 8801 — UI uses 8080)

echo "🚀 Starting CloudCost Optimizer Backend..."

# Free stale listener on 8801 so restarts are clean
if lsof -ti:8801 >/dev/null 2>&1; then
  echo "🧹 Stopping process on port 8801 (previous run)..."
  lsof -ti:8801 | xargs kill -9 2>/dev/null || true
fi

# Activate virtual environment
source venv/bin/activate

# Set environment to development
export ENVIRONMENT=development
export DEBUG=true

# Start the backend
echo "📡 Backend starting on http://localhost:8801"
echo "📖 API docs at http://localhost:8801/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn src.api.main:app --host 0.0.0.0 --port 8801 --reload
