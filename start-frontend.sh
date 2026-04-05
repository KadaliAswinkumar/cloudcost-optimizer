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

# CloudCost UI uses port 8080; API on 8801 (no 5xxx ports).
# Override: VITE_UI_PORT / VITE_DEV_PROXY_TARGET in frontend/.env.local
echo "🌐 Frontend starting on http://127.0.0.1:8080 (API proxied to :8801)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev -- --host 127.0.0.1
