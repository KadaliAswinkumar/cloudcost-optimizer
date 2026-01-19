# CloudCost Optimizer - Frontend

A beautiful, modern React dashboard for the CloudCost Optimizer multi-cloud price comparison platform.

## 🎨 Features

- **Dashboard** - Overview of cloud costs with quick stats
- **Get Recommendations** - AI-powered instance recommendations form
- **Instance Finder** - Search and filter 700+ instance types
- **Compare Clouds** - Side-by-side AWS vs GCP vs Azure comparison
- **Cost Calculator** - Interactive cost projections with charts

## 🛠️ Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool (fast!)
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Recharts** - Charts and visualizations
- **Lucide React** - Icons
- **Axios** - API client

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at **http://localhost:3000**

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js        # API client and endpoints
│   ├── components/
│   │   ├── Layout.jsx       # Main layout with sidebar
│   │   ├── CloudBadge.jsx   # Provider badges (AWS/GCP/Azure)
│   │   ├── StatsCard.jsx    # Statistics display cards
│   │   └── RecommendationCard.jsx
│   ├── pages/
│   │   ├── Dashboard.jsx    # Home page
│   │   ├── Recommendations.jsx
│   │   ├── InstanceFinder.jsx
│   │   ├── PriceComparison.jsx
│   │   └── CostCalculator.jsx
│   ├── App.jsx              # Main app with routing
│   ├── main.jsx             # Entry point
│   └── index.css            # Tailwind + custom styles
├── public/
│   └── cloud.svg            # Favicon
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## 🎯 Screenshots

### Dashboard
- Hero section with cloud provider selector
- Stats cards (Instance types, Max savings, Regions)
- Quick comparison table
- Feature cards with navigation

### Recommendations
- Form with vCPU, Memory, Budget inputs
- Cloud provider toggles
- Workload type selector
- Results with ranking and scores

### Instance Finder
- Search bar with filters
- Provider filter buttons
- Category dropdown
- Sortable table with pricing

### Price Comparison
- Spec selector (vCPUs, Memory)
- Bar chart comparison
- Detailed pricing table
- AI recommendation box

### Cost Calculator
- Interactive sliders for usage
- Pricing strategy selector
- Cost breakdown
- 12-month projection chart

## 🔗 API Integration

The frontend expects the backend API at `http://localhost:8000`. Configure in `.env`:

```
VITE_API_URL=http://localhost:8000
```

## 📝 License

MIT

