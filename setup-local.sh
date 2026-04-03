#!/bin/bash

# CloudCost Optimizer - Local Setup & Test Script
# Run this to set up everything locally before deploying to Render

set -e  # Exit on error

echo "🚀 CloudCost Optimizer - Local Setup"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo "📦 Step 1: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found!${NC}"
    echo "Install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Step 2: Create virtual environment
echo ""
echo "📦 Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Step 3: Activate and install dependencies
echo ""
echo "📦 Step 3: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 4: Check for Docker
echo ""
echo "🐳 Step 4: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found!${NC}"
    echo "We'll use Docker for PostgreSQL and Redis"
    echo "Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Step 5: Start PostgreSQL with Docker
echo ""
echo "🐘 Step 5: Starting PostgreSQL..."
if docker ps | grep -q cloudcost-postgres; then
    echo -e "${YELLOW}⚠️  PostgreSQL container already running${NC}"
else
    docker run -d \
        --name cloudcost-postgres \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=cloudcost \
        -p 5433:5432 \
        postgres:14-alpine
    
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
    echo -e "${GREEN}✅ PostgreSQL started on port 5433${NC}"
fi

# Step 6: Start Redis with Docker
echo ""
echo "📮 Step 6: Starting Redis..."
if docker ps | grep -q cloudcost-redis; then
    echo -e "${YELLOW}⚠️  Redis container already running${NC}"
else
    docker run -d \
        --name cloudcost-redis \
        -p 6379:6379 \
        redis:7-alpine
    
    echo "⏳ Waiting for Redis to be ready..."
    sleep 2
    echo -e "${GREEN}✅ Redis started on port 6379${NC}"
fi

# Step 7: Run database migrations
echo ""
echo "🔄 Step 7: Running database migrations..."
alembic upgrade head
echo -e "${GREEN}✅ Database migrations completed${NC}"

# Step 8: Test backend imports
echo ""
echo "🧪 Step 8: Testing backend imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.models import SpotPriceHistory
    from src.core.config import settings
    from src.api.main import app
    print('✅ All imports successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
echo -e "${GREEN}✅ Backend imports working${NC}"

# Step 9: Test database connection
echo ""
echo "🧪 Step 9: Testing database connection..."
python3 -c "
import asyncio
from src.core.database import init_db, close_db

async def test():
    try:
        await init_db()
        print('✅ Database connection successful!')
        await close_db()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)

asyncio.run(test())
"
echo -e "${GREEN}✅ Database connection working${NC}"

# Step 10: Check Redis connection
echo ""
echo "🧪 Step 10: Testing Redis connection..."
python3 -c "
import redis
try:
    r = redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis connection successful!')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"
echo -e "${GREEN}✅ Redis connection working${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 LOCAL SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start backend:  ./start-backend.sh"
echo "2. Start frontend: ./start-frontend.sh"
echo "3. Open browser:   http://localhost:5173"
echo ""
echo "To stop containers:"
echo "  docker stop cloudcost-postgres cloudcost-redis"
echo ""
echo "To remove containers:"
echo "  docker rm cloudcost-postgres cloudcost-redis"
echo ""
