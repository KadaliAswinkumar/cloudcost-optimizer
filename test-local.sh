#!/bin/bash

# Test Everything Locally Before Deploying (Using Podman)

echo "🧪 Testing CloudCost Optimizer Locally (Podman)"
echo "================================================"
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
echo "🐳 Test 1: Checking Podman containers..."
if podman ps | grep -q cloudcost-postgres; then
    echo -e "${GREEN}✅ PostgreSQL container running${NC}"
else
    echo -e "${RED}❌ PostgreSQL container NOT running${NC}"
    echo "   Run: ./setup-local.sh"
    exit 1
fi

if podman ps | grep -q cloudcost-redis; then
    echo -e "${GREEN}✅ Redis container running${NC}"
else
    echo -e "${RED}❌ Redis container NOT running${NC}"
    echo "   Run: ./setup-local.sh"
    exit 1
fi

echo ""

# Test 2: Check backend health
echo "🔍 Test 2: Testing Backend API..."
if check_service "http://localhost:8801/health" "Backend"; then
    HEALTH=$(curl -s http://localhost:8801/health)
    echo "   Response: $HEALTH"
else
    echo -e "${YELLOW}⚠️  Backend not running. Start with: ./start-backend.sh${NC}"
fi

echo ""

# Test 3: Check frontend
echo "🔍 Test 3: Testing Frontend..."
if check_service "http://127.0.0.1:8080" "Frontend"; then
    echo "   Frontend is accessible"
else
    echo -e "${YELLOW}⚠️  Frontend not running. Start with: ./start-frontend.sh${NC}"
fi

echo ""

# Test 4: Test API endpoints
echo "🔍 Test 4: Testing API Endpoints..."

# Test root endpoint
if curl -s http://localhost:8801/ | grep -q "CloudCost"; then
    echo -e "${GREEN}✅ Root endpoint working${NC}"
else
    echo -e "${RED}❌ Root endpoint failed${NC}"
fi

# Test health endpoint
if curl -s http://localhost:8801/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health endpoint working${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
fi

# Test instances endpoint
if curl -s "http://localhost:8801/api/v1/instances?limit=5" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Instances endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Instances endpoint failed (may need data)${NC}"
fi

echo ""

# Test 5: Container status
echo "🔍 Test 5: Checking container health..."
echo "PostgreSQL:"
podman ps --filter name=cloudcost-postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Redis:"
podman ps --filter name=cloudcost-redis --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

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
