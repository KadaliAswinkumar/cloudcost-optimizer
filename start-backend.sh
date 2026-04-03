#!/bin/bash

# Start Backend Server

echo "🚀 Starting CloudCost Optimizer Backend..."

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
