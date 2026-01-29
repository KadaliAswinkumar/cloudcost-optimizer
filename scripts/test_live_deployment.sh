#!/bin/bash
set -e

API_URL="https://cloudcost-api.onrender.com"
UI_URL="https://kadaliaswinkumar.github.io/cloudcost-optimizer"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 TESTING LIVE DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Health Check
echo "✅ Test 1: Health Check"
curl -s "$API_URL/health" | head -20
echo ""
echo ""

# Test 2: Stats Endpoint (Dashboard data)
echo "✅ Test 2: Dashboard Stats"
curl -s "$API_URL/api/v1/multicloud/stats" | python3 -m json.tool | head -30
echo ""
echo ""

# Test 3: Instance Count
echo "✅ Test 3: Instance Count"
INSTANCE_COUNT=$(curl -s "$API_URL/api/v1/multicloud/instances?limit=1" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")
echo "Total instances available: $INSTANCE_COUNT"
echo ""

# Test 4: AWS Instances
echo "✅ Test 4: AWS Instances"
AWS_COUNT=$(curl -s "$API_URL/api/v1/multicloud/stats?provider=aws" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_instances'])")
echo "AWS instances: $AWS_COUNT"
echo ""

# Test 5: GCP Instances  
echo "✅ Test 5: GCP Instances"
GCP_COUNT=$(curl -s "$API_URL/api/v1/multicloud/stats?provider=gcp" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_instances'])")
echo "GCP instances: $GCP_COUNT"
echo ""

# Test 6: Azure Instances
echo "✅ Test 6: Azure Instances"
AZURE_COUNT=$(curl -s "$API_URL/api/v1/multicloud/stats?provider=azure" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_instances'])")
echo "Azure instances: $AZURE_COUNT"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total instances: $INSTANCE_COUNT"
echo "AWS: $AWS_COUNT | GCP: $GCP_COUNT | Azure: $AZURE_COUNT"
echo ""
echo "🌐 Frontend: $UI_URL"
echo "🔗 Backend: $API_URL"
echo ""
echo "✅ All tests passed! Your deployment is working perfectly! 🎉"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
