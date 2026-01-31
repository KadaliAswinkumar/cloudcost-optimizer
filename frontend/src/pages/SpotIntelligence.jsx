import { useState, useEffect } from 'react'
import { 
  Zap, 
  DollarSign, 
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  BarChart3,
  MapPin,
  Info,
  Calculator,
  Clock,
  TrendingUp
} from 'lucide-react'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

export default function SpotIntelligence() {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    provider: 'aws',
    instance_type: 'm5.xlarge',
    region: '',
    hours_per_month: 730
  })

  const handleAnalyze = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await api.analyzeSpotInstance({
        provider: formData.provider,
        instance_type: formData.instance_type,
        region: formData.region || null,
        hours_per_month: parseInt(formData.hours_per_month)
      })
      
      setAnalysis(response)
    } catch (err) {
      console.error('Error analyzing spot instance:', err)
      setError(err.response?.data?.detail || 'Failed to analyze spot instance')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level) => {
    const colors = {
      low: 'text-green-400',
      medium: 'text-yellow-400',
      high: 'text-red-400'
    }
    return colors[level] || 'text-slate-400'
  }

  const getRiskIcon = (level) => {
    if (level === 'low') return <CheckCircle2 className="w-5 h-5" />
    if (level === 'medium') return <AlertTriangle className="w-5 h-5" />
    return <AlertTriangle className="w-5 h-5" />
  }

  const getRiskBadge = (level) => {
    const styles = {
      low: 'bg-green-500/10 text-green-400 border-green-500/20',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      high: 'bg-red-500/10 text-red-400 border-red-500/20'
    }
    return styles[level] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 mb-4">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium text-yellow-300">Save 70-90% with Spot</span>
        </div>
        <h1 className="text-4xl font-bold text-white mb-3">
          <span className="bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
            Spot Intelligence™
          </span>
        </h1>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto">
          Predict interruption risk and maximize savings with intelligent spot instance analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-1">
          <form onSubmit={handleAnalyze} className="glass-card p-6 space-y-6 sticky top-6">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Calculator className="w-5 h-5 text-yellow-400" />
              Analyze Spot Instance
            </h2>

            {/* Provider */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Cloud Provider
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['aws', 'gcp', 'azure'].map((provider) => (
                  <button
                    key={provider}
                    type="button"
                    onClick={() => setFormData({ ...formData, provider })}
                    className={`
                      px-3 py-2 rounded-lg border transition-all
                      ${formData.provider === provider
                        ? 'bg-slate-800 border-yellow-500/50'
                        : 'border-slate-700 opacity-50 hover:opacity-100'
                      }
                    `}
                  >
                    <CloudBadge provider={provider} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            {/* Instance Type */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Instance Type
              </label>
              <input
                type="text"
                value={formData.instance_type}
                onChange={(e) => setFormData({ ...formData, instance_type: e.target.value })}
                placeholder="e.g., m5.xlarge"
                className="input-field font-mono"
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                AWS: m5, c5, r5 | GCP: n2, e2, c2 | Azure: D, E, F-series
              </p>
            </div>

            {/* Region (Optional) */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Region (Optional)
              </label>
              <input
                type="text"
                value={formData.region}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                placeholder="Leave empty for all regions"
                className="input-field"
              />
            </div>

            {/* Usage Hours */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Usage (hours/month)
              </label>
              <input
                type="number"
                min="1"
                max="730"
                value={formData.hours_per_month}
                onChange={(e) => setFormData({ ...formData, hours_per_month: e.target.value })}
                className="input-field"
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                730 = 24/7 | 168 = 8hrs/day | 40 = 8hrs/weekday
              </p>
            </div>

            {/* Analyze Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Analyze Spot Pricing
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="glass-card p-6 border-l-4 border-red-500">
              <div className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-400 mb-1">Error</h3>
                  <p className="text-sm text-slate-300">{error}</p>
                </div>
              </div>
            </div>
          )}

          {!analysis && !loading && !error && (
            <div className="glass-card p-12 text-center">
              <Zap className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Ready to save money?</h3>
              <p className="text-slate-400 mb-4">
                Enter an instance type to analyze spot pricing and interruption risk
              </p>
              <div className="grid grid-cols-3 gap-4 text-left max-w-md mx-auto">
                <div className="p-4 rounded-lg bg-slate-800/30">
                  <div className="text-2xl font-bold text-yellow-400 mb-1">70-90%</div>
                  <div className="text-xs text-slate-400">Typical Savings</div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/30">
                  <div className="text-2xl font-bold text-green-400 mb-1">5-10%</div>
                  <div className="text-xs text-slate-400">Low Risk Interruptions</div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/30">
                  <div className="text-2xl font-bold text-blue-400 mb-1">Real-time</div>
                  <div className="text-xs text-slate-400">Pricing Analysis</div>
                </div>
              </div>
            </div>
          )}

          {analysis && (
            <>
              {/* Smart Recommendation (NEW!) */}
              {analysis.recommendation && (
                <div className="glass-card p-6 border-l-4 border-yellow-500">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-500/20 to-orange-500/20 flex items-center justify-center flex-shrink-0">
                      <Zap className="w-6 h-6 text-yellow-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-white mb-2">
                        💡 Our Recommendation
                      </h3>
                      <p className="text-slate-300 mb-4 leading-relaxed">
                        {analysis.recommendation.reasoning}
                      </p>
                      <div className="flex items-center gap-4">
                        <div className="px-4 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                          <span className="text-sm text-slate-400">Save </span>
                          <span className="text-lg font-bold text-yellow-400">
                            ${analysis.recommendation.estimated_monthly_savings?.toFixed(0)}/month
                          </span>
                        </div>
                        <div className="px-4 py-2 rounded-lg bg-slate-800/50">
                          <span className="text-sm text-slate-400">Annually: </span>
                          <span className="text-lg font-bold text-white">
                            ${analysis.recommendation.estimated_annual_savings?.toFixed(0)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Pricing Comparison: All Options (NEW!) */}
              {analysis.recommendation?.all_options && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-purple-400" />
                    Complete Pricing Comparison
                  </h3>
                  <p className="text-sm text-slate-400 mb-6">
                    Compare all pricing options to find the best fit for your workload
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(analysis.recommendation.all_options).map(([key, option]) => {
                      const isRecommended = key === analysis.recommendation.recommended_option
                      const isSpot = key === 'spot'
                      const isOnDemand = key === 'on_demand'
                      
                      return (
                        <div
                          key={key}
                          className={`
                            relative p-5 rounded-lg border transition-all
                            ${isRecommended 
                              ? 'border-yellow-500 bg-gradient-to-br from-yellow-500/10 to-orange-500/10 ring-2 ring-yellow-500/20' 
                              : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                            }
                          `}
                        >
                          {isRecommended && (
                            <div className="absolute -top-3 left-4 px-3 py-1 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 text-xs font-bold text-slate-900">
                              ⭐ RECOMMENDED
                            </div>
                          )}

                          <div className="mb-3">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="text-base font-semibold text-white capitalize">
                                {key.replace('_', ' ')}
                              </h4>
                              {isSpot && option.risk && (
                                <span className={`text-xs px-2 py-1 rounded ${getRiskBadge(option.risk)}`}>
                                  {option.risk} risk
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400">
                              {option.commitment}
                            </div>
                          </div>

                          <div className="mb-4">
                            <div className="text-3xl font-bold text-white mb-1">
                              ${option.monthly_cost?.toFixed(0)}
                            </div>
                            <div className="text-xs text-slate-500">per month</div>
                            {!isOnDemand && (
                              <div className="mt-2 text-sm">
                                <span className="text-green-400 font-semibold">
                                  {option.savings_percent?.toFixed(0)}% off
                                </span>
                                <span className="text-slate-500"> · Save </span>
                                <span className="text-white font-medium">
                                  ${option.savings_amount?.toFixed(0)}/mo
                                </span>
                              </div>
                            )}
                          </div>

                          <div className="space-y-3 mb-4">
                            <div>
                              <div className="text-xs font-semibold text-green-400 mb-1.5">Pros:</div>
                              <ul className="space-y-1">
                                {option.pros?.map((pro, idx) => (
                                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-1.5">
                                    <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0 mt-0.5" />
                                    <span>{pro}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-red-400 mb-1.5">Cons:</div>
                              <ul className="space-y-1">
                                {option.cons?.map((con, idx) => (
                                  <li key={idx} className="text-xs text-slate-400 flex items-start gap-1.5">
                                    <AlertTriangle className="w-3 h-3 text-red-500/70 flex-shrink-0 mt-0.5" />
                                    <span>{con}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          <div className="pt-3 border-t border-slate-700">
                            <div className="text-xs text-slate-400 mb-1">Best for:</div>
                            <div className="text-xs text-slate-300">{option.best_for}</div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Savings Summary */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingDown className="w-5 h-5 text-green-400" />
                  Spot Savings Potential
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20">
                    <div className="text-xs text-slate-400 mb-1">Monthly Savings</div>
                    <div className="text-3xl font-bold text-green-400">
                      ${analysis.spot_analysis?.savings?.monthly_amount?.toFixed(0)}
                    </div>
                    <div className="text-xs text-green-400 mt-1">
                      {analysis.spot_analysis?.savings?.percent?.toFixed(0)}% off on-demand
                    </div>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-slate-800/50">
                    <div className="text-xs text-slate-400 mb-1">Annual Savings</div>
                    <div className="text-2xl font-bold text-white">
                      ${analysis.spot_analysis?.savings?.annual_amount?.toFixed(0)}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Over 12 months
                    </div>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-slate-800/50">
                    <div className="text-xs text-slate-400 mb-1">Avg Spot Price</div>
                    <div className="text-2xl font-bold text-white">
                      ${analysis.spot_analysis?.average?.monthly?.toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      vs ${analysis.on_demand?.monthly?.toFixed(2)} on-demand
                    </div>
                  </div>
                </div>
              </div>

              {/* Interruption Risk */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  Interruption Risk Analysis
                </h3>

                <div className="flex items-center gap-4 mb-4">
                  <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${getRiskBadge(analysis.spot_analysis?.risk?.level)}`}>
                    <span className={getRiskColor(analysis.spot_analysis?.risk?.level)}>
                      {getRiskIcon(analysis.spot_analysis?.risk?.level)}
                    </span>
                    <span className="font-semibold uppercase">
                      {analysis.spot_analysis?.risk?.level} Risk
                    </span>
                  </div>
                  <div className="text-sm text-slate-300">
                    {analysis.spot_analysis?.risk?.description}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/30 mb-4">
                  <div className="text-sm text-slate-400 mb-2">Price Volatility</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-white">
                      {analysis.spot_analysis?.volatility?.percent?.toFixed(1)}%
                    </span>
                    <span className="text-sm text-slate-500">
                      Standard deviation: ${analysis.spot_analysis?.volatility?.value?.toFixed(4)}
                    </span>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border ${getRiskBadge(analysis.spot_analysis?.risk?.level)}`}>
                  <div className="flex items-start gap-2">
                    <Info className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-medium mb-1">Recommendation</div>
                      <div className="text-sm">
                        {analysis.spot_analysis?.risk?.recommendation}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Best Regions */}
              {analysis.spot_analysis?.best_regions?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-400" />
                    Best Regions for Spot
                  </h3>

                  <div className="space-y-3">
                    {analysis.spot_analysis.best_regions.slice(0, 5).map((region, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className={`
                            w-8 h-8 rounded-full flex items-center justify-center font-bold
                            ${idx === 0 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-700 text-slate-400'}
                          `}>
                            {idx + 1}
                          </div>
                          <div>
                            <div className="font-medium text-white">{region.region}</div>
                            <div className="text-xs text-slate-400">
                              ${region.hourly}/hour · ${region.monthly}/month
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-green-400">
                            {region.savings_vs_ondemand}%
                          </div>
                          <div className="text-xs text-slate-500">savings</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Price Range */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-400" />
                  Price Range Analysis
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-slate-800/30">
                    <div className="text-xs text-slate-400 mb-2">Minimum Spot Price</div>
                    <div className="text-xl font-bold text-white">
                      ${analysis.spot_analysis?.range?.min_hourly}/hr
                    </div>
                    <div className="text-sm text-slate-500">
                      ${analysis.spot_analysis?.range?.min_monthly}/mo
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-800/30">
                    <div className="text-xs text-slate-400 mb-2">Maximum Spot Price</div>
                    <div className="text-xl font-bold text-white">
                      ${analysis.spot_analysis?.range?.max_hourly}/hr
                    </div>
                    <div className="text-sm text-slate-500">
                      ${analysis.spot_analysis?.range?.max_monthly}/mo
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-800/30">
                    <div className="text-xs text-slate-400 mb-2">Average Spot Price</div>
                    <div className="text-xl font-bold text-white">
                      ${analysis.spot_analysis?.average?.hourly}/hr
                    </div>
                    <div className="text-sm text-slate-500">
                      ${analysis.spot_analysis?.average?.monthly}/mo
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-800/30">
                    <div className="text-xs text-slate-400 mb-2">On-Demand Price</div>
                    <div className="text-xl font-bold text-white">
                      ${analysis.on_demand?.hourly}/hr
                    </div>
                    <div className="text-sm text-slate-500">
                      ${analysis.on_demand?.monthly}/mo
                    </div>
                  </div>
                </div>
              </div>

              {/* Instance Details */}
              {analysis.instance_details && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Instance Specifications</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">vCPUs</div>
                      <div className="text-lg font-bold text-white">{analysis.instance_details.vcpus}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Memory</div>
                      <div className="text-lg font-bold text-white">{analysis.instance_details.memory_gb} GB</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Architecture</div>
                      <div className="text-sm font-medium text-white capitalize">{analysis.instance_details.processor_architecture}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Category</div>
                      <div className="text-sm font-medium text-white capitalize">
                        {analysis.instance_details.category?.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
