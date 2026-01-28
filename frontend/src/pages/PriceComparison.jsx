import { useState, useEffect } from 'react'
import { 
  GitCompare, 
  ArrowRight,
  DollarSign,
  TrendingDown,
  Check,
  Info,
  Loader2
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

export default function PriceComparison() {
  const [specs, setSpecs] = useState({ vcpus: 4, memory_gb: 16 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [comparisonData, setComparisonData] = useState([])

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await api.compareCloudPricing(specs.vcpus, specs.memory_gb)
        const data = response.data.comparison
        
        const formattedData = []
        
        for (const [provider, info] of Object.entries(data)) {
          if (provider !== 'cheapest_overall' && info.available) {
            // Base on-demand price
            const onDemandMonthly = Math.round(info.monthly_price)
            
            // Estimate other pricing models based on typical cloud discounts
            const spotPrice = Math.round(onDemandMonthly * 0.30) // ~70% discount
            const reserved1yr = Math.round(onDemandMonthly * 0.65) // ~35% discount
            const reserved3yr = Math.round(onDemandMonthly * 0.50) // ~50% discount
            
            formattedData.push({
              provider,
              name: provider.toUpperCase(),
              instance: info.cheapest_instance,
              onDemand: onDemandMonthly,
              spot: spotPrice,
              reserved1yr: reserved1yr,
              reserved3yr: reserved3yr,
              region: info.region,
              color: provider === 'aws' ? '#FF9900' : provider === 'gcp' ? '#4285F4' : '#0078D4',
            })
          }
        }
        
        // Sort by on-demand price
        formattedData.sort((a, b) => a.onDemand - b.onDemand)
        
        setComparisonData(formattedData)
        setLoading(false)
      } catch (err) {
        console.error('Failed to fetch comparison:', err)
        setError('Failed to load pricing comparison')
        setLoading(false)
      }
    }
    
    fetchComparison()
  }, [specs.vcpus, specs.memory_gb])

  const chartData = comparisonData.map(item => ({
    name: item.name,
    'On-Demand': item.onDemand,
    'Spot': item.spot,
    '1-Year Reserved': item.reserved1yr,
    '3-Year Reserved': item.reserved3yr,
  }))

  const cheapest = comparisonData.length > 0 ? comparisonData.reduce((min, item) => 
    item.onDemand < min.onDemand ? item : min
  , comparisonData[0]) : null

  const maxSavings = comparisonData.length > 2 ? Math.round((1 - comparisonData[0].spot / comparisonData[2].onDemand) * 100) : 0

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <GitCompare className="w-8 h-8 text-green-400" />
          Compare Clouds
        </h1>
        <p className="text-slate-400 mt-2">
          Side-by-side pricing comparison across AWS, GCP, and Azure.
        </p>
      </div>

      {/* Spec Selector */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Select Instance Specifications</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm text-slate-400 mb-2 block">vCPUs</label>
            <select
              value={specs.vcpus}
              onChange={(e) => setSpecs({ ...specs, vcpus: parseInt(e.target.value) })}
              className="input-field"
            >
              {[1, 2, 4, 8, 16, 32, 64].map(v => (
                <option key={v} value={v}>{v} vCPUs</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-2 block">Memory (GB)</label>
            <select
              value={specs.memory_gb}
              onChange={(e) => setSpecs({ ...specs, memory_gb: parseInt(e.target.value) })}
              className="input-field"
            >
              {[1, 2, 4, 8, 16, 32, 64, 128].map(m => (
                <option key={m} value={m}>{m} GB</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="glass-card p-12 text-center">
          <Loader2 className="w-12 h-12 text-primary-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading pricing comparison...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="glass-card p-6 border-red-500/30 bg-red-500/5">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {!loading && !error && comparisonData.length > 0 && (
        <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-6 border-green-500/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Cheapest Provider</span>
            <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">BEST</span>
          </div>
          <div className="flex items-center gap-3">
            <CloudBadge provider={cheapest.provider} size="md" />
            <div>
              <p className="text-2xl font-bold text-white">${cheapest.onDemand}/mo</p>
              <p className="text-xs text-slate-500">On-Demand</p>
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Max Potential Savings</span>
            <TrendingDown className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-2xl font-bold text-green-400">{maxSavings}%</p>
          <p className="text-xs text-slate-500">With GCP Spot vs Azure On-Demand</p>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Comparing</span>
            <Info className="w-5 h-5 text-slate-500" />
          </div>
          <p className="text-2xl font-bold text-white">{specs.vcpus} vCPU, {specs.memory_gb}GB</p>
          <p className="text-xs text-slate-500">Similar instances across clouds</p>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Monthly Cost Comparison</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94a3b8' }} tickFormatter={(v) => `$${v}`} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8' }} width={60} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '0.5rem',
                }}
                formatter={(value) => [`$${value}/mo`, '']}
              />
              <Bar dataKey="On-Demand" fill="#64748b" radius={[0, 4, 4, 0]} />
              <Bar dataKey="Spot" fill="#22c55e" radius={[0, 4, 4, 0]} />
              <Bar dataKey="1-Year Reserved" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              <Bar dataKey="3-Year Reserved" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-6 mt-4">
          {[
            { label: 'On-Demand', color: 'bg-slate-500' },
            { label: 'Spot', color: 'bg-green-500' },
            { label: '1-Year Reserved', color: 'bg-blue-500' },
            { label: '3-Year Reserved', color: 'bg-purple-500' },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded ${item.color}`} />
              <span className="text-sm text-slate-400">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Comparison Table */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Detailed Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="pb-4 text-left text-sm font-medium text-slate-400">Provider</th>
                <th className="pb-4 text-left text-sm font-medium text-slate-400">Instance</th>
                <th className="pb-4 text-right text-sm font-medium text-slate-400">On-Demand</th>
                <th className="pb-4 text-right text-sm font-medium text-slate-400">Spot</th>
                <th className="pb-4 text-right text-sm font-medium text-slate-400">1-Yr Reserved</th>
                <th className="pb-4 text-right text-sm font-medium text-slate-400">3-Yr Reserved</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {comparisonData.map((item) => (
                <tr key={item.provider} className="hover:bg-slate-800/30">
                  <td className="py-4">
                    <CloudBadge provider={item.provider} />
                  </td>
                  <td className="py-4 font-mono text-sm text-white">{item.instance}</td>
                  <td className="py-4 text-right">
                    <span className="text-white">${item.onDemand}</span>
                    <span className="text-slate-500">/mo</span>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-green-400">${item.spot}</span>
                    <span className="text-slate-500">/mo</span>
                    <span className="ml-2 text-xs text-green-400">
                      -{Math.round((1 - item.spot/item.onDemand) * 100)}%
                    </span>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-blue-400">${item.reserved1yr}</span>
                    <span className="text-slate-500">/mo</span>
                    <span className="ml-2 text-xs text-blue-400">
                      -{Math.round((1 - item.reserved1yr/item.onDemand) * 100)}%
                    </span>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-purple-400">${item.reserved3yr}</span>
                    <span className="text-slate-500">/mo</span>
                    <span className="ml-2 text-xs text-purple-400">
                      -{Math.round((1 - item.reserved3yr/item.onDemand) * 100)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendation */}
      <div className="glass-card p-6 border-green-500/20 bg-green-500/5">
        <div className="flex items-start gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-green-500/20">
            <Check className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Our Recommendation</h3>
            <p className="text-slate-300">
              For <strong>{specs.vcpus} vCPUs and {specs.memory_gb}GB RAM</strong>, 
              we recommend <CloudBadge provider="gcp" size="sm" /> <strong>e2-standard-4</strong> 
              {' '}as the most cost-effective option at <strong>${cheapest.onDemand}/month</strong>.
            </p>
            <p className="text-slate-400 text-sm mt-2">
              💡 If your workload can tolerate interruptions, consider Spot instances for up to {maxSavings}% savings.
            </p>
          </div>
        </div>
      </div>
      </>
      )}
    </div>
  )
}

