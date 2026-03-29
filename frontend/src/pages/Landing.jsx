import { Link } from 'react-router-dom'
import { 
  ArrowRight, 
  Sparkles, 
  Zap, 
  Shield, 
  TrendingDown,
  Cloud,
  CheckCircle2,
  BarChart3,
  DollarSign,
  Cpu,
  Globe,
  Brain,
  LineChart
} from 'lucide-react'

export default function Landing() {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Recommendations',
      description: 'Get intelligent instance recommendations based on your workload with our advanced AI engine.',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: Zap,
      title: 'Spot Intelligence™',
      description: 'Predict interruption risk and maximize savings with real-time spot pricing analysis.',
      gradient: 'from-yellow-500 to-orange-500'
    },
    {
      icon: Globe,
      title: 'Multi-Cloud Comparison',
      description: 'Compare AWS, GCP, and Azure pricing instantly to find the best deals across clouds.',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: TrendingDown,
      title: 'Cost Optimization',
      description: 'Reduce your cloud costs by up to 90% with our advanced optimization algorithms.',
      gradient: 'from-green-500 to-emerald-500'
    },
    {
      icon: BarChart3,
      title: 'Real-Time Analytics',
      description: 'Track pricing trends, interruption rates, and cost savings in real-time dashboards.',
      gradient: 'from-indigo-500 to-purple-500'
    },
    {
      icon: Shield,
      title: 'Risk Assessment',
      description: 'Understand interruption risks and choose the right balance between cost and reliability.',
      gradient: 'from-red-500 to-orange-500'
    }
  ]

  const stats = [
    { value: '70-90%', label: 'Cost Savings', icon: DollarSign },
    { value: '3 Clouds', label: 'Supported', icon: Cloud },
    { value: '5000+', label: 'Instances', icon: Cpu },
    { value: 'Real-Time', label: 'Pricing Data', icon: LineChart }
  ]

  const benefits = [
    'Compare 5000+ instance types across AWS, GCP, and Azure',
    'Real-time spot pricing and interruption risk analysis',
    'AI-powered recommendations tailored to your workload',
    'Save 70-90% on compute costs with intelligent optimization',
    'Track historical pricing trends and make data-driven decisions',
    'Get instant multi-cloud cost comparisons'
  ]

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-40 -left-40 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
          <div className="absolute bottom-0 right-1/3 w-80 h-80 bg-yellow-500/20 rounded-full blur-3xl animate-pulse delay-2000" />
        </div>

        {/* Navigation */}
        <nav className="relative z-10 container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <Cloud className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">CloudCost Optimizer</h1>
                <p className="text-xs text-slate-400">AI-Powered Cloud Savings</p>
              </div>
            </div>
            
            <Link
              to="/login"
              className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium transition-all shadow-lg shadow-purple-500/25"
            >
              Sign In
            </Link>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-6 py-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 mb-6">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-purple-300">Reduce Cloud Costs by 70-90%</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Optimize Your <br />
            <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Cloud Costs
            </span>
            <br />
            with AI
          </h1>

          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-10 leading-relaxed">
            Compare 5000+ instances across AWS, GCP, and Azure. Get AI-powered recommendations, 
            real-time spot pricing, and intelligent cost optimization strategies.
          </p>

          <div className="flex items-center justify-center gap-4 mb-16">
            <Link
              to="/signup"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold text-lg flex items-center gap-2 transition-all shadow-2xl shadow-purple-500/30"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            
            <a
              href="#features"
              className="px-8 py-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-lg transition-all"
            >
              Learn More
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, idx) => (
              <div 
                key={idx} 
                className="glass-card p-6 text-center"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <stat.icon className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Everything You Need to <span className="text-purple-400">Save Money</span>
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Powerful tools and insights to optimize your cloud infrastructure costs
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="glass-card p-8 group hover:border-purple-500/30 transition-all duration-300"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} bg-opacity-10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Why Choose Us */}
      <div className="bg-slate-800/50 py-20">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-white mb-6">
                Why CloudCost Optimizer?
              </h2>
              <p className="text-lg text-slate-300 mb-8">
                Stop overpaying for cloud resources. Our AI-powered platform analyzes thousands of 
                instance configurations across AWS, GCP, and Azure to find you the perfect balance 
                between cost, performance, and reliability.
              </p>
              
              <div className="space-y-4">
                {benefits.map((benefit, idx) => (
                  <div key={idx} className="flex items-start gap-3 animate-fade-in" style={{ animationDelay: `${idx * 100}ms` }}>
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center mt-0.5">
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    </div>
                    <span className="text-slate-300">{benefit}</span>
                  </div>
                ))}
              </div>

              <Link
                to="/signup"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-purple-500 hover:bg-purple-600 text-white font-medium mt-8 transition-all"
              >
                Start Optimizing Now
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>

            <div className="relative">
              <div className="glass-card p-8">
                <div className="space-y-4">
                  {/* Mock UI Preview */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-700/50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center">
                        <Zap className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">AWS m5.xlarge</div>
                        <div className="text-xs text-slate-400">Spot Instance</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-400">-87%</div>
                      <div className="text-xs text-slate-500">savings</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-700/50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                        <Cloud className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">GCP n2-standard-4</div>
                        <div className="text-xs text-slate-400">On-Demand</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">$124/mo</div>
                      <div className="text-xs text-slate-500">cheapest</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-700/50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        <Brain className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">AI Recommendation</div>
                        <div className="text-xs text-slate-400">Best for your workload</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-purple-400">Spot</div>
                      <div className="text-xs text-slate-500">low risk</div>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-300">Monthly Savings</span>
                      <span className="text-2xl font-bold text-green-400">$2,847</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating badge */}
              <div className="absolute -top-4 -right-4 px-4 py-2 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 text-sm font-bold text-slate-900 shadow-lg">
                Save 90%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="glass-card p-12 text-center relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-cyan-500/10" />
          
          <div className="relative z-10">
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to Slash Your Cloud Costs?
            </h2>
            <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
              Join thousands of companies saving millions on cloud infrastructure. 
              Start optimizing your costs today - completely free.
            </p>
            
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold text-lg transition-all shadow-2xl shadow-purple-500/30"
            >
              <Sparkles className="w-5 h-5" />
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Link>

            <p className="text-sm text-slate-500 mt-4">
              No credit card required • Free forever • Full access to all features
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <Cloud className="w-5 h-5 text-white" />
              </div>
              <span className="text-slate-400 text-sm">
                © 2026 CloudCost Optimizer. All rights reserved.
              </span>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="#features" className="hover:text-white transition-colors">Features</a>
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
