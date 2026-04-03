#!/bin/bash
# Complete Diagnostic Script for Fly.io Backend

echo "======================================"
echo "  BACKEND DIAGNOSTIC REPORT"
echo "======================================"
echo ""

echo "1️⃣  Checking app status..."
flyctl status --app cloudcost-optimizer-api-aswin
echo ""

echo "2️⃣  Checking secrets configuration..."
flyctl secrets list --app cloudcost-optimizer-api-aswin
echo ""

echo "3️⃣  Viewing last 50 log lines (CRITICAL - shows the error)..."
echo "---"
flyctl logs --app cloudcost-optimizer-api-aswin | tail -50
echo "---"
echo ""

echo "4️⃣  Attempting to test health endpoint..."
curl -v https://cloudcost-optimizer-api-aswin.fly.dev/health 2>&1 | grep -E "HTTP|Connected|status"
echo ""

echo "======================================"
echo "  DIAGNOSIS COMPLETE"
echo "======================================"
echo ""
echo "📋 Next step: Look at the logs above (section 3)"
echo "   Find the ERROR or exception that shows why the app crashed"
