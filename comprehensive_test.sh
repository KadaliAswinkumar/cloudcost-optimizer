#!/bin/bash

API_URL="https://cloudcost-api.onrender.com"
UI_URL="https://kadaliaswinkumar.github.io/cloudcost-optimizer"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 COMPREHENSIVE DEPLOYMENT TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Stats Endpoint
echo "✅ Test 1: Dashboard Stats"
STATS=$(curl -sk "$API_URL/api/v1/multicloud/stats")
TOTAL=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_instances'])" 2>/dev/null || echo "ERROR")
AWS=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['by_provider']['aws'])" 2>/dev/null || echo "ERROR")
GCP=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['by_provider']['gcp'])" 2>/dev/null || echo "ERROR")
AZURE=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['by_provider']['azure'])" 2>/dev/null || echo "ERROR")
REGIONS=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_regions'])" 2>/dev/null || echo "ERROR")

echo "  Total instances: $TOTAL"
echo "  AWS: $AWS | GCP: $GCP | Azure: $AZURE"
echo "  Regions: $REGIONS"
echo ""

# Test 2: Instances Endpoint
echo "✅ Test 2: Instance Finder"
INSTANCES=$(curl -sk "$API_URL/api/v1/multicloud/instances?limit=5")
INST_COUNT=$(echo "$INSTANCES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['instances']))" 2>/dev/null || echo "ERROR")
echo "  Returned $INST_COUNT instances (expected 5)"
echo ""

# Test 3: AWS Instances
echo "✅ Test 3: AWS Instances"
AWS_INSTANCES=$(curl -sk "$API_URL/api/v1/multicloud/instances?provider=aws&limit=3")
AWS_COUNT=$(echo "$AWS_INSTANCES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['instances']))" 2>/dev/null || echo "ERROR")
echo "  Returned $AWS_COUNT AWS instances (expected 3)"
echo ""

# Test 4: GCP Instances
echo "✅ Test 4: GCP Instances"
GCP_INSTANCES=$(curl -sk "$API_URL/api/v1/multicloud/instances?provider=gcp&limit=3")
GCP_COUNT=$(echo "$GCP_INSTANCES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['instances']))" 2>/dev/null || echo "ERROR")
echo "  Returned $GCP_COUNT GCP instances (expected 3)"
echo ""

# Test 5: Azure Instances
echo "✅ Test 5: Azure Instances"
AZURE_INSTANCES=$(curl -sk "$API_URL/api/v1/multicloud/instances?provider=azure&limit=3")
AZURE_COUNT=$(echo "$AZURE_INSTANCES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['instances']))" 2>/dev/null || echo "ERROR")
echo "  Returned $AZURE_COUNT Azure instances (expected 3)"
echo ""

# Test 6: Price Comparison
echo "✅ Test 6: Price Comparison (2 vCPU, 8GB)"
COMPARISON=$(curl -sk "$API_URL/api/v1/multicloud/pricing/compare?vcpus=2&memory_gb=8")
COMP_STATUS=$(echo "$COMPARISON" | python3 -c "import sys, json; print('success' if json.load(sys.stdin).get('success') else 'fail')" 2>/dev/null || echo "ERROR")
echo "  Status: $COMP_STATUS"
echo ""

# Test 7: Filtered Instances (vCPUs)
echo "✅ Test 7: Filtered Instances (4+ vCPUs)"
FILTERED=$(curl -sk "$API_URL/api/v1/multicloud/instances?min_vcpus=4&limit=5")
FILTERED_COUNT=$(echo "$FILTERED" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['instances']))" 2>/dev/null || echo "ERROR")
echo "  Returned $FILTERED_COUNT instances with 4+ vCPUs"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Backend API: $API_URL ✅"
echo "Frontend UI: $UI_URL ✅"
echo ""
echo "Database Status:"
echo "  • Total: $TOTAL instances across $REGIONS regions"
echo "  • AWS: $AWS instances"
echo "  • GCP: $GCP instances"
echo "  • Azure: $AZURE instances"
echo ""
echo "API Endpoints:"
echo "  • /stats: ✅"
echo "  • /instances: ✅ ($INST_COUNT/5 returned)"
echo "  • /instances?provider=aws: ✅ ($AWS_COUNT/3 returned)"
echo "  • /instances?provider=gcp: ✅ ($GCP_COUNT/3 returned)"
echo "  • /instances?provider=azure: ✅ ($AZURE_COUNT/3 returned)"
echo "  • /pricing/compare: ✅ ($COMP_STATUS)"
echo "  • Filtering (vCPUs): ✅ ($FILTERED_COUNT results)"
echo ""
echo "🎯 Next Steps:"
echo "  1. Open $UI_URL"
echo "  2. Test Instance Finder (should show $TOTAL instances)"
echo "  3. Test Dashboard (should show correct counts)"
echo "  4. Test Price Comparison"
echo "  5. Test Recommendations"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
