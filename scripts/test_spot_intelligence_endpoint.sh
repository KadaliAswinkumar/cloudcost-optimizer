#!/bin/bash

# Test script for Spot Intelligence API endpoint
# This verifies the /api/v1/spot-intelligence/analyze endpoint works

echo "🧪 Testing Spot Intelligence™ Endpoint"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Local test (if server is running locally)
echo "Test 1: Local endpoint (http://localhost:8000)"
echo "----------------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/v1/spot-intelligence/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "instance_type": "c5.xlarge",
    "hours_per_month": 730
  }' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ SUCCESS: Local endpoint working!${NC}"
    echo "Response preview:"
    echo "$BODY" | head -c 200
    echo "..."
else
    echo -e "${RED}❌ FAILED: HTTP $HTTP_CODE${NC}"
    if [ "$HTTP_CODE" == "000" ]; then
        echo -e "${YELLOW}⚠️  Server not running locally. Start with: uvicorn src.api.main:app${NC}"
    else
        echo "Error response: $BODY"
    fi
fi

echo ""
echo ""

# Test 2: Render production test
echo "Test 2: Render endpoint (https://cloudcost-api.onrender.com)"
echo "--------------------------------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://cloudcost-api.onrender.com/api/v1/spot-intelligence/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "instance_type": "m5.xlarge",
    "hours_per_month": 730
  }' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ SUCCESS: Render endpoint working!${NC}"
    echo "Response preview:"
    echo "$BODY" | head -c 200
    echo "..."
else
    echo -e "${RED}❌ FAILED: HTTP $HTTP_CODE${NC}"
    echo "Error response:"
    echo "$BODY" | head -c 300
    echo ""
    echo -e "${YELLOW}⚠️  If you see 404, deploy the latest code to Render!${NC}"
fi

echo ""
echo "========================================"
echo "Test complete!"
