import { useState, useMemo } from 'react'
import { 
  Calculator, 
  DollarSign, 
  Clock, 
  Calendar,
  Server,
  TrendingDown,
  Info
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import CloudBadge from '../components/CloudBadge'

export default function CostCalculator() {
  const [config, setConfig] = useState({
    provider: 'aws',
    instanceType: 'm5.large',
    count: 3,
    hoursPerDay: 24,
    daysPerMonth: 30,
    pricingStrategy: 'on_demand',
  })

  // Mock pricing data
  const instancePricing = {
    aws: {
      'm5.large': { onDemand: 0.096, spot: 0.038, reserved1yr: 0.060, reserved3yr: 0.043 },
      'm5.xlarge': { onDemand: 0.192, spot: 0.077, reserved1yr: 0.121, reserved3yr: 0.086 },
      't3.large': { onDemand: 0.0832, spot: 0.025, reserved1yr: 0.052, reserved3yr: 0.037 },
    },
    gcp: {
      'e2-standard-2': { onDemand: 0.067, spot: 0.020, reserved1yr: 0.042, reserved3yr: 0.030 },
      'e2-standard-4': { onDemand: 0.134, spot: 0.040, reserved1yr: 0.085, reserved3yr: 0.060 },
      'n2-standard-2': { onDemand: 0.097, spot: 0.029, reserved1yr: 0.061, reserved3yr: 0.044 },
    },
    azure: {
      'Standard_D2s_v4': { onDemand: 0.096, spot: 0.034, reserved1yr: 0.062, reserved3yr: 0.043 },
      'Standard_D4s_v4': { onDemand: 0.192, spot: 0.067, reserved1yr: 0.125, reserved3yr: 0.086 },
      'Standard_B2s': { onDemand: 0.042, spot: 0.013, reserved1yr: 0.027, reserved3yr: 0.019 },
    },
  }

  const instances = Object.keys(instancePricing[config.provider])

  const costs = useMemo(() => {
    const pricing = instancePricing[config.provider][config.instanceType]
    if (!pricing) return null

    const hoursPerMonth = config.hoursPerDay * config.daysPerMonth
    const hourlyRate = pricing[config.pricingStrategy === 'on_demand' ? 'onDemand' : 
                               config.pricingStrategy === 'spot' ? 'spot' :
                               config.pricingStrategy === 'reserved_1yr' ? 'reserved1yr' : 'reserved3yr']

    const hourly = hourlyRate * config.count
    const monthly = hourly * hoursPerMonth
    const annual = monthly * 12

    // Compare with on-demand
    const onDemandMonthly = pricing.onDemand * config.count * hoursPerMonth
    const savings = onDemandMonthly - monthly
    const savingsPercent = (savings / onDemandMonthly) * 100

    return {
      hourly: hourly.toFixed(2),
      daily: (hourly * config.hoursPerDay).toFixed(2),
      monthly: monthly.toFixed(2),
      annual: annual.toFixed(2),
      savings: savings.toFixed(2),
      savingsPercent: savingsPercent.toFixed(1),
      hoursPerMonth,
    }
  }, [config])

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
                    onClick={() => setConfig({ 
                      ...config, 
                      provider,
                      instanceType: Object.keys(instancePricing[provider])[0]
                    })}
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
              <label className="text-sm text-slate-400 mb-2 block">Instance Type</label>
              <select
                value={config.instanceType}
                onChange={(e) => setConfig({ ...config, instanceType: e.target.value })}
                className="input-field"
              >
                {instances.map(inst => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
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
          {costs && (
            <>
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

