# QUICK START - Test Locally Before Deploying

## The Smart Way: Test → Fix → Deploy

### Step 1: One Command Setup (2 minutes)
```bash
./setup-local.sh
```

**This automatically:**
- Creates Python virtual environment
- Installs all dependencies
- Starts PostgreSQL (Docker)
- Starts Redis (Docker)
- Runs database migrations
- Tests all connections

### Step 2: Start Backend (Terminal 1)
```bash
./start-backend.sh
```

Visit: http://localhost:8000/docs

### Step 3: Start Frontend (Terminal 2)
```bash
./start-frontend.sh
```

Visit: http://localhost:5173

### Step 4: Test Everything (Terminal 3)
```bash
./test-local.sh
```

**This tests:**
- Docker containers running
- Backend API health
- Frontend accessibility
- All endpoints working
- Database connection
- Redis connection

---

## If Everything Works Locally ✅

**Then and ONLY then, deploy to Render:**

```bash
git add .
git commit -m "Tested locally - ready for production"
git push origin main
```

Go to Render → Click "Deploy latest commit"

---

## If Something Fails ❌

**Check the guide:** `LOCAL_DEVELOPMENT.md`

**Common fixes:**
- Docker not running → Start Docker Desktop
- Port in use → Kill process: `lsof -ti:8000 | xargs kill -9`
- Missing dependencies → `pip install -r requirements.txt`
- Migration errors → Check `LOCAL_DEVELOPMENT.md`

---

## Why This Approach?

### Before (Bad):
1. Make change
2. Push to GitHub
3. Deploy to Render
4. Fails
5. Waste free tier resources
6. Repeat 😞

### Now (Smart):
1. Make change
2. Test locally with `./test-local.sh`
3. Fix any issues
4. Push only when working ✅
5. Deploy to Render
6. Works first time! 🎉

---

## Requirements

- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Python 3.11+** - Already have 3.14.2 ✅
- **Node.js 18+** - For frontend

---

## Troubleshooting

### "Docker not found"
```bash
# Install Docker Desktop from:
https://www.docker.com/products/docker-desktop

# After install, start Docker Desktop app
```

### "Port already in use"
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.api.main:app --port 8001
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## Next Steps

1. Install Docker Desktop (if you don't have it)
2. Run `./setup-local.sh`
3. Run `./start-backend.sh` (Terminal 1)
4. Run `./start-frontend.sh` (Terminal 2)
5. Run `./test-local.sh` (Terminal 3)
6. If all ✅ → Deploy to Render!

**See `LOCAL_DEVELOPMENT.md` for detailed guide**
