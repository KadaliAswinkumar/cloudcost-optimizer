#!/bin/bash

# CloudCost Optimizer - Local Setup with Podman
# Run this to set up everything locally before deploying to Render

set -e  # Exit on error

echo "🚀 CloudCost Optimizer - Local Setup (Using Podman)"
echo "====================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python version (must be 3.11, 3.12, or 3.13)
echo "📦 Step 1: Checking Python..."

# Try to find Python 3.11, 3.12, or 3.13
PYTHON_CMD=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | cut -d' ' -f2)
        MAJOR=$(echo $VERSION | cut -d'.' -f1)
        MINOR=$(echo $VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge 11 ] && [ "$MINOR" -le 13 ]; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$VERSION
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python 3.11, 3.12, or 3.13 not found!${NC}"
    echo ""
    echo "Your system has Python 3.14, but the packages don't support it yet."
    echo ""
    echo "Install Python 3.11 or 3.12:"
    echo "  brew install python@3.11"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Step 2: Create virtual environment
echo ""
echo "📦 Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created with $PYTHON_VERSION${NC}"
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

# Step 4: Check for Podman
echo ""
echo "🐳 Step 4: Checking Podman..."
if ! command -v podman &> /dev/null; then
    echo -e "${RED}❌ Podman not found!${NC}"
    echo "Install Podman from: https://podman.io/getting-started/installation"
    echo ""
    echo "macOS: brew install podman"
    echo "       podman machine init"
    echo "       podman machine start"
    exit 1
fi

# Check if podman machine is running (macOS/Windows)
if podman machine list 2>/dev/null | grep -q "Currently running"; then
    echo -e "${GREEN}✅ Podman machine is running${NC}"
elif podman machine list 2>/dev/null | grep -q "Last up"; then
    echo -e "${YELLOW}⚠️  Starting podman machine...${NC}"
    podman machine start
    echo -e "${GREEN}✅ Podman machine started${NC}"
else
    echo -e "${GREEN}✅ Podman found${NC}"
fi

# Step 5: Start PostgreSQL with Podman
echo ""
echo "🐘 Step 5: Starting PostgreSQL..."

# Check if container exists (running or stopped)
if podman ps -a | grep -q cloudcost-postgres; then
    echo -e "${YELLOW}⚠️  Old PostgreSQL container found, removing...${NC}"
    podman stop cloudcost-postgres 2>/dev/null || true
    podman rm -f cloudcost-postgres 2>/dev/null || true
    sleep 1
fi

# Check if it's running
if podman ps | grep -q cloudcost-postgres; then
    echo -e "${YELLOW}⚠️  PostgreSQL container already running${NC}"
else
    podman run -d \
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

# Step 6: Start Redis with Podman
echo ""
echo "📮 Step 6: Starting Redis..."

# Check if container exists (running or stopped)
if podman ps -a | grep -q cloudcost-redis; then
    echo -e "${YELLOW}⚠️  Old Redis container found, removing...${NC}"
    podman stop cloudcost-redis 2>/dev/null || true
    podman rm -f cloudcost-redis 2>/dev/null || true
    sleep 1
fi

# Check if it's running
if podman ps | grep -q cloudcost-redis; then
    echo -e "${YELLOW}⚠️  Redis container already running${NC}"
else
    podman run -d \
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
$PYTHON_CMD -c "
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
$PYTHON_CMD -c "
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
$PYTHON_CMD -c "
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
echo "  podman stop cloudcost-postgres cloudcost-redis"
echo ""
echo "To remove containers:"
echo "  podman rm cloudcost-postgres cloudcost-redis"
echo ""
echo "Documentation: See doc/ directory for guides"
echo ""
