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

# Start the dev server
echo "🌐 Frontend starting on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev
