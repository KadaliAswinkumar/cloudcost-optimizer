#!/bin/bash

# Start Frontend Development Server

echo "🚀 Starting CloudCost Optimizer Frontend..."

# Navigate to frontend directory
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# CloudCost UI uses port 5174 by default (5173 is often taken by other Vite apps).
# Override: VITE_UI_PORT in frontend/.env.local
echo "🌐 Frontend starting on http://127.0.0.1:5174 (API proxied to :8000)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev -- --host 127.0.0.1
