import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Cloud, 
  DollarSign, 
  Server, 
  TrendingDown, 
  ArrowRight,
  Sparkles,
  Zap,
  Shield
} from 'lucide-react'
import StatsCard from '../components/StatsCard'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

export default function Dashboard() {
  const [selectedCloud, setSelectedCloud] = useState('all')
  const [stats, setStats] = useState([
    { title: 'Instance Types', value: '...', subtitle: 'Across all clouds', icon: Server },
    { title: 'Max Savings', value: '90%', subtitle: 'With Spot instances', icon: TrendingDown, trend: 'up', trendValue: 'vs On-Demand' },
    { title: 'Regions', value: '...', subtitle: 'Global coverage', icon: Cloud },
    { title: 'Updated', value: 'Real-time', subtitle: 'Pricing data', icon: Zap },
  ])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const provider = selectedCloud === 'all' ? null : selectedCloud
        const response = await api.get('/api/v1/multicloud/stats', {
          params: provider ? { provider } : {}
        })
        const data = response.data
        
        setStats([
          { 
            title: 'Instance Types', 
            value: data.total_instances.toLocaleString(), 
            subtitle: selectedCloud === 'all' 
              ? `AWS: ${data.by_provider.aws || 0}, GCP: ${data.by_provider.gcp || 0}, Azure: ${data.by_provider.azure || 0}` 
              : `${selectedCloud.toUpperCase()} instances`,
            icon: Server 
          },
          { 
            title: 'Max Savings', 
            value: '90%', 
            subtitle: 'With Spot instances', 
            icon: TrendingDown, 
            trend: 'up', 
            trendValue: 'vs On-Demand' 
          },
          { 
            title: 'Regions', 
            value: `${data.total_regions}+`, 
            subtitle: 'Global coverage', 
            icon: Cloud 
          },
          { 
            title: 'Updated', 
            value: 'Real-time', 
            subtitle: 'Pricing data', 
            icon: Zap 
          },
        ])
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        setLoading(false)
      }
    }
    
    fetchStats()
  }, [selectedCloud])

  const features = [
    {
      icon: Sparkles,
      title: 'Smart Recommendations',
      description: 'AI-powered suggestions based on your workload requirements',
      link: '/recommendations',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Server,
      title: 'Instance Finder',
      description: 'Search and filter 1200+ instance types across AWS, GCP, and Azure',
      link: '/instances',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: DollarSign,
      title: 'Price Comparison',
      description: 'Compare costs across clouds and find the best deals',
      link: '/compare',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: Shield,
      title: 'Spot Analysis',
      description: 'Track spot prices and interruption risks',
      link: '/spot-intelligence',
      color: 'from-orange-500 to-amber-500',
    },
  ]

  const [quickCompare, setQuickCompare] = useState([])

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const response = await api.compareCloudPricing(2, 8)
        const data = response.data.comparison
        
        const compareData = []
        for (const [provider, info] of Object.entries(data)) {
          if (provider !== 'cheapest_overall' && info.available) {
            compareData.push({
              provider,
              instance: info.cheapest_instance,
              price: info.hourly_price,
              region: info.region
            })
          }
        }
        setQuickCompare(compareData)
      } catch (error) {
        console.error('Failed to fetch comparison:', error)
        // Fallback to sample data
        setQuickCompare([
          { provider: 'aws', instance: 'm5.large', price: 0.096, region: 'us-east-1' },
          { provider: 'gcp', instance: 'n2-standard-2', price: 0.097, region: 'us-central1' },
          { provider: 'azure', instance: 'Standard_D2s_v4', price: 0.096, region: 'eastus' },
        ])
      }
    }
    
    fetchComparison()
  }, [])

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 via-purple-500/20 to-pink-500/20 blur-3xl -z-10" />
        <div className="text-center py-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Cloud Cost <span className="bg-gradient-to-r from-primary-400 to-purple-400 bg-clip-text text-transparent">Optimizer</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Find the most cost-effective cloud instances across AWS, GCP, and Azure.
            Save up to 90% on your cloud infrastructure costs.
          </p>
          
          {/* Cloud provider buttons */}
          <div className="flex items-center justify-center gap-3 mt-8">
            {['all', 'aws', 'gcp', 'azure'].map((cloud) => (
              <button
                key={cloud}
                onClick={() => setSelectedCloud(cloud)}
                className={`
                  px-4 py-2 rounded-xl font-medium transition-all duration-200
                  ${selectedCloud === cloud 
                    ? 'bg-slate-800 text-white border border-slate-700' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }
                `}
              >
                {cloud === 'all' ? '🌐 All Clouds' : <CloudBadge provider={cloud} size="sm" />}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <StatsCard key={stat.title} {...stat} className="animate-slide-up" style={{ animationDelay: `${index * 100}ms` }} />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, index) => (
          <Link
            key={feature.title}
            to={feature.link}
            className="glass-card p-6 group card-hover animate-slide-up"
            style={{ animationDelay: `${(index + 4) * 100}ms` }}
          >
            <div className="flex items-start gap-4">
              <div className={`flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} shadow-lg`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white group-hover:text-primary-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-400 mt-1">
                  {feature.description}
                </p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-primary-400 group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Compare Table */}
      <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '800ms' }}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Quick Comparison: 2 vCPU, 8GB RAM</h2>
          <Link to="/compare" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
            View detailed comparison <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b border-slate-800">
                <th className="pb-3 text-sm font-medium text-slate-400">Provider</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Instance Type</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Region</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Hourly</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Monthly</th>
              </tr>
            </thead>
            <tbody>
              {quickCompare.map((item, index) => (
                <tr key={item.provider} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                  <td className="py-4">
                    <CloudBadge provider={item.provider} size="sm" />
                  </td>
                  <td className="py-4 font-mono text-sm text-white">{item.instance}</td>
                  <td className="py-4 text-sm text-slate-400">{item.region}</td>
                  <td className="py-4 text-sm text-white">${item.price.toFixed(3)}</td>
                  <td className="py-4 text-sm font-semibold text-white">${(item.price * 730).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
          <p className="text-sm text-green-400">
            💡 <strong>Tip:</strong> These are On-Demand prices. You can save up to 60% with Reserved Instances or 90% with Spot!
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="relative overflow-hidden glass-card p-8 text-center animate-slide-up" style={{ animationDelay: '900ms' }}>
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 via-purple-500/10 to-pink-500/10" />
        <div className="relative">
          <h2 className="text-2xl font-bold text-white mb-3">Ready to optimize your cloud costs?</h2>
          <p className="text-slate-400 mb-6 max-w-lg mx-auto">
            Get personalized recommendations based on your specific workload requirements.
          </p>
          <Link to="/recommendations" className="btn-primary inline-flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Get Recommendations
          </Link>
        </div>
      </div>
    </div>
  )
}

