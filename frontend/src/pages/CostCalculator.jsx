import { useState, useMemo, useEffect } from 'react'
import { 
  Calculator, 
  DollarSign, 
  Clock, 
  Calendar,
  Server,
  TrendingDown,
  Info,
  Loader2
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

export default function CostCalculator() {
  const [config, setConfig] = useState({
    provider: 'aws',
    instanceType: '',
    count: 3,
    hoursPerDay: 24,
    daysPerMonth: 30,
    pricingStrategy: 'on_demand',
  })

  const [allInstances, setAllInstances] = useState([])
  const [loading, setLoading] = useState(true)

  // Fetch all instances from API
  useEffect(() => {
    const fetchInstances = async () => {
      try {
        setLoading(true)
        const response = await api.getMulticloudInstances({ limit: 5000 })
        setAllInstances(response.data.instances)
        
        // Set default instance type for selected provider
        const providerInstances = response.data.instances.filter(i => i.provider === config.provider)
        if (providerInstances.length > 0 && !config.instanceType) {
          setConfig(prev => ({ ...prev, instanceType: providerInstances[0].instance_type }))
        }
      } catch (error) {
        console.error('Failed to fetch instances:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchInstances()
  }, [])

  // Get instances for selected provider
  const instances = useMemo(() => {
    return allInstances
      .filter(i => i.provider === config.provider)
      .sort((a, b) => {
        // Sort by vCPUs, then memory
        if (a.vcpus !== b.vcpus) return a.vcpus - b.vcpus
        return a.memory_gb - b.memory_gb
      })
  }, [allInstances, config.provider])

  // Get current instance details
  const currentInstance = useMemo(() => {
    return instances.find(i => i.instance_type === config.instanceType)
  }, [instances, config.instanceType])

  const costs = useMemo(() => {
    if (!currentInstance) return null

    const hoursPerMonth = config.hoursPerDay * config.daysPerMonth
    let baseHourlyRate = currentInstance.hourly_price || 0
    let isEstimated = false

    // If no pricing data, estimate based on instance specs
    if (baseHourlyRate === 0 && currentInstance.vcpus && currentInstance.memory_gb) {
      isEstimated = true
      // Rough estimation: $0.04 per vCPU + $0.005 per GB RAM (typical AWS pricing)
      baseHourlyRate = (currentInstance.vcpus * 0.04) + (currentInstance.memory_gb * 0.005)
      
      // Adjust based on category
      if (currentInstance.category === 'compute_optimized') {
        baseHourlyRate *= 1.1  // Compute optimized slightly more expensive
      } else if (currentInstance.category === 'memory_optimized') {
        baseHourlyRate *= 1.3  // Memory optimized more expensive
      } else if (currentInstance.category === 'storage_optimized') {
        baseHourlyRate *= 1.2
      }
    }
    
    // Apply discounts based on pricing strategy
    // Spot: ~60% discount, Reserved 1yr: ~35% discount, Reserved 3yr: ~55% discount
    const discountMultipliers = {
      'on_demand': 1.0,
      'spot': 0.4,
      'reserved_1yr': 0.65,
      'reserved_3yr': 0.45,
    }
    
    const hourlyRate = baseHourlyRate * discountMultipliers[config.pricingStrategy]
    const hourly = hourlyRate * config.count
    const monthly = hourly * hoursPerMonth
    const annual = monthly * 12

    // Compare with on-demand
    const onDemandMonthly = baseHourlyRate * config.count * hoursPerMonth
    const savings = onDemandMonthly - monthly
    const savingsPercent = (savings / onDemandMonthly) * 100

    return {
      hourly: hourly.toFixed(4),
      daily: (hourly * config.hoursPerDay).toFixed(2),
      monthly: monthly.toFixed(2),
      annual: annual.toFixed(2),
      savings: savings.toFixed(2),
      savingsPercent: savingsPercent.toFixed(1),
      hoursPerMonth,
      isEstimated,
    }
  }, [config, currentInstance])

  // Projection data for chart
  const projectionData = useMemo(() => {
    if (!costs) return []
    
    const monthly = parseFloat(costs.monthly)
    return Array.from({ length: 12 }, (_, i) => ({
      month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
      cost: monthly,
      cumulative: monthly * (i + 1),
    }))
  }, [costs])

  const strategyLabels = {
    on_demand: 'On-Demand',
    spot: 'Spot',
    reserved_1yr: '1-Year Reserved',
    reserved_3yr: '3-Year Reserved',
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Calculator className="w-8 h-8 text-orange-400" />
          Cost Calculator
        </h1>
        <p className="text-slate-400 mt-2">
          Calculate and project your cloud infrastructure costs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration */}
        <div className="lg:col-span-1">
          <div className="glass-card p-6 space-y-6 sticky top-8">
            <h2 className="text-lg font-semibold text-white">Configuration</h2>

            {/* Provider */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Cloud Provider</label>
              <div className="flex gap-2">
                {['aws', 'gcp', 'azure'].map((provider) => (
                  <button
                    key={provider}
                    onClick={() => {
                      const providerInstances = allInstances.filter(i => i.provider === provider)
                      setConfig({ 
                      ...config, 
                      provider,
                        instanceType: providerInstances.length > 0 ? providerInstances[0].instance_type : ''
                      })
                    }}
                    className={`
                      flex-1 py-2 rounded-lg border transition-all
                      ${config.provider === provider 
                        ? 'bg-slate-800 border-primary-500/50' 
                        : 'border-slate-700 hover:border-slate-600'
                      }
                    `}
                  >
                    <CloudBadge provider={provider} size="sm" showIcon={false} />
                  </button>
                ))}
              </div>
            </div>

            {/* Instance Type */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">
                Instance Type
                {loading && <Loader2 className="inline-block w-3 h-3 ml-2 animate-spin" />}
              </label>
              {loading ? (
                <div className="input-field flex items-center justify-center text-slate-400">
                  Loading instances...
                </div>
              ) : (
              <select
                value={config.instanceType}
                onChange={(e) => setConfig({ ...config, instanceType: e.target.value })}
                className="input-field"
              >
                {instances.map(inst => (
                    <option key={inst.instance_type} value={inst.instance_type}>
                      {inst.instance_type} ({inst.vcpus} vCPUs, {inst.memory_gb}GB RAM)
                    </option>
                ))}
              </select>
              )}
              <p className="text-xs text-slate-500 mt-1">
                {instances.length} instances available for {config.provider.toUpperCase()}
              </p>
            </div>

            {/* Instance Count */}
            <div>
              <label className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                <Server className="w-4 h-4" />
                Number of Instances
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={config.count}
                onChange={(e) => setConfig({ ...config, count: parseInt(e.target.value) || 1 })}
                className="input-field"
              />
            </div>

            {/* Hours per Day */}
            <div>
              <label className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                <Clock className="w-4 h-4" />
                Hours per Day
              </label>
              <input
                type="range"
                min="1"
                max="24"
                value={config.hoursPerDay}
                onChange={(e) => setConfig({ ...config, hoursPerDay: parseInt(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>1 hr</span>
                <span className="font-medium text-white">{config.hoursPerDay} hours</span>
                <span>24 hr</span>
              </div>
            </div>

            {/* Days per Month */}
            <div>
              <label className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                <Calendar className="w-4 h-4" />
                Days per Month
              </label>
              <input
                type="range"
                min="1"
                max="31"
                value={config.daysPerMonth}
                onChange={(e) => setConfig({ ...config, daysPerMonth: parseInt(e.target.value) })}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>1 day</span>
                <span className="font-medium text-white">{config.daysPerMonth} days</span>
                <span>31 days</span>
              </div>
            </div>

            {/* Pricing Strategy */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Pricing Strategy</label>
              <select
                value={config.pricingStrategy}
                onChange={(e) => setConfig({ ...config, pricingStrategy: e.target.value })}
                className="input-field"
              >
                <option value="on_demand">On-Demand</option>
                <option value="spot">Spot / Preemptible</option>
                <option value="reserved_1yr">1-Year Reserved</option>
                <option value="reserved_3yr">3-Year Reserved</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center">
              <Loader2 className="w-12 h-12 text-blue-400 animate-spin mb-4" />
              <p className="text-slate-400">Loading instances...</p>
            </div>
          ) : !costs ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center">
              <Server className="w-12 h-12 text-slate-600 mb-4" />
              <p className="text-slate-400">Select an instance type to calculate costs</p>
            </div>
          ) : (
            <>
              {/* Estimated Pricing Notice */}
              {costs.isEstimated && (
                <div className="glass-card p-4 border-yellow-500/30 bg-yellow-500/5">
                  <div className="flex items-center gap-2">
                    <Info className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                    <p className="text-sm text-yellow-200">
                      <span className="font-semibold">Estimated Pricing:</span> These costs are estimated based on instance specifications. 
                      {config.provider === 'aws' && ' AWS pricing data will be available once API credentials are configured.'}
                    </p>
                  </div>
                </div>
              )}

              {/* Cost Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4">
                  <p className="text-xs text-slate-400 mb-1">Hourly</p>
                  <p className="text-2xl font-bold text-white">${costs.hourly}</p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-slate-400 mb-1">Daily</p>
                  <p className="text-2xl font-bold text-white">${costs.daily}</p>
                </div>
                <div className="glass-card p-4 border-primary-500/30">
                  <p className="text-xs text-slate-400 mb-1">Monthly</p>
                  <p className="text-2xl font-bold text-primary-400">${costs.monthly}</p>
                </div>
                <div className="glass-card p-4">
                  <p className="text-xs text-slate-400 mb-1">Annual</p>
                  <p className="text-2xl font-bold text-white">${costs.annual}</p>
                </div>
              </div>

              {/* Savings */}
              {config.pricingStrategy !== 'on_demand' && parseFloat(costs.savings) > 0 && (
                <div className="glass-card p-6 border-green-500/30 bg-green-500/5">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-green-500/20">
                      <TrendingDown className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">
                        Savings vs On-Demand ({strategyLabels[config.pricingStrategy]})
                      </p>
                      <p className="text-2xl font-bold text-green-400">
                        ${costs.savings}/mo <span className="text-lg">({costs.savingsPercent}%)</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Breakdown */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Cost Breakdown</h3>
                <div className="space-y-3">
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Instance Type</span>
                    <span className="text-white font-mono">{config.instanceType}</span>
                  </div>
                  {currentInstance && (
                    <>
                      <div className="flex justify-between py-2 border-b border-slate-800">
                        <span className="text-slate-400">vCPUs</span>
                        <span className="text-white">{currentInstance.vcpus}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-slate-800">
                        <span className="text-slate-400">Memory</span>
                        <span className="text-white">{currentInstance.memory_gb} GB</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-slate-800">
                        <span className="text-slate-400">Category</span>
                        <span className="text-white capitalize">{currentInstance.category?.replace('_', ' ')}</span>
                      </div>
                    </>
                  )}
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Number of Instances</span>
                    <span className="text-white">{config.count}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Hours per Month</span>
                    <span className="text-white">{costs.hoursPerMonth} hrs</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Pricing Strategy</span>
                    <span className="text-white">{strategyLabels[config.pricingStrategy]}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Provider</span>
                    <CloudBadge provider={config.provider} size="sm" />
                  </div>
                </div>
              </div>

              {/* Projection Chart */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">12-Month Projection</h3>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={projectionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="month" tick={{ fill: '#94a3b8' }} />
                      <YAxis tick={{ fill: '#94a3b8' }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1e293b', 
                          border: '1px solid #334155',
                          borderRadius: '0.5rem',
                        }}
                        formatter={(value) => [`$${value.toFixed(2)}`, '']}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="cost" 
                        stroke="#0ea5e9" 
                        strokeWidth={2}
                        name="Monthly Cost"
                        dot={false}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="cumulative" 
                        stroke="#8b5cf6" 
                        strokeWidth={2}
                        name="Cumulative"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="mt-4 p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-start gap-2">
                    <Info className="w-5 h-5 text-slate-400 mt-0.5" />
                    <div className="text-sm text-slate-400">
                      <p>Total projected cost over 12 months: <span className="text-white font-semibold">${costs.annual}</span></p>
                      {config.pricingStrategy !== 'on_demand' && (
                        <p className="text-green-400 mt-1">
                          Annual savings: ${(parseFloat(costs.savings) * 12).toFixed(2)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

