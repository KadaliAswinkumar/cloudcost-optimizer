#!/bin/bash
# Quick API Tests for CloudCost Optimizer

echo "================================"
echo "CloudCost Optimizer API Tests"
echo "================================"
echo ""

# Test 1: Health Check
echo "1. Testing Health Endpoint..."
curl -s https://cloudcost-api.onrender.com/health | python3 -m json.tool
echo ""
echo ""

# Test 2: Instances Count
echo "2. Testing Instances API (checking total count)..."
curl -s "https://cloudcost-api.onrender.com/api/v1/multicloud/instances?provider=aws&limit=1" | \
  python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Total AWS Instances: {data[\"total\"]}'); print(f'Sample: {data[\"instances\"][0][\"instance_type\"]} - ${data[\"instances\"][0][\"hourly_price\"]}/hr')"
echo ""
echo ""

# Test 3: Spot Intelligence (Expected to fail for now)
echo "3. Testing Spot Intelligence API..."
curl -s -X POST https://cloudcost-api.onrender.com/api/v1/spot-intelligence/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "instance_type": "t2.nano", "region": "us-east-1"}' | \
  python3 -m json.tool
echo ""
echo ""

echo "================================"
echo "Test Results Summary:"
echo "================================"
echo "✅ If health check passed → API is running"
echo "✅ If instances count > 1000 → Data is loaded"
echo "❌ If Spot Intelligence fails → Expected (needs fix)"
echo ""
