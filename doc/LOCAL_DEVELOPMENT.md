# Local Development Guide

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Node.js 18+** - [Download](https://nodejs.org/)

## Quick Start (5 Minutes)

### Step 1: Initial Setup
```bash
# Make scripts executable
chmod +x setup-local.sh start-backend.sh start-frontend.sh test-local.sh

# Run setup (creates venv, starts Docker containers, runs migrations)
./setup-local.sh
```

**This will:**
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Start PostgreSQL in Docker (port 5433)
- ✅ Start Redis in Docker (port 6379)
- ✅ Run database migrations
- ✅ Test all connections

### Step 2: Start Backend
```bash
# In terminal 1
./start-backend.sh
```

**Backend will be available at:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Step 3: Start Frontend
```bash
# In terminal 2
./start-frontend.sh
```

**Frontend will be available at:**
- App: http://localhost:5173

### Step 4: Test Everything
```bash
# In terminal 3
./test-local.sh
```

**This tests:**
- ✅ Docker containers running
- ✅ Backend health endpoint
- ✅ Frontend accessibility
- ✅ All API endpoints
- ✅ Database connection
- ✅ Redis connection

---

## Manual Setup (If Scripts Don't Work)

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start PostgreSQL (Docker)
```bash
docker run -d \
  --name cloudcost-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cloudcost \
  -p 5433:5432 \
  postgres:14-alpine
```

### 3. Start Redis (Docker)
```bash
docker run -d \
  --name cloudcost-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 4. Run Migrations
```bash
source venv/bin/activate
alembic upgrade head
```

### 5. Start Backend
```bash
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Testing Checklist

Before deploying to Render, verify:

### Backend Tests
- [ ] `curl http://localhost:8000/health` returns 200 OK
- [ ] `curl http://localhost:8000/` shows welcome message
- [ ] Visit http://localhost:8000/docs - Swagger UI loads
- [ ] Test `/api/v1/instances` endpoint
- [ ] Test `/api/v1/recommendations` endpoint
- [ ] No errors in backend terminal

### Frontend Tests
- [ ] Open http://localhost:5173
- [ ] Landing page loads correctly
- [ ] Can click "Login" button
- [ ] Can click "Sign up free" link
- [ ] Can register new account
- [ ] Can login successfully
- [ ] Dashboard loads after login
- [ ] No errors in browser console (F12)

### Database Tests
```bash
# Connect to PostgreSQL
docker exec -it cloudcost-postgres psql -U postgres -d cloudcost

# Check tables exist
\dt

# Should see tables like:
# - cloud_instances
# - cloud_pricing
# - recommendations
# - users
# etc.
```

### Redis Tests
```bash
# Test Redis connection
docker exec -it cloudcost-redis redis-cli ping
# Should return: PONG
```

---

## Common Issues & Solutions

### Issue: Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn src.api.main:app --port 8001
```

### Issue: PostgreSQL Connection Failed
```bash
# Check if container is running
docker ps | grep cloudcost-postgres

# Check logs
docker logs cloudcost-postgres

# Restart container
docker restart cloudcost-postgres
```

### Issue: Redis Connection Failed
```bash
# Check if container is running
docker ps | grep cloudcost-redis

# Restart container
docker restart cloudcost-redis
```

### Issue: Migration Errors
```bash
# Reset database (WARNING: Deletes all data)
docker exec -it cloudcost-postgres psql -U postgres -c "DROP DATABASE cloudcost; CREATE DATABASE cloudcost;"

# Run migrations again
alembic upgrade head
```

### Issue: Import Errors
```bash
# Make sure you're in the project root
cd /path/to/cloudcost-optimizer

# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Stopping Everything

### Stop Backend & Frontend
Press `Ctrl+C` in each terminal

### Stop Docker Containers
```bash
docker stop cloudcost-postgres cloudcost-redis
```

### Remove Docker Containers (Clean Slate)
```bash
docker rm cloudcost-postgres cloudcost-redis
```

### Deactivate Virtual Environment
```bash
deactivate
```

---

## Development Workflow

### Daily Development
```bash
# Start containers (if not running)
docker start cloudcost-postgres cloudcost-redis

# Activate venv
source venv/bin/activate

# Start backend
uvicorn src.api.main:app --reload

# In another terminal, start frontend
cd frontend && npm run dev
```

### After Making Code Changes
```bash
# Backend changes are auto-reloaded (--reload flag)
# Frontend changes are auto-reloaded (Vite HMR)

# If you change database models:
alembic revision --autogenerate -m "Description of change"
alembic upgrade head
```

### Before Committing
```bash
# Run linters
ruff check src/
black src/
cd frontend && npm run lint

# Run tests (when we add them)
pytest

# Test locally
./test-local.sh
```

---

## Environment Variables

The `.env` file is already configured for local development:

```bash
# Application
DEBUG=true
ENVIRONMENT=development

# Database (Docker PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/cloudcost

# Redis (Docker Redis)
REDIS_URL=redis://localhost:6379/0

# AWS (Optional - for real pricing data)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
```

**Don't commit `.env` file!** (Already in `.gitignore`)

---

## Performance Tips

### Speed Up Backend Reload
```bash
# Use watchfiles for faster reloading
pip install watchfiles
uvicorn src.api.main:app --reload --reload-dir src
```

### Speed Up Frontend Dev Server
```bash
# Already configured in vite.config.js
# Uses esbuild for fast builds
```

### Cache Dependencies
```bash
# Backend: venv is already cached
# Frontend: node_modules is cached after first install
```

---

## Debugging

### Backend Debugging
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use VS Code debugger
# .vscode/launch.json already configured
```

### Frontend Debugging
- Open browser DevTools (F12)
- Use React DevTools extension
- Check Console for errors
- Check Network tab for API calls

### Database Debugging
```bash
# Connect to database
docker exec -it cloudcost-postgres psql -U postgres -d cloudcost

# Run queries
SELECT * FROM cloud_instances LIMIT 5;

# Check table structure
\d cloud_instances
```

### Redis Debugging
```bash
# Connect to Redis
docker exec -it cloudcost-redis redis-cli

# Check keys
KEYS *

# Get value
GET key_name

# Clear all
FLUSHALL
```

---

## Next Steps

After everything works locally:

1. ✅ All tests pass (`./test-local.sh`)
2. ✅ No errors in backend logs
3. ✅ No errors in frontend console
4. ✅ Can login and use all features
5. 🚀 Ready to deploy to Render!

**Deployment command:**
```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

Then go to Render dashboard and click **"Deploy latest commit"**

---

## Need Help?

- Check logs: `docker logs cloudcost-postgres`
- Check backend logs: Terminal where backend is running
- Check frontend logs: Browser console (F12)
- Run diagnostics: `./test-local.sh`
