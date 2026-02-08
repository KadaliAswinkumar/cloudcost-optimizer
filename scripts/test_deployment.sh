#!/bin/bash

echo "======================================"
echo "🔍 TESTING CLOUDCOST API DEPLOYMENT"
echo "======================================"
echo ""

API_URL="https://cloudcost-api.onrender.com/api/v1"

# Test 1: Health Check
echo "1️⃣ HEALTH CHECK"
echo "----------------------------------------"
curl -k -s "${API_URL}/../health" | python3 -m json.tool 2>&1 || echo "Health endpoint failed"
echo ""
echo ""

# Test 2: Instances API (with pricing)
echo "2️⃣ INSTANCES API (should show pricing)"
echo "----------------------------------------"
curl -k -s "${API_URL}/multicloud/instances?provider=aws&limit=1" | python3 -m json.tool 2>&1 | head -30
echo ""
echo ""

# Test 3: Spot Intelligence (THE BROKEN ONE)
echo "3️⃣ SPOT INTELLIGENCE API (currently broken)"
echo "----------------------------------------"
curl -k -s -X POST "${API_URL}/spot-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "instance_type": "c5.large", "region": "us-east-1"}' | python3 -m json.tool 2>&1
echo ""
echo ""

# Test 4: Spot History (from cron job - should work)
echo "4️⃣ SPOT HISTORY API (from cron job)"
echo "----------------------------------------"
curl -k -s "${API_URL}/spot-intelligence/history?provider=aws&instance_type=c5.large&region=us-east-1&days=7" | python3 -m json.tool 2>&1 | head -30
echo ""
echo ""

# Test 5: Recommendations (should show pricing)
echo "5️⃣ RECOMMENDATIONS API"
echo "----------------------------------------"
curl -k -s -X POST "${API_URL}/multicloud/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"vcpu_min": 2, "vcpu_max": 4, "memory_gb_min": 8, "memory_gb_max": 16}' | python3 -m json.tool 2>&1 | head -50
echo ""
echo ""

echo "======================================"
echo "📊 SUMMARY"
echo "======================================"
echo "✅ = Working"
echo "❌ = Broken"
echo ""
echo "Expected Status:"
echo "  - Health: ✅"
echo "  - Instances: ✅ (should show hourly_price)"
echo "  - Spot Intelligence: ❌ (No spot pricing available)"
echo "  - Spot History: ✅ (cron job working)"
echo "  - Recommendations: ✅"
echo ""
echo "ROOT CAUSE: cloud_pricing table not populated with spot prices"
echo "SOLUTION: fetch_real_spot_pricing.py needs debugging"
echo "======================================"
