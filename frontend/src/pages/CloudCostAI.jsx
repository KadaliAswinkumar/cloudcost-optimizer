import { useState, useEffect } from 'react'
import { 
  Sparkles, 
  Cpu, 
  MemoryStick, 
  DollarSign, 
  TrendingDown,
  Zap,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Info,
  ArrowRight,
  Award
} from 'lucide-react'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

const workloadIcons = {
  web_app: '🌐',
  database: '🗄️',
  compute_intensive: '⚙️',
  memory_intensive: '💾',
  ml_training: '🤖',
  general: '⚡'
}

export default function CloudCostAI() {
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState(null)
  const [workloadTypes, setWorkloadTypes] = useState([])
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    min_vcpus: 4,
    min_memory_gb: 16,
    workload_type: 'general',
    traffic_pattern: 'steady',
    providers: ['aws', 'gcp', 'azure'],
    max_monthly_budget: '',
    spot_eligible: true,
    limit: 10
  })

  // Fetch workload types on mount
  useEffect(() => {
    const fetchWorkloadTypes = async () => {
      try {
        const response = await api.getWorkloadTypes()
        setWorkloadTypes(response.data.workload_types)
      } catch (err) {
        console.error('Failed to fetch workload types:', err)
      }
    }
    fetchWorkloadTypes()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const requestData = {
        min_vcpus: parseInt(formData.min_vcpus),
        min_memory_gb: parseFloat(formData.min_memory_gb),
        workload_type: formData.workload_type,
        traffic_pattern: formData.traffic_pattern,
        providers: formData.providers.length > 0 ? formData.providers : null,
        spot_eligible: formData.spot_eligible,
        limit: formData.limit
      }
      
      if (formData.max_monthly_budget && formData.max_monthly_budget > 0) {
        requestData.max_monthly_budget = parseFloat(formData.max_monthly_budget)
      }
      
      console.log('Sending AI recommendation request:', requestData)
      const response = await api.getAIRecommendations(requestData)
      console.log('Received AI recommendations:', response.data)
      
      setRecommendations(response.data.data)
    } catch (err) {
      console.error('Error fetching AI recommendations:', err)
      const errorMessage = err.response?.data?.detail || 'Failed to get recommendations. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const toggleProvider = (provider) => {
    setFormData(prev => ({
      ...prev,
      providers: prev.providers.includes(provider)
        ? prev.providers.filter(p => p !== provider)
        : [...prev, provider],
    }))
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 mb-4">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Powered by AI</span>
        </div>
        <h1 className="text-4xl font-bold text-white mb-3">
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            CloudCost AI™
          </span>
        </h1>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto">
          Get intelligent, AI-powered instance recommendations tailored to your exact workload.
          Save up to 70% on cloud costs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-1">
          <form onSubmit={handleSubmit} className="glass-card p-6 space-y-6 sticky top-6">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-400" />
              Your Requirements
            </h2>

            {/* vCPUs */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Minimum vCPUs
              </label>
              <input
                type="number"
                min="1"
                max="256"
                value={formData.min_vcpus}
                onChange={(e) => setFormData({ ...formData, min_vcpus: e.target.value })}
                className="input-field"
                required
              />
            </div>

            {/* Memory */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Minimum Memory (GB)
              </label>
              <input
                type="number"
                min="0.5"
                max="4096"
                step="0.5"
                value={formData.min_memory_gb}
                onChange={(e) => setFormData({ ...formData, min_memory_gb: e.target.value })}
                className="input-field"
                required
              />
            </div>

            {/* Workload Type */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Workload Type
              </label>
              <select
                value={formData.workload_type}
                onChange={(e) => setFormData({ ...formData, workload_type: e.target.value })}
                className="input-field"
              >
                {workloadTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.icon} {type.name}
                  </option>
                ))}
              </select>
              {workloadTypes.find(t => t.id === formData.workload_type) && (
                <p className="text-xs text-slate-400 mt-1">
                  {workloadTypes.find(t => t.id === formData.workload_type).description}
                </p>
              )}
            </div>

            {/* Traffic Pattern */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Traffic Pattern
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['steady', 'variable', 'spiky'].map((pattern) => (
                  <button
                    key={pattern}
                    type="button"
                    onClick={() => setFormData({ ...formData, traffic_pattern: pattern })}
                    className={`
                      px-3 py-2 rounded-lg text-sm font-medium transition-all
                      ${formData.traffic_pattern === pattern
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/50'
                        : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
                      }
                    `}
                  >
                    {pattern.charAt(0).toUpperCase() + pattern.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Cloud Providers */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Cloud Providers
              </label>
              <div className="flex gap-2">
                {['aws', 'gcp', 'azure'].map((provider) => (
                  <button
                    key={provider}
                    type="button"
                    onClick={() => toggleProvider(provider)}
                    className={`
                      flex-1 px-3 py-2 rounded-lg border transition-all
                      ${formData.providers.includes(provider)
                        ? 'bg-slate-800 border-primary-500/50'
                        : 'border-slate-700 opacity-50 hover:opacity-100'
                      }
                    `}
                  >
                    <CloudBadge provider={provider} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            {/* Budget (Optional) */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Max Monthly Budget (Optional)
              </label>
              <input
                type="number"
                min="0"
                step="10"
                placeholder="No limit"
                value={formData.max_monthly_budget}
                onChange={(e) => setFormData({ ...formData, max_monthly_budget: e.target.value })}
                className="input-field"
              />
            </div>

            {/* Spot Eligible */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="spot_eligible"
                checked={formData.spot_eligible}
                onChange={(e) => setFormData({ ...formData, spot_eligible: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500"
              />
              <label htmlFor="spot_eligible" className="text-sm text-slate-300">
                Consider Spot/Preemptible instances (up to 90% savings)
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || formData.providers.length === 0}
              className="btn-primary w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  AI is analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Get AI Recommendations
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
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-400 mb-1">Error</h3>
                  <p className="text-sm text-slate-300">{error}</p>
                </div>
              </div>
            </div>
          )}

          {!recommendations && !loading && !error && (
            <div className="glass-card p-12 text-center">
              <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Ready to optimize?</h3>
              <p className="text-slate-400">
                Fill in your requirements and let our AI find the perfect instances for you.
              </p>
            </div>
          )}

          {recommendations && (
            <>
              {/* Insights Summary */}
              {recommendations.insights && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingDown className="w-5 h-5 text-green-400" />
                    Cost Insights
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="p-4 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-400 mb-1">Cheapest Option</div>
                      <div className="text-2xl font-bold text-green-400">
                        ${recommendations.insights.price_range?.cheapest?.toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-500">per month</div>
                    </div>
                    
                    <div className="p-4 rounded-lg bg-slate-800/50">
                      <div className="text-xs text-slate-400 mb-1">Potential Savings</div>
                      <div className="text-2xl font-bold text-blue-400">
                        {recommendations.insights.savings_potential?.percent?.toFixed(0)}%
                      </div>
                      <div className="text-xs text-slate-500">
                        ${recommendations.insights.savings_potential?.monthly_amount?.toFixed(0)}/mo
                      </div>
                    </div>
                    
                    {recommendations.insights.spot_instance_opportunity?.average_savings > 0 && (
                      <div className="p-4 rounded-lg bg-slate-800/50">
                        <div className="text-xs text-slate-400 mb-1">With Spot Instances</div>
                        <div className="text-2xl font-bold text-purple-400">
                          {recommendations.insights.spot_instance_opportunity?.average_savings?.toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-500">additional savings</div>
                      </div>
                    )}
                  </div>

                  {/* Key Insights */}
                  {recommendations.insights.key_insights?.length > 0 && (
                    <div className="space-y-2">
                      {recommendations.insights.key_insights.map((insight, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                          <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                          <span>{insight}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Recommendations List */}
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-yellow-400" />
                  Top {recommendations.total} Recommendations
                </h3>

                {recommendations.recommendations?.map((rec) => (
                  <div
                    key={`${rec.provider}-${rec.instance_type}`}
                    className={`
                      glass-card p-6 transition-all hover:border-primary-500/50
                      ${rec.rank === 1 ? 'ring-2 ring-yellow-500/20' : ''}
                    `}
                  >
                    {/* Rank Badge */}
                    {rec.rank <= 3 && (
                      <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gradient-to-r from-yellow-500/10 to-amber-500/10 border border-yellow-500/20 mb-3">
                        <span className="text-yellow-400 text-sm">
                          {rec.rank === 1 ? '🥇' : rec.rank === 2 ? '🥈' : '🥉'}
                        </span>
                        <span className="text-xs font-medium text-yellow-300">
                          {rec.rank === 1 ? 'Best Match' : `#${rec.rank}`}
                        </span>
                      </div>
                    )}

                    <div className="flex flex-col md:flex-row gap-6">
                      {/* Left: Instance Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <CloudBadge provider={rec.provider} />
                          <h4 className="text-lg font-semibold text-white font-mono">
                            {rec.instance_type}
                          </h4>
                          <div className="flex-1" />
                          <div className="text-right">
                            <div className="text-xs text-slate-400">AI Score</div>
                            <div className="text-lg font-bold text-primary-400">{rec.score}/100</div>
                          </div>
                        </div>

                        {/* Specs */}
                        <div className="grid grid-cols-2 gap-3 mb-4">
                          <div className="flex items-center gap-2 text-sm text-slate-300">
                            <Cpu className="w-4 h-4 text-slate-400" />
                            <span>{rec.vcpus} vCPUs</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-slate-300">
                            <MemoryStick className="w-4 h-4 text-slate-400" />
                            <span>{rec.memory_gb} GB RAM</span>
                          </div>
                        </div>

                        {/* Tags */}
                        <div className="flex flex-wrap gap-2 mb-4">
                          {rec.best_for?.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 text-xs rounded-md bg-slate-800 text-slate-300 border border-slate-700"
                            >
                              {tag}
                            </span>
                          ))}
                          {rec.processor_architecture === 'arm64' && (
                            <span className="px-2 py-1 text-xs rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20">
                              ARM (Efficient)
                            </span>
                          )}
                        </div>

                        {/* Reasoning */}
                        <p className="text-sm text-slate-400 leading-relaxed">
                          {rec.reasoning}
                        </p>
                      </div>

                      {/* Right: Pricing */}
                      <div className="md:w-48 flex flex-col gap-3">
                        {/* On-Demand Price */}
                        <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                          <div className="text-xs text-slate-400 mb-1">On-Demand</div>
                          <div className="text-2xl font-bold text-white">
                            ${rec.monthly_price?.toFixed(2)}
                          </div>
                          <div className="text-xs text-slate-500">per month</div>
                          <div className="text-xs text-slate-500 mt-1">
                            ${rec.hourly_price?.toFixed(4)}/hour
                          </div>
                        </div>

                        {/* Spot Price */}
                        {rec.spot_price && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20">
                            <div className="text-xs text-slate-400 mb-1">Spot/Preemptible</div>
                            <div className="text-2xl font-bold text-green-400">
                              ${rec.spot_price?.toFixed(2)}
                            </div>
                            <div className="text-xs text-green-400">
                              Save {rec.spot_savings?.toFixed(0)}%
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
