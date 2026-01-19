# 🚀 CloudCost Optimizer - Quick Reference Card

## 📋 Test Scripts

### Run Quick Test Suite (Recommended)
```bash
./quick_test.sh
```
**What it tests**: Basic health checks for all services (12 tests, ~10 seconds)

### Run Full Integration Tests
```bash
./integration_test.sh
```
**What it tests**: Comprehensive API and integration tests (17 tests, ~30 seconds)

---

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **Health** | http://localhost:8000/health | System health check |
| **Flower** | http://localhost:5555 | Celery task monitoring |

---

## 🧪 Manual Test Commands

### 1. Health Check
```bash
curl http://localhost:8000/health | jq
```

### 2. Get Cloud Providers
```bash
curl http://localhost:8000/api/v1/multicloud/providers | jq
```

### 3. Get Workload Types
```bash
curl http://localhost:8000/api/v1/recommendations/workload-types | jq
```

### 4. List Instances (with filters)
```bash
curl "http://localhost:8000/api/v1/multicloud/instances?min_vcpus=2&min_memory=4" | jq
```

### 5. Get Quick Recommendation
```bash
curl -X POST http://localhost:8000/api/v1/recommendations/quick \
  -H "Content-Type: application/json" \
  -d '{
    "vcpus": 2,
    "memory_gb": 4,
    "region": "us-east-1"
  }' | jq
```

### 6. Get Multi-Cloud Recommendations
```bash
curl -X POST http://localhost:8000/api/v1/multicloud/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "min_vcpus": 4,
    "min_memory_gb": 8,
    "providers": ["aws", "gcp", "azure"],
    "workload_type": "steady",
    "spot_eligible": true,
    "hours_per_month": 730,
    "max_monthly_budget": 200
  }' | jq
```

### 7. Compare Instances Across Clouds
```bash
curl "http://localhost:8000/api/v1/multicloud/compare/m5.large?provider=aws" | jq
```

---

## 🐳 Podman Commands

### Container Management
```bash
# Check status
podman-compose ps

# View logs
podman logs cloudcost-api
podman logs cloudcost-celery-worker
podman logs -f cloudcost-api  # Follow logs

# Restart services
podman-compose restart
podman restart cloudcost-api  # Restart specific service

# Stop services
podman-compose down

# Start services
podman-compose up -d
```

### Database Operations
```bash
# Connect to PostgreSQL
podman exec -it cloudcost-db psql -U postgres -d cloudcost

# Check database connection
podman exec cloudcost-db pg_isready -U postgres

# Run SQL query
podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT COUNT(*) FROM cloud_instances;"

# Backup database
podman exec cloudcost-db pg_dump -U postgres cloudcost > backup.sql
```

### Redis Operations
```bash
# Check Redis connection
podman exec cloudcost-redis redis-cli ping

# Connect to Redis CLI
podman exec -it cloudcost-redis redis-cli

# Check Redis info
podman exec cloudcost-redis redis-cli INFO
```

### Celery Operations
```bash
# Check Celery worker status
podman logs cloudcost-celery-worker | grep "ready"

# Check registered tasks via Flower
open http://localhost:5555/tasks

# Manual task execution (inside container)
podman exec -it cloudcost-api celery -A src.jobs.celery_app inspect active
```

---

## 📊 Test Results Summary

### Quick Test (./quick_test.sh)
- ✅ Infrastructure: Containers running
- ✅ API Health: Endpoints responding
- ✅ Database: Connected and queryable
- ✅ Redis: Responding to commands
- ✅ Celery: Workers active
- ✅ API Endpoints: All functional
- ✅ Flower: Dashboard accessible

### Expected Results
- **11-12 tests passing** ✅
- **Response time**: < 1 second
- **All containers**: Status "Up"

---

## 🔍 Troubleshooting

### Problem: Container won't start
```bash
# Check logs
podman logs cloudcost-api

# Check all container status
podman-compose ps

# Restart container
podman restart cloudcost-api
```

### Problem: Database connection failed
```bash
# Check database is running
podman ps | grep cloudcost-db

# Check database health
podman exec cloudcost-db pg_isready -U postgres

# Restart database
podman restart cloudcost-db
```

### Problem: API returns errors
```bash
# Check API logs
podman logs cloudcost-api --tail 50

# Check if database migrations are up to date
podman exec cloudcost-api alembic current

# Run migrations if needed
podman exec cloudcost-api alembic upgrade head
```

### Problem: Port already in use
```bash
# Find what's using the port
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Clean Restart
```bash
# Stop everything
podman-compose down

# Start fresh
podman-compose up -d

# Check status
podman-compose ps
```

---

## 📚 Documentation Files

| File | Description |
|------|-------------|
| `README.md` | Main project documentation |
| `RUNNING_WITH_PODMAN.md` | Complete Podman setup guide |
| `TEST_CASES.md` | Detailed test cases documentation |
| `QUICK_REFERENCE.md` | This file - quick commands |

---

## ✅ Success Checklist

Your system is working if:
- [ ] `podman-compose ps` shows all containers "Up"
- [ ] `curl http://localhost:8000/health` returns `"healthy"`
- [ ] `curl http://localhost:8000/docs` returns Swagger UI
- [ ] `./quick_test.sh` passes 11+ tests
- [ ] `curl http://localhost:5555/` shows Flower dashboard
- [ ] No errors in `podman logs cloudcost-api`

---

## 🎯 Next Steps

1. **Explore the API**: Open http://localhost:8000/docs
2. **Run Full Tests**: `./integration_test.sh`
3. **Monitor Tasks**: http://localhost:5555
4. **Seed Data** (optional):
   ```bash
   podman exec -it cloudcost-api python -c "from src.jobs.price_updater import seed_sample_data; seed_sample_data()"
   ```
5. **Run Frontend** (optional):
   ```bash
   cd frontend && npm install && npm run dev
   ```

---

**Happy Testing!** 🎉

For detailed test documentation, see: `TEST_CASES.md`
For Podman setup details, see: `RUNNING_WITH_PODMAN.md`
