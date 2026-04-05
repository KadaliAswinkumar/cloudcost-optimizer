# CloudCost Optimizer

A smart, AI-powered cloud cost optimization platform that helps you analyze, compare, and reduce your AWS cloud spending.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Multi-Cloud Comparison**: Compare instance types across AWS regions
- **AI-Powered Recommendations**: Get intelligent cost-saving suggestions
- **Spot Instance Intelligence**: Analyze spot pricing trends and interruption risks
- **Real-time Price Analysis**: Live AWS pricing data integration
- **Interactive Dashboard**: Beautiful, modern UI with real-time metrics

## Quick Start

### Local Development (Using Podman)

```bash
# 1. Setup environment (one time)
./setup-local.sh

# 2. Start backend (Terminal 1)
./start-backend.sh

# 3. Start frontend (Terminal 2)
./start-frontend.sh

# 4. Test everything (Terminal 3)
./test-local.sh
```

**Access:**
- Frontend: http://127.0.0.1:8080
- Backend API: http://localhost:8801
- API Docs: http://localhost:8801/docs

**Important — local dev:** Start the API on **port 8801** (`start-backend.sh`). The Vite dev server is on **8080** and proxies `/api` and `/health` to the API. Do not set `VITE_API_URL` unless you intentionally call a remote API. Optional: set `VITE_UI_PORT` / `VITE_DEV_PROXY_TARGET` in `frontend/.env.local`.

**CloudCost AI™ chat:** Add `GROQ_API_KEY` to your `.env` (free key from [Groq Console](https://console.groq.com/keys)). Without it, chat returns a configuration error instead of a reply.

**Empty instance list:** Run `python scripts/seed_demo_cloud_data.py` after migrations, or use `./setup-local.sh` (seeds when the DB has fewer than 50 instances).

### Documentation & API contract

- **Technical docs index:** [docs/README.md](docs/README.md)
- **API overview (routes + patterns):** [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Repo layout:** [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md)
- **OpenAPI 3.1 JSON:** [docs/openapi.json](docs/openapi.json) (run `python scripts/export_openapi.py` after route changes)

Interactive docs on a running server: `/docs`, `/redoc`, `/openapi.json`.

### Verify before deploy

```bash
chmod +x scripts/verify_local.sh   # once
./scripts/verify_local.sh
```

Runs `pytest`, frontend ESLint, and a production Vite build.

### Deploy to Render (Free Tier)

After testing locally:

```bash
git push origin main
```

Then go to Render dashboard → Click **"Deploy latest commit"**

See `doc/DEPLOY_TO_RENDER.md` for detailed instructions.

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Redis** - High-performance caching
- **SQLAlchemy** - Powerful ORM
- **Celery** - Background job processing

### Frontend
- **React** - Component-based UI
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Beautiful data visualizations

## Project Structure

```
cloudcost-optimizer/
├── src/              # Backend source code
│   ├── api/          # FastAPI routes
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   └── core/         # Core utilities
├── frontend/         # React frontend
│   ├── src/
│   │   ├── pages/    # React pages
│   │   └── components/
│   └── public/
├── doc/              # Documentation
├── scripts/          # Utility scripts
├── setup-local.sh    # Local setup script
├── start-backend.sh  # Start backend
├── start-frontend.sh # Start frontend
└── test-local.sh     # Test everything
```

## Documentation

All documentation is in the `doc/` directory:

- **[START_HERE.md](doc/START_HERE.md)** - Begin here!
- **[QUICK_START.md](doc/QUICK_START.md)** - 5-minute quick start
- **[LOCAL_DEVELOPMENT.md](doc/LOCAL_DEVELOPMENT.md)** - Complete local dev guide
- **[DEPLOY_TO_RENDER.md](doc/DEPLOY_TO_RENDER.md)** - Deployment guide
- **[RENDER_QUICKSTART.md](doc/RENDER_QUICKSTART.md)** - Quick deployment

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Podman** - [Install](https://podman.io/getting-started/installation)
- **Node.js 18+** - [Download](https://nodejs.org/)

### Installing Podman (macOS)
```bash
brew install podman
podman machine init
podman machine start
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
DEBUG=true
ENVIRONMENT=development

# Database (Local Podman)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/cloudcost

# Redis (Local Podman)
REDIS_URL=redis://localhost:6379/0

# AWS (Optional - for real pricing data)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

## Development Workflow

### Daily Development
```bash
# Start containers
podman start cloudcost-postgres cloudcost-redis

# Activate virtual environment
source venv/bin/activate

# Start backend (auto-reload enabled)
./start-backend.sh

# Start frontend (in another terminal)
./start-frontend.sh
```

### After Code Changes
```bash
# Backend: Auto-reloads with --reload flag
# Frontend: Auto-reloads with Vite HMR

# If database models change:
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Before Committing
```bash
# Test locally first!
./test-local.sh

# If all tests pass:
git add .
git commit -m "Your message"
git push origin main
```

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8801/docs
- **ReDoc**: http://localhost:8801/redoc

## Key Endpoints

- `GET /health` - Health check
- `GET /api/v1/instances` - List cloud instances
- `GET /api/v1/instances/compare` - Compare instances
- `POST /api/v1/recommendations` - Get cost optimization recommendations
- `GET /api/v1/pricing/spot/history` - Spot price history
- `POST /api/v1/ai/chat` - AI-powered cost analysis

## Testing

```bash
# Run all tests
./test-local.sh

# Backend tests (when implemented)
pytest

# Frontend tests
cd frontend && npm test

# Code quality
ruff check src/
black src/
cd frontend && npm run lint
```

## Troubleshooting

### Podman Issues
```bash
# Check if podman machine is running
podman machine list

# Start podman machine
podman machine start

# Check running containers
podman ps

# View container logs
podman logs cloudcost-postgres
podman logs cloudcost-redis
```

### Port Already in Use
```bash
# Find and kill process
lsof -ti:8801 | xargs kill -9
lsof -ti:8080 | xargs kill -9
```

### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
podman exec -it cloudcost-postgres psql -U postgres -c "DROP DATABASE cloudcost; CREATE DATABASE cloudcost;"
alembic upgrade head
```

See `doc/LOCAL_DEVELOPMENT.md` for detailed troubleshooting.

## Deployment

### Render (Recommended - Free Tier)

1. Test locally: `./test-local.sh`
2. Push to GitHub: `git push origin main`
3. Go to Render dashboard
4. Click **"Deploy latest commit"**

**Cost: $0/month** (free tier)

See `doc/DEPLOY_TO_RENDER.md` for complete guide.

## Production Features

✅ **Security**
- Password hashing with bcrypt
- JWT authentication
- CORS protection
- XSS prevention
- SQL injection prevention

✅ **Performance**
- Redis caching
- Database connection pooling
- Async/await throughout
- Query optimization

✅ **Monitoring**
- Structured JSON logging
- Request/response logging
- Health check endpoints
- Error tracking

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Test locally: `./test-local.sh`
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Create Pull Request

## License

MIT License - see LICENSE file for details

## Support

- 📖 Documentation: `doc/` directory
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

## Roadmap

- [ ] Support for Azure and GCP
- [ ] Cost forecasting with ML
- [ ] Slack/Email notifications
- [ ] Team collaboration features
- [ ] Kubernetes cost optimization
- [ ] Reserved instance recommendations

---

**Made with ❤️ for cloud cost optimization**

**Star this repo if you find it useful!** ⭐
