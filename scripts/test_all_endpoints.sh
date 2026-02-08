#!/bin/bash

API_URL="https://cloudcost-api.onrender.com/api/v1"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    🧪 COMPREHENSIVE API TEST SUITE                            ║"
echo "║    Testing all endpoints after Spot Intelligence fixes        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Debug Endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  DEBUG ENDPOINT - Database Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: GET ${API_URL}/debug/database-status"
echo ""

RESPONSE=$(curl -k -s "${API_URL}/debug/database-status")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Check if it has spot pricing
SPOT_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('pricing', {}).get('spot', 0))" 2>/dev/null || echo "0")
echo ""
echo "📊 Spot prices in cloud_pricing table: $SPOT_COUNT"

if [ "$SPOT_COUNT" -gt "0" ]; then
    echo "✅ SPOT PRICING LOADED!"
else
    echo "❌ NO SPOT PRICING (fetch_real_spot_pricing.py may have failed)"
fi

echo ""
echo "Press Enter to continue..."
read

# Test 2: Spot Intelligence - Analyze
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  SPOT INTELLIGENCE - Analyze Instance"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: POST ${API_URL}/spot-intelligence/analyze"
echo "Instance: AWS t3.micro in us-east-1"
echo ""

ANALYZE_RESPONSE=$(curl -k -s -X POST "${API_URL}/spot-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "instance_type": "t3.micro", "region": "us-east-1"}')

echo "$ANALYZE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ANALYZE_RESPONSE"

# Check if it succeeded
if echo "$ANALYZE_RESPONSE" | grep -q '"success"'; then
    echo ""
    echo "✅ SPOT INTELLIGENCE WORKING!"
else
    echo ""
    echo "❌ SPOT INTELLIGENCE FAILED"
fi

echo ""
echo "Press Enter to continue..."
read

# Test 3: Spot History
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  SPOT INTELLIGENCE - Historical Data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: GET ${API_URL}/spot-intelligence/history"
echo "Instance: AWS c5.large in us-east-1 (7 days)"
echo ""

HISTORY_RESPONSE=$(curl -k -s "${API_URL}/spot-intelligence/history?provider=aws&instance_type=c5.large&region=us-east-1&days=7")

echo "$HISTORY_RESPONSE" | python3 -m json.tool 2>/dev/null | head -40
echo "... (truncated for readability)"

if echo "$HISTORY_RESPONSE" | grep -q '"data_points"'; then
    DATA_POINTS=$(echo "$HISTORY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data_points', 0))" 2>/dev/null || echo "0")
    echo ""
    echo "✅ Historical data found: $DATA_POINTS data points"
else
    echo ""
    echo "⚠️  No historical data yet (cron job may not have run)"
fi

echo ""
echo "Press Enter to continue..."
read

# Test 4: Instances API
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  INSTANCES API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: GET ${API_URL}/multicloud/instances?provider=aws&limit=2"
echo ""

curl -k -s "${API_URL}/multicloud/instances?provider=aws&limit=2" | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo "✅ Instances API working (should show hourly_price)"

echo ""
echo "Press Enter to continue..."
read

# Test 5: Quick Check
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  SPOT INTELLIGENCE - Quick Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: GET ${API_URL}/spot-intelligence/quick-check"
echo ""

curl -k -s "${API_URL}/spot-intelligence/quick-check?provider=aws&instance_type=m5.xlarge" | python3 -m json.tool 2>/dev/null

echo ""
echo ""

# Final Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    📊 TEST SUMMARY                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Expected Results:"
echo "  1. Debug endpoint should show spot pricing count > 0"
echo "  2. Spot Intelligence /analyze should return success: true"
echo "  3. Spot History should return historical price data"
echo "  4. Instances API should show hourly_price for instances"
echo "  5. Quick Check should return savings and risk data"
echo ""
echo "If Spot Intelligence is still failing, check Render logs for:"
echo "  - fetch_real_spot_pricing.py execution output"
echo "  - Any database errors during UPSERT"
echo "  - AWS credential warnings"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Tests complete! Review the output above.                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
