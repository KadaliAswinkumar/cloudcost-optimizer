# Running CloudCost Optimizer with Podman

This document explains how to run the CloudCost Optimizer project using **Podman** instead of Docker.

## ✅ Status

The project is now successfully running with Podman! All services are up and operational.

## 🚀 Quick Start

### Start All Services

```bash
cd /Users/aswinkumar/Downloads/Aswin/Startups/cloudcost-optimizer
podman-compose up -d
```

### Check Service Status

```bash
podman-compose ps
```

### Stop All Services

```bash
podman-compose down
```

## 📊 Services Running

| Service | Container Name | Port | Status | Description |
|---------|---------------|------|--------|-------------|
| **FastAPI API** | `cloudcost-api` | 8000 | ✅ Running | Main REST API service |
| **PostgreSQL** | `cloudcost-db` | 5433 | ✅ Running | Database (mapped to 5433 to avoid conflicts) |
| **Redis** | `cloudcost-redis` | 6379 | ✅ Running | Cache and message broker |
| **Celery Worker** | `cloudcost-celery-worker` | - | ✅ Running | Background task processor |
| **Celery Beat** | `cloudcost-celery-beat` | - | ✅ Running | Task scheduler |
| **Flower** | `cloudcost-flower` | 5555 | ✅ Running | Celery monitoring dashboard |

## 🌐 Access Points

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Monitoring
- **Flower Dashboard**: http://localhost:5555 (Celery task monitoring)

### Database
- **PostgreSQL**: `localhost:5433`
  - Username: `postgres`
  - Password: `postgres`
  - Database: `cloudcost`

### Cache
- **Redis**: `localhost:6379`

## 🔧 Useful Commands

### View Logs

```bash
# View API logs
podman logs cloudcost-api

# View Celery worker logs
podman logs cloudcost-celery-worker

# View database logs
podman logs cloudcost-db

# Follow logs in real-time
podman logs -f cloudcost-api
```

### Restart Services

```bash
# Restart specific service
podman restart cloudcost-api

# Restart all services
podman-compose restart
```

### Execute Commands in Containers

```bash
# Access the API container shell
podman exec -it cloudcost-api /bin/bash

# Run database migrations
podman exec -it cloudcost-api alembic upgrade head

# Seed sample data
podman exec -it cloudcost-api python -c "from src.jobs.price_updater import seed_sample_data; seed_sample_data()"
```

### Database Operations

```bash
# Connect to PostgreSQL
podman exec -it cloudcost-db psql -U postgres -d cloudcost

# Backup database
podman exec cloudcost-db pg_dump -U postgres cloudcost > backup.sql

# Restore database
cat backup.sql | podman exec -i cloudcost-db psql -U postgres cloudcost
```

## 🔍 Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "CloudCost Optimizer",
  "version": "1.0.0",
  "timestamp": "2026-01-19T10:04:18.857247"
}
```

### List Instances

```bash
curl http://localhost:8000/api/v1/instances | jq
```

### Get Multi-Cloud Recommendations

```bash
curl -X POST http://localhost:8000/api/v1/multicloud/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "min_vcpus": 4,
    "min_memory_gb": 16,
    "providers": ["aws", "gcp", "azure"],
    "workload_type": "steady",
    "spot_eligible": true,
    "hours_per_month": 730,
    "max_monthly_budget": 200
  }' | jq
```

## ⚠️ Important Notes

### Port Conflict Resolution

The PostgreSQL port was changed from `5432` to `5433` to avoid conflicts with local PostgreSQL installations. The containers internally still use port 5432, but it's mapped to 5433 on the host.

If you need to change this back or use different ports, edit the `docker-compose.yml` file:

```yaml
db:
  ports:
    - "5433:5432"  # Change 5433 to your preferred port
```

### Podman vs Docker

Podman is a drop-in replacement for Docker with these advantages:
- **Daemonless**: No background daemon required
- **Rootless**: Can run without root privileges
- **Pod-based**: Native Kubernetes pod support
- **Compatible**: Uses the same CLI commands as Docker

All `docker` commands work with `podman`:
```bash
# These are equivalent
docker ps          ↔  podman ps
docker logs        ↔  podman logs
docker-compose up  ↔  podman-compose up
```

## 🎯 Next Steps

### 1. Initialize Database

If this is your first run, initialize the database:

```bash
podman exec -it cloudcost-api alembic upgrade head
```

### 2. Seed Sample Data (Optional)

To test without AWS credentials:

```bash
podman exec -it cloudcost-api python -c "from src.jobs.price_updater import seed_sample_data; seed_sample_data()"
```

### 3. Run Tests

```bash
podman exec -it cloudcost-api pytest
```

### 4. Access Frontend (Optional)

If you want to run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check container logs
podman logs cloudcost-api

# Check container status
podman ps -a

# Restart container
podman restart cloudcost-api
```

### Port Already in Use

If you see "address already in use" errors:

1. Find what's using the port:
   ```bash
   lsof -i :8000  # or whatever port
   ```

2. Either stop the conflicting service or change the port in `docker-compose.yml`

### Database Connection Issues

```bash
# Check if database is healthy
podman ps | grep cloudcost-db

# Test database connection
podman exec -it cloudcost-db psql -U postgres -c "SELECT 1;"
```

### Redis Connection Issues

```bash
# Check Redis status
podman exec -it cloudcost-redis redis-cli ping
```

### Clean Restart

If things are broken, try a clean restart:

```bash
# Stop and remove all containers
podman-compose down

# Remove volumes (WARNING: This deletes all data!)
podman volume prune

# Start fresh
podman-compose up -d
```

## 📝 Configuration

### Environment Variables

The `.env` file contains configuration. Key variables:

```bash
# Database (internal container connection)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/cloudcost

# Redis (internal container connection)
REDIS_URL=redis://redis:6379/0

# AWS (optional - for live data)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

## 🎉 Success!

Your CloudCost Optimizer is now running successfully with Podman! 

- **API**: http://localhost:8000/docs
- **Flower**: http://localhost:5555
- **Health**: http://localhost:8000/health

Enjoy optimizing your cloud costs! 💰☁️
