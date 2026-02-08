#!/bin/bash
# Quick script to check database status

echo "🔍 CHECKING DATABASE STATUS..."
echo ""

echo "======================================"
echo "1. SPOT PRICE HISTORY (from cron job)"
echo "======================================"
curl -s "https://cloudcost-api.onrender.com/api/v1/spot-intelligence/history?provider=gcp&instance_type=e2-micro&region=us-central1&days=7" | python3 -m json.tool | head -30
echo ""
echo ""

echo "======================================"
echo "2. CLOUD PRICING TABLE"
echo "======================================"
echo "Testing if Spot Intelligence can find pricing..."
curl -s -X POST "https://cloudcost-api.onrender.com/api/v1/spot-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"provider": "gcp", "instance_type": "e2-micro", "region": "us-central1"}' | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "3. INSTANCES API"
echo "======================================"
curl -s "https://cloudcost-api.onrender.com/api/v1/multicloud/instances?provider=gcp&limit=1" | python3 -m json.tool | head -30
