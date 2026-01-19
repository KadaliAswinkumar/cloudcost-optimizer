# 🧪 CloudCost Optimizer - Test Cases

This document provides comprehensive test cases to verify that your CloudCost Optimizer is working properly with Podman.

## Table of Contents
1. [Infrastructure Tests](#1-infrastructure-tests)
2. [API Health Tests](#2-api-health-tests)
3. [Database Tests](#3-database-tests)
4. [Cache (Redis) Tests](#4-cache-redis-tests)
5. [Celery Worker Tests](#5-celery-worker-tests)
6. [API Endpoint Tests](#6-api-endpoint-tests)
7. [Multi-Cloud Tests](#7-multi-cloud-tests)
8. [Performance Tests](#8-performance-tests)

---

## 1. Infrastructure Tests

### Test 1.1: Check All Containers Are Running

```bash
podman-compose ps
```

**Expected Output**: All 6 containers should show status "Up"
- ✅ cloudcost-api
- ✅ cloudcost-db
- ✅ cloudcost-redis
- ✅ cloudcost-celery-worker
- ✅ cloudcost-celery-beat
- ✅ cloudcost-flower

### Test 1.2: Check Container Health

```bash
# Check database health
podman exec cloudcost-db pg_isready -U postgres

# Check Redis health
podman exec cloudcost-redis redis-cli ping

# Check API health
curl -s http://localhost:8000/health | jq
```

**Expected Output**:
- PostgreSQL: `postgres:5432 - accepting connections`
- Redis: `PONG`
- API: `{"status":"healthy",...}`

---

## 2. API Health Tests

### Test 2.1: Basic Health Check

```bash
curl -s http://localhost:8000/health | jq
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "CloudCost Optimizer",
  "version": "1.0.0",
  "timestamp": "2026-01-19T..."
}
```

### Test 2.2: API Documentation Accessibility

```bash
# Check Swagger UI
curl -s http://localhost:8000/docs | grep -q "swagger" && echo "✅ Swagger UI accessible" || echo "❌ Swagger UI not accessible"

# Check ReDoc
curl -s http://localhost:8000/redoc | grep -q "redoc" && echo "✅ ReDoc accessible" || echo "❌ ReDoc not accessible"
```

**Expected Output**: Both should show "✅ accessible"

### Test 2.3: API Response Time

```bash
time curl -s http://localhost:8000/health > /dev/null
```

**Expected Output**: Should complete in < 1 second

---

## 3. Database Tests

### Test 3.1: Database Connection

```bash
podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT 1 as connection_test;"
```

**Expected Output**:
```
 connection_test 
-----------------
               1
```

### Test 3.2: Check Database Tables

```bash
podman exec cloudcost-db psql -U postgres -d cloudcost -c "\dt"
```

**Expected Output**: Should list tables like:
- `cloud_instances`
- `cloud_pricing`
- `alembic_version`
- etc.

### Test 3.3: Check Data in Tables

```bash
# Check if tables have been created
podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

**Expected Output**: Should show a number greater than 0

### Test 3.4: Run Database Migrations

```bash
podman exec cloudcost-api alembic current
```

**Expected Output**: Should show current migration version (no errors)

---

## 4. Cache (Redis) Tests

### Test 4.1: Redis Ping

```bash
podman exec cloudcost-redis redis-cli ping
```

**Expected Output**: `PONG`

### Test 4.2: Redis Set/Get Test

```bash
# Set a test key
podman exec cloudcost-redis redis-cli SET test_key "test_value"

# Get the test key
podman exec cloudcost-redis redis-cli GET test_key

# Delete the test key
podman exec cloudcost-redis redis-cli DEL test_key
```

**Expected Output**:
- SET: `OK`
- GET: `"test_value"`
- DEL: `(integer) 1`

### Test 4.3: Check Redis Memory

```bash
podman exec cloudcost-redis redis-cli INFO memory | grep used_memory_human
```

**Expected Output**: Should show memory usage (e.g., `used_memory_human:1.23M`)

---

## 5. Celery Worker Tests

### Test 5.1: Check Celery Worker Status

```bash
podman logs cloudcost-celery-worker --tail 20
```

**Expected Output**: Should show "celery@... ready." with no errors

### Test 5.2: Check Celery Beat (Scheduler) Status

```bash
podman logs cloudcost-celery-beat --tail 20
```

**Expected Output**: Should show beat scheduler running with no errors

### Test 5.3: Access Flower Dashboard

```bash
curl -s http://localhost:5555/ | grep -q "Flower" && echo "✅ Flower dashboard accessible" || echo "❌ Flower dashboard not accessible"
```

**Expected Output**: `✅ Flower dashboard accessible`

### Test 5.4: Check Registered Tasks in Flower

Open in browser: http://localhost:5555/tasks

**Expected**: Should see registered Celery tasks

---

## 6. API Endpoint Tests

### Test 6.1: Get Workload Types

```bash
curl -s http://localhost:8000/api/v1/recommendations/workload-types | jq
```

**Expected Output**: List of workload types
```json
{
  "workload_types": [
    {
      "id": "steady",
      "name": "Steady State",
      "description": "..."
    },
    ...
  ]
}
```

### Test 6.2: Get Multi-Cloud Providers

```bash
curl -s http://localhost:8000/api/v1/multicloud/providers | jq
```

**Expected Output**: List of providers (AWS, GCP, Azure)
```json
{
  "providers": [
    {
      "id": "aws",
      "name": "Amazon Web Services",
      ...
    },
    ...
  ]
}
```

### Test 6.3: Get Instance Categories

```bash
curl -s http://localhost:8000/api/v1/multicloud/categories | jq
```

**Expected Output**: Instance categories
```json
{
  "categories": [
    {
      "id": "general",
      "name": "General Purpose",
      ...
    },
    ...
  ]
}
```

### Test 6.4: List Cloud Instances (with filters)

```bash
curl -s "http://localhost:8000/api/v1/multicloud/instances?min_vcpus=2&min_memory=4" | jq
```

**Expected Output**: Paginated list of instances
```json
{
  "instances": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Test 6.5: Get Specific Instance Details (AWS)

```bash
curl -s "http://localhost:8000/api/v1/multicloud/instances/aws/t3.medium" | jq
```

**Expected Output**: Instance details
```json
{
  "provider": "aws",
  "instance_type": "t3.medium",
  "vcpus": 2,
  "memory_gb": 4,
  ...
}
```

### Test 6.6: Quick Recommendation

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/quick \
  -H "Content-Type: application/json" \
  -d '{
    "vcpus": 2,
    "memory_gb": 4,
    "region": "us-east-1"
  }' | jq
```

**Expected Output**: Quick recommendation response

---

## 7. Multi-Cloud Tests

### Test 7.1: Multi-Cloud Recommendations

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

**Expected Output**: Multi-cloud recommendations
```json
{
  "overall_best": [...],
  "by_provider": {
    "aws": [...],
    "gcp": [...],
    "azure": [...]
  },
  "cross_cloud_comparison": {...}
}
```

### Test 7.2: Find Equivalent Instances

```bash
curl -s "http://localhost:8000/api/v1/multicloud/compare/m5.large?provider=aws" | jq
```

**Expected Output**: Equivalent instances across clouds
```json
{
  "source": {
    "provider": "aws",
    "instance_type": "m5.large",
    ...
  },
  "equivalents": {
    "gcp": [...],
    "azure": [...]
  }
}
```

### Test 7.3: Compare Pricing Across Clouds

```bash
curl -s "http://localhost:8000/api/v1/multicloud/pricing/compare?vcpus=4&memory_gb=16" | jq
```

**Expected Output**: Pricing comparison
```json
{
  "specifications": {
    "vcpus": 4,
    "memory_gb": 16
  },
  "comparisons": [
    {
      "provider": "aws",
      "instance_type": "...",
      "pricing": {...}
    },
    ...
  ]
}
```

---

## 8. Performance Tests

### Test 8.1: API Response Time Test

```bash
# Test multiple requests
echo "Testing API response times (10 requests):"
for i in {1..10}; do
  time curl -s http://localhost:8000/health > /dev/null
done
```

**Expected Output**: All requests should complete in < 1 second

### Test 8.2: Concurrent Request Test

```bash
# Test 10 concurrent requests
echo "Testing concurrent requests..."
for i in {1..10}; do
  curl -s http://localhost:8000/health > /dev/null &
done
wait
echo "✅ All concurrent requests completed"
```

**Expected Output**: All requests should complete successfully

### Test 8.3: Database Query Performance

```bash
# Time a database query
time podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT COUNT(*) FROM information_schema.tables;"
```

**Expected Output**: Should complete in < 500ms

---

## 9. Integration Tests

### Test 9.1: Full Workflow Test

```bash
#!/bin/bash
echo "🧪 Running Full Integration Test..."

# Step 1: Health check
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | jq -r '.status' | grep -q "healthy" && echo "✅ Health check passed" || echo "❌ Health check failed"

# Step 2: Get providers
echo "2. Testing providers endpoint..."
curl -s http://localhost:8000/api/v1/multicloud/providers | jq -r '.providers[0].id' | grep -q "aws" && echo "✅ Providers endpoint passed" || echo "❌ Providers endpoint failed"

# Step 3: Get workload types
echo "3. Testing workload types endpoint..."
curl -s http://localhost:8000/api/v1/recommendations/workload-types | jq -r '.workload_types[0].id' | grep -q "steady" && echo "✅ Workload types passed" || echo "❌ Workload types failed"

# Step 4: List instances
echo "4. Testing instances listing..."
INSTANCES=$(curl -s "http://localhost:8000/api/v1/multicloud/instances?min_vcpus=2")
echo $INSTANCES | jq -r '.instances' | grep -q '\[' && echo "✅ Instance listing passed" || echo "❌ Instance listing failed"

# Step 5: Database connectivity
echo "5. Testing database connectivity..."
podman exec cloudcost-db psql -U postgres -d cloudcost -c "SELECT 1;" > /dev/null 2>&1 && echo "✅ Database connection passed" || echo "❌ Database connection failed"

# Step 6: Redis connectivity
echo "6. Testing Redis connectivity..."
podman exec cloudcost-redis redis-cli ping | grep -q "PONG" && echo "✅ Redis connection passed" || echo "❌ Redis connection failed"

# Step 7: Celery worker
echo "7. Testing Celery worker..."
podman logs cloudcost-celery-worker 2>&1 | grep -q "ready" && echo "✅ Celery worker passed" || echo "❌ Celery worker failed"

echo ""
echo "🎉 Integration test complete!"
```

**Save this as `run_tests.sh` and execute**:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## 10. Error Handling Tests

### Test 10.1: Invalid Endpoint

```bash
curl -s http://localhost:8000/api/v1/invalid-endpoint
```

**Expected Output**: 404 error with proper JSON response

### Test 10.2: Invalid Request Body

```bash
curl -X POST http://localhost:8000/api/v1/multicloud/recommendations \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

**Expected Output**: 422 Validation Error with details

### Test 10.3: Missing Required Parameters

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/quick \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Output**: 422 Validation Error listing missing fields

---

## 🎯 Quick Test Suite

Run all critical tests at once:

```bash
#!/bin/bash
echo "🚀 Running Quick Test Suite..."
echo ""

# Test 1: Container Health
echo "1️⃣ Container Health:"
podman-compose ps | grep -q "Up" && echo "✅ Containers running" || echo "❌ Containers not running"

# Test 2: API Health
echo ""
echo "2️⃣ API Health:"
curl -s http://localhost:8000/health | jq -r '.status' | grep -q "healthy" && echo "✅ API healthy" || echo "❌ API not healthy"

# Test 3: Database
echo ""
echo "3️⃣ Database:"
podman exec cloudcost-db pg_isready -U postgres | grep -q "accepting connections" && echo "✅ Database connected" || echo "❌ Database not connected"

# Test 4: Redis
echo ""
echo "4️⃣ Redis:"
podman exec cloudcost-redis redis-cli ping | grep -q "PONG" && echo "✅ Redis connected" || echo "❌ Redis not connected"

# Test 5: API Endpoints
echo ""
echo "5️⃣ API Endpoints:"
curl -s http://localhost:8000/api/v1/multicloud/providers | jq -r '.providers' | grep -q '\[' && echo "✅ Endpoints working" || echo "❌ Endpoints not working"

# Test 6: Flower
echo ""
echo "6️⃣ Flower Dashboard:"
curl -s http://localhost:5555/ | grep -q "Flower" && echo "✅ Flower accessible" || echo "❌ Flower not accessible"

echo ""
echo "✨ Quick test suite complete!"
```

**Save as `quick_test.sh` and run**:
```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

## 📊 Expected Results Summary

| Test Category | Expected Result |
|---------------|-----------------|
| **Infrastructure** | All 6 containers running |
| **API Health** | Status: healthy, response < 1s |
| **Database** | Connected, tables created |
| **Redis** | PONG response, caching works |
| **Celery** | Workers ready, no errors |
| **API Endpoints** | All endpoints return valid JSON |
| **Multi-Cloud** | Recommendations from all providers |
| **Performance** | Response time < 1s for most endpoints |

---

## 🐛 Troubleshooting

If any test fails:

1. **Check logs**:
   ```bash
   podman logs cloudcost-api
   podman logs cloudcost-celery-worker
   ```

2. **Restart services**:
   ```bash
   podman-compose restart
   ```

3. **Check database migrations**:
   ```bash
   podman exec cloudcost-api alembic upgrade head
   ```

4. **Verify all containers are running**:
   ```bash
   podman-compose ps
   ```

---

## 🎉 Success Criteria

Your CloudCost Optimizer is working properly if:

- ✅ All containers are running
- ✅ Health endpoint returns "healthy"
- ✅ Database accepts connections
- ✅ Redis responds to PING
- ✅ API endpoints return valid responses
- ✅ Flower dashboard is accessible
- ✅ No errors in container logs
- ✅ Response times are < 1 second

---

**Happy Testing!** 🧪🚀
