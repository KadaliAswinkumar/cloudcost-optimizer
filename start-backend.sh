#!/bin/bash

# Start Backend Server (FastAPI on port 8000)

echo "🚀 Starting CloudCost Optimizer Backend..."

# Free stale processes on 8001 (old runs / other experiments) so nothing confusing is left
if lsof -ti:8001 >/dev/null 2>&1; then
  echo "🧹 Stopping process on port 8001 (previous run / stray listener)..."
  lsof -ti:8001 | xargs kill -9 2>/dev/null || true
fi

# Activate virtual environment
source venv/bin/activate

# Set environment to development
export ENVIRONMENT=development
export DEBUG=true

# Start the backend
echo "📡 Backend starting on http://localhost:8000"
echo "📖 API docs at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
