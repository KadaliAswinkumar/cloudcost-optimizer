#!/bin/bash

# Test Everything Locally Before Deploying

echo "🧪 Testing CloudCost Optimizer Locally"
echo "======================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is NOT running${NC}"
        return 1
    fi
}

# Test 1: Check if containers are running
echo "🐳 Test 1: Checking Docker containers..."
if docker ps | grep -q cloudcost-postgres; then
    echo -e "${GREEN}✅ PostgreSQL container running${NC}"
else
    echo -e "${RED}❌ PostgreSQL container NOT running${NC}"
    echo "   Run: ./setup-local.sh"
    exit 1
fi

if docker ps | grep -q cloudcost-redis; then
    echo -e "${GREEN}✅ Redis container running${NC}"
else
    echo -e "${RED}❌ Redis container NOT running${NC}"
    echo "   Run: ./setup-local.sh"
    exit 1
fi

echo ""

# Test 2: Check backend health
echo "🔍 Test 2: Testing Backend API..."
if check_service "http://localhost:8000/health" "Backend"; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH"
else
    echo -e "${YELLOW}⚠️  Backend not running. Start with: ./start-backend.sh${NC}"
fi

echo ""

# Test 3: Check frontend
echo "🔍 Test 3: Testing Frontend..."
if check_service "http://localhost:5173" "Frontend"; then
    echo "   Frontend is accessible"
else
    echo -e "${YELLOW}⚠️  Frontend not running. Start with: ./start-frontend.sh${NC}"
fi

echo ""

# Test 4: Test API endpoints
echo "🔍 Test 4: Testing API Endpoints..."

# Test root endpoint
if curl -s http://localhost:8000/ | grep -q "CloudCost"; then
    echo -e "${GREEN}✅ Root endpoint working${NC}"
else
    echo -e "${RED}❌ Root endpoint failed${NC}"
fi

# Test instances endpoint
if curl -s http://localhost:8000/api/v1/instances?limit=5 | grep -q "instances"; then
    echo -e "${GREEN}✅ Instances endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Instances endpoint failed (may need data)${NC}"
fi

# Test pricing endpoint
if curl -s http://localhost:8000/api/v1/pricing/spot/history?limit=5 | grep -q "history"; then
    echo -e "${GREEN}✅ Pricing endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Pricing endpoint failed (may need data)${NC}"
fi

echo ""

# Test 5: Check logs for errors
echo "🔍 Test 5: Checking for errors in logs..."
echo "   (Check terminal running backend for any red error messages)"

echo ""
echo "======================================"
echo -e "${GREEN}✅ LOCAL TESTING COMPLETE${NC}"
echo "======================================"
echo ""
echo "If all tests passed, you're ready to deploy to Render!"
echo ""
echo "To deploy:"
echo "1. git add ."
echo "2. git commit -m 'Ready for deployment'"
echo "3. git push origin main"
echo "4. Go to Render dashboard and click 'Deploy latest commit'"
echo ""
