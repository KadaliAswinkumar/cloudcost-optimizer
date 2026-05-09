import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  Brain,
  Calculator,
  CheckCircle2,
  Cloud,
  Gauge,
  GitCompare,
  LineChart,
  RadioTower,
  Search,
  Shield,
  Sparkles,
  Target,
  TrendingDown,
  Zap,
} from 'lucide-react'

export default function Landing() {
  const services = [
    {
      icon: Sparkles,
      title: 'AI Recommendations',
      route: '/recommendations',
      description: 'Workload-aware recommendations with savings estimates and confidence context.',
    },
    {
      icon: Zap,
      title: 'Spot Intelligence',
      route: '/spot-intelligence',
      description: 'Interruption-aware spot insights to balance savings and reliability.',
    },
    {
      icon: Search,
      title: 'Instance Finder',
      route: '/instances',
      description: 'Find the best-fit instances across providers by CPU, memory, and architecture.',
    },
    {
      icon: GitCompare,
      title: 'Price Comparison',
      route: '/compare',
      description: 'Cross-cloud price comparison to choose the lowest cost path for each workload.',
    },
    {
      icon: Calculator,
      title: 'Cost Calculator',
      route: '/calculator',
      description: 'Quick compute and scenario cost calculations for planning and procurement.',
    },
    {
      icon: BarChart3,
      title: 'FinOps Intelligence',
      route: '/finops',
      description: 'FOCUS-style analytics, lifecycle workflows, anomalies, and investor-grade KPIs.',
    },
    {
      icon: RadioTower,
      title: 'Infrastructure Intelligence',
      route: '/infra-intelligence',
      description: 'Deep cloud inventory scans with rule-driven findings and optimization briefs.',
    },
    {
      icon: Gauge,
      title: 'Savings Readiness Score',
      route: '/readiness',
      description: 'Execution maturity scoring with a concrete 90-day action plan.',
    },
    {
      icon: Brain,
      title: 'CloudCost AI Assistant',
      route: '/ai',
      description: 'Conversational copilot for cost questions, trade-offs, and decision support.',
    },
  ]

  const pillars = [
    {
      icon: BarChart3,
      title: 'Cost Intelligence (FinOps)',
      description: 'FOCUS-style cost analytics, action lifecycle, confidence scoring, anomalies, and investor reporting in one view.',
    },
    {
      icon: RadioTower,
      title: 'Infrastructure Intelligence',
      description: 'Deep AWS collection (EC2/EKS/RDS/ECS/Lambda/S3) with deterministic rules and optimization briefs.',
    },
    {
      icon: Gauge,
      title: 'Execution Readiness Scoring',
      description: 'New built-in readiness score estimates your ability to convert opportunities into verified realized savings.',
    },
  ]

  const highlights = [
    'Recommendation lifecycle: open -> accepted -> in_progress -> implemented -> verified -> rollback',
    'Anomaly and regression signals to prevent savings decay after optimization',
    'Investor export reports with activation, impact, adoption, and confidence KPIs',
    'Cloud commitment awareness (RI / Savings Plan coverage) in decision support',
    'All onboarding paths: CSV/FOCUS, AWS CUR, Azure export, GCP billing, API push',
    'Single command center for founders, finance, engineering, and operations',
  ]

  const workflow = [
    'Connect billing + cloud sources',
    'Detect opportunities and risks',
    'Prioritize with confidence and blast radius',
    'Execute and track recommendation lifecycle',
    'Verify savings and monitor regressions',
    'Export investor and board-ready reports',
  ]

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-40 -left-40 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <nav className="relative z-10 container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <Cloud className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">CloudCost Optimizer</h1>
                <p className="text-xs text-slate-400">FinOps + CloudOps Execution Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link to="/support" className="px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 text-sm">Support</Link>
              <Link
                to="/login"
                className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium transition-all shadow-lg shadow-purple-500/25"
              >
                Sign In
              </Link>
            </div>
          </div>
        </nav>

        <div className="relative z-10 container mx-auto px-6 py-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 mb-6">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-purple-300">Multi-product cloud efficiency suite in one platform</span>
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            One Platform for <br />
            <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Cloud Cost + Infrastructure Decisions
            </span>
          </h1>

          <p className="text-xl text-slate-300 max-w-4xl mx-auto mb-10 leading-relaxed">
            CloudCost Optimizer brings Recommendations, Spot Intelligence, Instance Finder, Price Comparison,
            Cost Calculator, FinOps dashboards, Infra diagnostics, and investor reporting into one execution system.
          </p>

          <div className="flex items-center justify-center gap-4 mb-10">
            <Link
              to="/signup"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold text-lg flex items-center gap-2 transition-all shadow-2xl shadow-purple-500/30"
            >
              Start Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#platform"
              className="px-8 py-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-lg transition-all"
            >
              Explore Services
            </a>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="glass-card p-4"><p className="text-2xl font-bold text-white">60-70%</p><p className="text-xs text-slate-400">Potential optimization opportunity</p></div>
            <div className="glass-card p-4"><p className="text-2xl font-bold text-white">3</p><p className="text-xs text-slate-400">Intelligence layers in one product</p></div>
            <div className="glass-card p-4"><p className="text-2xl font-bold text-white">5+</p><p className="text-xs text-slate-400">Onboarding paths supported</p></div>
            <div className="glass-card p-4"><p className="text-2xl font-bold text-white">E2E</p><p className="text-xs text-slate-400">Action-to-verification tracking</p></div>
          </div>
        </div>
      </div>

      <div id="platform" className="container mx-auto px-6 py-16">
        <h2 className="text-4xl font-bold text-white text-center mb-12">What You Get in the Product</h2>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5 mb-14">
          {services.map((service) => (
            <div key={service.title} className="glass-card p-6 flex flex-col">
              <service.icon className="w-6 h-6 text-primary-300 mb-3" />
              <h3 className="text-xl font-semibold text-white">{service.title}</h3>
              <p className="text-slate-400 mt-2 flex-1">{service.description}</p>
              <Link to="/login" className="mt-4 text-sm text-primary-300 hover:text-primary-200 inline-flex items-center gap-1">
                Open in app
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ))}
        </div>

        <h2 className="text-4xl font-bold text-white text-center mb-12">Platform Pillars</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {pillars.map((item) => (
            <div key={item.title} className="glass-card p-6">
              <item.icon className="w-7 h-7 text-primary-300 mb-3" />
              <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
              <p className="text-slate-400">{item.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-800/40 py-16">
        <div className="container mx-auto px-6 grid lg:grid-cols-2 gap-8 items-start">
          <div>
            <h2 className="text-3xl font-bold text-white mb-4">What makes this different</h2>
            <p className="text-slate-300 mb-6">
              Most tools stop at recommendations. We continue through execution, verification, and investor-grade outcome reporting.
            </p>
            <div className="space-y-3">
              {highlights.map((point) => (
                <div key={point} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5" />
                  <p className="text-slate-300">{point}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between border border-slate-700 rounded-lg p-3">
              <div className="flex items-center gap-2"><Target className="w-4 h-4 text-emerald-300" /><p className="text-sm text-white">Detected opportunity</p></div>
              <p className="text-emerald-300 font-semibold">$48,700/mo</p>
            </div>
            <div className="flex items-center justify-between border border-slate-700 rounded-lg p-3">
              <div className="flex items-center gap-2"><TrendingDown className="w-4 h-4 text-sky-300" /><p className="text-sm text-white">Verified savings</p></div>
              <p className="text-sky-300 font-semibold">$18,300/mo</p>
            </div>
            <div className="flex items-center justify-between border border-slate-700 rounded-lg p-3">
              <div className="flex items-center gap-2"><Shield className="w-4 h-4 text-amber-300" /><p className="text-sm text-white">Open regressions</p></div>
              <p className="text-amber-300 font-semibold">2 alerts</p>
            </div>
            <p className="text-xs text-slate-500">Illustrative sample output from in-product traction dashboards.</p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-8">
          <div className="glass-card p-6">
            <h3 className="text-2xl font-semibold text-white mb-4">How the platform works end-to-end</h3>
            <div className="space-y-2">
              {workflow.map((step) => (
                <div key={step} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-1" />
                  <p className="text-slate-300">{step}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-card p-6">
            <h3 className="text-2xl font-semibold text-white mb-4">Enterprise-ready trust and governance</h3>
            <div className="space-y-3 text-slate-300">
              <p className="flex items-start gap-2"><Shield className="w-4 h-4 text-sky-300 mt-1" />Role-based access and connector security controls.</p>
              <p className="flex items-start gap-2"><LineChart className="w-4 h-4 text-sky-300 mt-1" />Audit-friendly action logs and KPI history.</p>
              <p className="flex items-start gap-2"><Target className="w-4 h-4 text-sky-300 mt-1" />Investor and board reporting exports built in.</p>
              <p className="mt-4 text-sm text-slate-400">
                Legal and trust center: <Link to="/privacy" className="text-primary-300 hover:text-primary-200">Privacy</Link>,
                {' '}<Link to="/terms" className="text-primary-300 hover:text-primary-200">Terms</Link>, and
                {' '}<Link to="/support" className="text-primary-300 hover:text-primary-200">Support</Link>.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-16">
        <div className="glass-card p-10 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">Built for founders who need proof, fast</h2>
          <p className="text-lg text-slate-300 mb-8 max-w-3xl mx-auto">
            Launch quickly, connect billing data, prioritize actions, and generate investor updates from one operating system.
          </p>
          <Link
            to="/signup"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold text-lg transition-all shadow-2xl shadow-purple-500/30"
          >
            Create Account
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      <footer className="border-t border-slate-800 py-8">
        <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <span className="text-slate-400 text-sm">© 2026 CloudCost Optimizer. All rights reserved.</span>
          <div className="flex items-center gap-6 text-sm text-slate-400">
            <a href="#platform" className="hover:text-white transition-colors">Platform</a>
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link to="/terms" className="hover:text-white transition-colors">Terms</Link>
            <Link to="/support" className="hover:text-white transition-colors">Support</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
