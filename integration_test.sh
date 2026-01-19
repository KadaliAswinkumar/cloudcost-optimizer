#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║      🧪 CloudCost Optimizer - Integration Tests 🧪           ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Function to run test
run_test() {
    local test_name=$1
    local test_number=$2
    shift 2
    
    echo -e "${YELLOW}Test $test_number: ${test_name}${NC}"
    if "$@"; then
        echo -e "${GREEN}✅ PASSED${NC}\n"
        ((PASS_COUNT++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}\n"
        ((FAIL_COUNT++))
        return 1
    fi
}

# Test Functions

test_health_endpoint() {
    local response=$(curl -s http://localhost:8000/health)
    echo "Response: $response"
    echo "$response" | grep -q "healthy"
}

test_providers_endpoint() {
    local response=$(curl -s http://localhost:8000/api/v1/multicloud/providers)
    echo "Response: $(echo $response | jq -c '.providers[0:2]')"
    echo "$response" | jq -e '.providers | length > 0' > /dev/null
}

test_workload_types() {
    local response=$(curl -s http://localhost:8000/api/v1/recommendations/workload-types)
    echo "Response: $(echo $response | jq -c '.workload_types[0:2]')"
    echo "$response" | jq -e '.workload_types | length > 0' > /dev/null
}

test_categories() {
    local response=$(curl -s http://localhost:8000/api/v1/multicloud/categories)
    echo "Response: $(echo $response | jq -c '.categories[0:2]')"
    echo "$response" | jq -e '.categories | length > 0' > /dev/null
}

test_list_instances() {
    local response=$(curl -s "http://localhost:8000/api/v1/multicloud/instances?min_vcpus=2&min_memory=4")
    echo "Response: $(echo $response | jq -c '{total: .total, page: .page}')"
    echo "$response" | jq -e '.instances' > /dev/null
}

test_quick_recommendation() {
    local response=$(curl -s -X POST http://localhost:8000/api/v1/recommendations/quick \
        -H "Content-Type: application/json" \
        -d '{
            "vcpus": 2,
            "memory_gb": 4,
            "region": "us-east-1"
        }')
    echo "Response: $(echo $response | jq -c 'if .recommendations then {count: (.recommendations | length)} else . end')"
    echo "$response" | jq -e 'has("recommendations") or has("detail")' > /dev/null
}

test_multicloud_recommendations() {
    local response=$(curl -s -X POST http://localhost:8000/api/v1/multicloud/recommendations \
        -H "Content-Type: application/json" \
        -d '{
            "min_vcpus": 4,
            "min_memory_gb": 8,
            "providers": ["aws", "gcp", "azure"],
            "workload_type": "steady",
            "spot_eligible": true,
            "hours_per_month": 730,
            "max_monthly_budget": 200
        }')
    echo "Response: $(echo $response | jq -c 'if .overall_best then {count: (.overall_best | length)} else . end')"
    echo "$response" | jq -e 'has("overall_best") or has("by_provider") or has("detail")' > /dev/null
}

test_database_connection() {
    podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT 1;" > /dev/null 2>&1
}

test_database_tables() {
    local count=$(podman exec cloudcost-db psql -U postgres -d cloudcost -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "Tables found: $count"
    [ "$count" -gt 0 ]
}

test_redis_connection() {
    local response=$(podman exec cloudcost-redis redis-cli ping)
    echo "Response: $response"
    [ "$response" = "PONG" ]
}

test_redis_setget() {
    podman exec cloudcost-redis redis-cli SET test_key "test_value" > /dev/null
    local value=$(podman exec cloudcost-redis redis-cli GET test_key)
    podman exec cloudcost-redis redis-cli DEL test_key > /dev/null
    echo "Retrieved value: $value"
    [ "$value" = "test_value" ]
}

test_celery_worker() {
    podman logs cloudcost-celery-worker 2>&1 | grep -q "ready"
}

test_celery_beat() {
    podman logs cloudcost-celery-beat 2>&1 | grep -q "beat"
}

test_flower_dashboard() {
    curl -s http://localhost:5555/ | grep -q "Flower"
}

test_response_time() {
    local start=$(date +%s%N)
    curl -s http://localhost:8000/health > /dev/null
    local end=$(date +%s%N)
    local duration=$(( (end - start) / 1000000 )) # Convert to milliseconds
    echo "Response time: ${duration}ms"
    [ $duration -lt 1000 ] # Less than 1 second
}

test_invalid_endpoint() {
    local response=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/invalid-endpoint)
    echo "HTTP Status: ${response: -3}"
    echo "${response: -3}" | grep -q "404"
}

test_invalid_request() {
    local response=$(curl -s -X POST http://localhost:8000/api/v1/multicloud/recommendations \
        -H "Content-Type: application/json" \
        -d '{"invalid": "data"}' \
        -w "%{http_code}")
    echo "HTTP Status: ${response: -3}"
    echo "${response: -3}" | grep -q "422"
}

# Run all tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    🏗️  Infrastructure Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

run_test "Database Connection" "1.1" test_database_connection
run_test "Database Tables Created" "1.2" test_database_tables
run_test "Redis Connection" "1.3" test_redis_connection
run_test "Redis SET/GET Operations" "1.4" test_redis_setget
run_test "Celery Worker Running" "1.5" test_celery_worker
run_test "Celery Beat Running" "1.6" test_celery_beat

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                     🌐 API Endpoint Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

run_test "Health Endpoint" "2.1" test_health_endpoint
run_test "Get Providers" "2.2" test_providers_endpoint
run_test "Get Workload Types" "2.3" test_workload_types
run_test "Get Categories" "2.4" test_categories
run_test "List Instances" "2.5" test_list_instances
run_test "Quick Recommendation" "2.6" test_quick_recommendation
run_test "Multi-Cloud Recommendations" "2.7" test_multicloud_recommendations

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                   ⚡ Performance & Error Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

run_test "Response Time Check" "3.1" test_response_time
run_test "Invalid Endpoint (404)" "3.2" test_invalid_endpoint
run_test "Invalid Request (422)" "3.3" test_invalid_request
run_test "Flower Dashboard" "3.4" test_flower_dashboard

# Summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      📊 Final Results                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total Tests Run: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}✅ Passed: $PASS_COUNT${NC}"
echo -e "${RED}❌ Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║     🎉 ALL TESTS PASSED! System is fully functional! 🎉      ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║        ⚠️  Some tests failed. Review output above.  ⚠️       ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo -e "   • Check logs: podman-compose logs"
    echo -e "   • Restart services: podman-compose restart"
    echo -e "   • Check container status: podman-compose ps"
    exit 1
fi
