# CloudCost Optimizer - README

A smart, AI-powered cloud cost optimization platform that helps you analyze, compare, and reduce your AWS cloud spending.

## Features

- **Multi-Cloud Comparison**: Compare instance types across AWS regions
- **AI-Powered Recommendations**: Get intelligent cost-saving suggestions
- **Spot Instance Intelligence**: Analyze spot pricing trends and interruption risks
- **Real-time Price Analysis**: Live AWS pricing data integration
- **Interactive Dashboard**: Beautiful, modern UI with real-time metrics

## Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **PostgreSQL** - Robust relational database
- **Redis** - High-performance caching
- **SQLAlchemy** - Powerful ORM
- **Alembic** - Database migrations
- **Celery** - Background job processing

### Frontend
- **React** - Component-based UI library
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Beautiful data visualizations
- **Axios** - HTTP client

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+

### Backend Setup
```bash
# Clone the repo
git clone <your-repo-url>
cd cloudcost-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn src.api.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Deployment

### Deploy to Render (Recommended - Free Tier)

**No credit card required!**

1. Read the comprehensive guide: `DEPLOY_TO_RENDER.md`
2. Or follow the quick start: `RENDER_QUICKSTART.md`
3. Total setup time: ~10 minutes

**What you get:**
- ✅ Free backend hosting
- ✅ Free frontend hosting
- ✅ Free PostgreSQL (90 days)
- ✅ Auto-deploy on git push
- ✅ HTTPS enabled
- ✅ Custom domain support

### Alternative Deployment Options
- Railway (requires credit card)
- Vercel (frontend) + Railway (backend)
- AWS Amplify
- DigitalOcean App Platform

## Project Structure

```
cloudcost-optimizer/
├── src/
│   ├── api/           # FastAPI routes & endpoints
│   ├── core/          # Core utilities (config, cache, database)
│   ├── models/        # SQLAlchemy ORM models
│   ├── services/      # Business logic services
│   └── jobs/          # Background job tasks
├── frontend/
│   ├── src/
│   │   ├── pages/     # React page components
│   │   ├── components/# Reusable UI components
│   │   ├── context/   # React Context (auth, etc.)
│   │   └── api/       # API client
│   └── public/        # Static assets
├── alembic/           # Database migrations
├── tests/             # Test suite
└── requirements.txt   # Python dependencies
```

## API Documentation

Once the backend is running, visit:
- **Interactive Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## Key Endpoints

- `GET /health` - Health check
- `GET /api/v1/instances` - List cloud instances
- `GET /api/v1/instances/compare` - Compare instances
- `POST /api/v1/recommendations` - Get cost optimization recommendations
- `GET /api/v1/pricing/spot/history` - Spot price history
- `POST /api/v1/ai/chat` - AI-powered cost analysis

## Environment Variables

See `.env.example` for all available configuration options.

**Critical variables for production:**
- `SECRET_KEY` - Generate with: `openssl rand -base64 32`
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CORS_ORIGINS` - Allowed frontend URLs (comma-separated)
- `DEBUG` - Set to `false` in production
- `ENVIRONMENT` - Set to `production`

## Features in Detail

### 1. Price Comparison
Compare cloud instance costs across:
- Multiple AWS regions
- Different instance families
- On-demand vs Spot pricing
- Real-time price updates

### 2. AI Recommendations
Get intelligent suggestions based on:
- Current workload requirements
- Budget constraints
- Performance needs
- Risk tolerance for spot instances

### 3. Spot Intelligence
Analyze spot instances with:
- Historical price trends
- Interruption frequency data
- Best availability zones
- Risk-adjusted pricing

### 4. Dashboard Analytics
Monitor your optimization with:
- Total savings potential
- Active recommendations
- Cost trends over time
- Instance utilization metrics

## Development

### Run Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test
```

### Code Quality
```bash
# Backend linting
ruff check src/
black src/

# Frontend linting
cd frontend && npm run lint
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Production Considerations

### Security
- ✅ All passwords hashed with bcrypt
- ✅ JWT-based authentication
- ✅ CORS properly configured
- ✅ XSS protection enabled
- ✅ SQL injection prevention (ORM)
- ✅ Sensitive data masking in logs

### Performance
- ✅ Redis caching for frequently accessed data
- ✅ Database query optimization
- ✅ Connection pooling
- ✅ Async/await throughout
- ✅ Background job processing with Celery

### Monitoring
- ✅ Structured JSON logging
- ✅ Request/response logging middleware
- ✅ Health check endpoints
- ✅ Error tracking and reporting

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Check Redis is running: `redis-cli ping`
- Verify environment variables in `.env`
- Check logs: `tail -f logs/app.log`

### Frontend can't connect to backend
- Verify `VITE_API_URL` in `frontend/.env`
- Check backend is running: `curl http://localhost:8000/health`
- Check browser console for CORS errors
- Verify `CORS_ORIGINS` includes frontend URL

### Database migration errors
- Rollback: `alembic downgrade -1`
- Check database connection
- Verify PostgreSQL version compatibility
- Check migration files for syntax errors

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- 📧 Email: support@cloudcost-optimizer.com
- 📖 Docs: See `DEPLOY_TO_RENDER.md`
- 🐛 Issues: GitHub Issues tab
- 💬 Discussions: GitHub Discussions tab

## Roadmap

- [ ] Support for Azure and GCP
- [ ] Cost forecasting with ML
- [ ] Slack/Email notifications
- [ ] Team collaboration features
- [ ] Custom cost rules engine
- [ ] Kubernetes cost optimization
- [ ] Reserved instance recommendations

## Acknowledgments

- AWS Pricing API for real-time data
- OpenAI for AI recommendations
- Render for free hosting
- Open source community

---

Made with ❤️ by the CloudCost Optimizer team

**Star this repo if you find it useful!** ⭐
