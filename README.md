# ☁️ CloudCost Optimizer

> **Multi-Cloud Instance Price Optimizer & Recommender**

A production-ready full-stack application that helps you find the most cost-effective cloud instances across **AWS, Google Cloud Platform (GCP), and Microsoft Azure**. Built with modern technologies and deployed with GitHub Pages.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![React](https://img.shields.io/badge/React-18.2-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7-red.svg)

---

## 🌐 Live Demo

**👉 [View Live Application](https://kadaliaswinkumar.github.io/cloudcost-optimizer/)**

---

## ✨ Features

### Core Capabilities

- **🌐 Multi-Cloud Support** - Compare instances across AWS, GCP, and Azure in one place
- **📊 Instance Discovery** - Browse and filter 700+ instance types across all major clouds
- **💰 Cross-Cloud Comparison** - Find the cheapest option across providers for your workload
- **🤖 Smart Recommendations** - Intelligent recommendations considering all cloud options
- **🔄 Instance Mapping** - Find equivalent instances across different cloud providers
- **📈 Spot Analysis** - Track spot/preemptible prices and interruption risks
- **🛡️ Interruption Risk Analysis** - Real-time risk scoring based on historical volatility
- **📉 Cost Projection** - Project costs over time with different scenarios
- **⚡ Real-time Updates** - Background jobs keep pricing data fresh
- **🎨 Modern React UI** - Beautiful dashboard built with React + Tailwind CSS

### Supported Cloud Providers

| Provider | Instance Types | Regions | Spot Support |
|----------|---------------|---------|--------------|
| **AWS** | EC2 (600+ types) | 17 regions | ✅ Spot Instances |
| **GCP** | Compute Engine (50+ types) | 28 regions | ✅ Preemptible/Spot VMs |
| **Azure** | Virtual Machines (60+ types) | 34 regions | ✅ Spot VMs |

### Pricing Strategies Analyzed

| Strategy | AWS | GCP | Azure | Savings |
|----------|-----|-----|-------|---------|
| **On-Demand** | ✅ | ✅ | ✅ | Baseline |
| **Reserved/Committed 1-Year** | ✅ | ✅ CUD | ✅ | Up to 40% |
| **Reserved/Committed 3-Year** | ✅ | ✅ CUD | ✅ | Up to 60% |
| **Spot/Preemptible** | ✅ | ✅ | ✅ | Up to 90% |

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                     CloudCost Optimizer (Multi-Cloud)                  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────┐    ┌────────────┐    ┌──────────────────────────────┐ │
│  │  FastAPI   │───▶│   Redis    │───▶│     Background Jobs          │ │
│  │   Server   │    │   Cache    │    │     (Celery + Beat)          │ │
│  └────────────┘    └────────────┘    └──────────────────────────────┘ │
│        │                                          │                    │
│        ▼                                          ▼                    │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                        PostgreSQL                               │   │
│  │  • Cloud Instances (AWS/GCP/Azure)  • Pricing Data              │   │
│  │  • Cross-Cloud Mappings  • Recommendations                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                     Cloud Provider APIs                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │  AWS APIs    │  │  GCP APIs    │  │    Azure APIs        │  │   │
│  │  │  • Pricing   │  │  • Compute   │  │    • Retail Prices   │  │   │
│  │  │  • EC2       │  │  • Billing   │  │    • Compute         │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Tech Stack

### Frontend
- **React 18** - Modern UI framework
- **Tailwind CSS** - Utility-first styling
- **Vite** - Lightning-fast build tool
- **React Router** - Client-side routing
- **Recharts** - Data visualization
- **Axios** - HTTP client

### Backend
- **FastAPI 0.109** - Async REST API framework
- **PostgreSQL 16** - Persistent data storage
- **Redis 7** - Caching & rate limiting
- **Celery** - Background job processing
- **SQLAlchemy 2.0** - Async database operations
- **Pydantic 2.5** - Request/response validation
- **Boto3** - AWS API integration

### DevOps
- **Podman/Docker** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **GitHub Pages** - Static site hosting
- **Alembic** - Database migrations

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Podman or Docker
- PostgreSQL (or use Docker)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/cloudcost-optimizer.git
cd cloudcost-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Start with Podman

```bash
# Start all services
podman-compose up -d

# Check status
podman-compose ps

# View logs
podman-compose logs -f api
```

### 3. Start the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🌐 Fetching Real Cloud Data

By default, the application includes sample pricing data. To fetch **real, live pricing** from AWS, GCP, and Azure:

### Quick Setup (Local)

```bash
# 1. Set up AWS credentials in .env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# 2. Run the data fetcher
python fetch_real_data.py
```

This will fetch:
- ✅ **600+ AWS EC2 instances** from AWS Pricing API
- ✅ **50+ GCP Compute Engine instances** from public APIs (no credentials needed)
- ✅ **60+ Azure VM instances** from public APIs (no credentials needed)

**Fetch time**: 10-15 minutes for the first run.

### AWS Credentials Setup

1. **Create AWS Free Account**: https://aws.amazon.com/free (credit card required but won't be charged)
2. **Create IAM User** in AWS Console with **AWSPriceListServiceFullAccess** policy
3. **Generate Access Keys** for the IAM user
4. **Add credentials** to `.env` file

📖 **Detailed guide**: See [SETUP_REAL_DATA.md](./SETUP_REAL_DATA.md)

### For Render Deployment

1. Go to Render Dashboard → your **cloudcost-api** service
2. Add environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
3. Open Shell tab and run:
```bash
python -c "from src.jobs.price_updater import update_all_prices; update_all_prices()"
```

**Note**: AWS Pricing API is **100% FREE**. No charges for reading pricing data!

---

## 📚 API Documentation

### Key Endpoints

```bash
# Multi-cloud recommendations
POST /api/v1/multicloud/recommendations
{
    "min_vcpus": 4,
    "min_memory_gb": 16,
    "providers": ["aws", "gcp", "azure"],
    "workload_type": "steady",
    "spot_eligible": true,
    "hours_per_month": 730,
    "max_monthly_budget": 200
}

# List instances across clouds
GET /api/v1/multicloud/instances?min_vcpus=4&min_memory=8

# Compare instance pricing
GET /api/v1/multicloud/pricing/compare?vcpus=4&memory_gb=16

# Find equivalent instances
GET /api/v1/multicloud/compare/m5.large?provider=aws
```

For complete API documentation, visit `/docs` endpoint when running locally.

---

## 🧪 Testing

```bash
# Run quick tests
./quick_test.sh

# Run full integration tests
./integration_test.sh

# Run specific tests
pytest tests/test_api.py -v
```

---

## 🚢 Deployment

### GitHub Pages (Frontend Only)

The frontend is automatically deployed to GitHub Pages on every push to main branch.

1. Enable GitHub Pages in repository settings
2. Push to main branch
3. Access at: `https://YOUR_USERNAME.github.io/cloudcost-optimizer/`

### Full Stack Deployment

For deploying the complete application with backend, see `DEPLOYMENT_GUIDE.md`.

Recommended platforms:
- **Render.com** - Free tier with PostgreSQL & Redis
- **Railway.app** - $5/month credit
- **Fly.io** - Free tier available

---

## 📊 Project Structure

```
cloudcost-optimizer/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── pages/        # Dashboard, Recommendations, etc.
│   │   ├── components/   # Reusable UI components
│   │   └── api/          # API client
│   ├── package.json
│   └── vite.config.js
├── src/                  # Backend application
│   ├── api/              # FastAPI routes
│   ├── services/         # Business logic & cloud integrations
│   ├── models/           # Database models
│   ├── jobs/             # Celery background tasks
│   └── core/             # Configuration & utilities
├── tests/                # Test suite
├── alembic/              # Database migrations
├── docker-compose.yml    # Container orchestration
└── requirements.txt      # Python dependencies
```

---

## 💡 Key Features Explained

### Multi-Cloud Recommendations

The application analyzes pricing across all major cloud providers and provides:
- Cost comparison across AWS, GCP, and Azure
- Equivalent instance mapping
- Spot/preemptible instance analysis
- Risk-based recommendations
- Real-time pricing data

### Interruption Risk Analysis

For Spot/Preemptible instances, the system calculates:
- Historical price volatility (30-day rolling)
- Price trend detection
- Frequency of price spikes
- Risk scores (0-100)
- Bid strategy recommendations

### Cost Optimization

Recommendations consider:
- On-Demand vs Reserved vs Spot pricing
- Regional pricing variations
- Instance family characteristics
- Workload patterns
- Budget constraints

---

## 🎯 Use Cases

1. **Cost Optimization** - Find the cheapest instances for your workload across clouds
2. **Cloud Migration** - Compare costs when moving between cloud providers
3. **Budget Planning** - Project monthly costs with different scenarios
4. **Instance Selection** - Choose the right instance type based on requirements
5. **Spot Analysis** - Evaluate risk vs savings for spot instances

---

## 📝 Documentation

- `RUNNING_WITH_PODMAN.md` - Complete setup guide with Podman
- `DEPLOYMENT_GUIDE.md` - Deploy to various platforms
- `TEST_CASES.md` - Comprehensive testing guide
- `QUICK_REFERENCE.md` - Command reference
- `ACCESS_POINTS.md` - UI and API access guide

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details

---

## 👨‍💻 Author

**Aswin Kumar**

Built as a comprehensive full-stack project showcasing:
- Modern web development practices
- Cloud infrastructure knowledge
- System architecture design
- API integration skills
- DevOps & deployment expertise

---

## 🙏 Acknowledgments

- Cloud pricing data from AWS, GCP, and Azure public APIs
- Open source community for amazing tools and libraries
- FastAPI and React communities for excellent documentation

---

## 📞 Contact

For questions or feedback:
- GitHub: [@KadaliAswinkumar](https://github.com/KadaliAswinkumar)
- Project Link: [https://github.com/KadaliAswinkumar/cloudcost-optimizer](https://github.com/KadaliAswinkumar/cloudcost-optimizer)

---

**Built with ❤️ for cloud cost optimization**
