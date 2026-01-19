#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║        🚀 CloudCost Optimizer - Quick Test Suite 🚀          ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    local expected=$3
    
    echo -ne "${YELLOW}Testing: ${test_name}...${NC} "
    
    if eval "$test_command" | grep -q "$expected" 2>/dev/null; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASS_COUNT++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((FAIL_COUNT++))
        return 1
    fi
}

echo -e "${BLUE}1️⃣ Infrastructure Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "All containers running" "podman-compose ps" "Up"
echo ""

echo -e "${BLUE}2️⃣ API Health Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "API health endpoint" "curl -s http://localhost:8000/health" "healthy"
run_test "Swagger UI accessible" "curl -s http://localhost:8000/docs" "swagger"
echo ""

echo -e "${BLUE}3️⃣ Database Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Database connection" "podman exec cloudcost-db pg_isready -U postgres" "accepting connections"
run_test "Database query" "podman exec cloudcost-db psql -U postgres -d cloudcost -c 'SELECT 1;'" "1"
echo ""

echo -e "${BLUE}4️⃣ Redis Cache Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Redis PING" "podman exec cloudcost-redis redis-cli ping" "PONG"
echo ""

echo -e "${BLUE}5️⃣ Celery Worker Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Celery worker status" "podman logs cloudcost-celery-worker" "ready"
run_test "Celery beat status" "podman logs cloudcost-celery-beat" "beat"
echo ""

echo -e "${BLUE}6️⃣ API Endpoint Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Get providers" "curl -s http://localhost:8000/api/v1/multicloud/providers" "providers"
run_test "Get workload types" "curl -s http://localhost:8000/api/v1/recommendations/workload-types" "workload_types"
run_test "Get categories" "curl -s http://localhost:8000/api/v1/multicloud/categories" "categories"
echo ""

echo -e "${BLUE}7️⃣ Flower Dashboard Test${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Flower accessible" "curl -s http://localhost:5555/" "Flower"
echo ""

# Summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      📊 Test Summary                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Passed: $PASS_COUNT${NC}"
echo -e "${RED}❌ Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your CloudCost Optimizer is working perfectly! 🎉${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    echo -e "${YELLOW}💡 Tip: Run 'podman-compose logs' to see detailed logs${NC}"
    exit 1
fi
