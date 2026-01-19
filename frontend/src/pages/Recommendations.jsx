import { useState } from 'react'
import { 
  Sparkles, 
  Cpu, 
  MemoryStick, 
  DollarSign, 
  Clock,
  Loader2,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Shield,
  Info
} from 'lucide-react'
import RecommendationCard from '../components/RecommendationCard'
import CloudBadge from '../components/CloudBadge'

export default function Recommendations() {
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState(null)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    min_vcpus: 4,
    min_memory_gb: 16,
    providers: ['aws', 'gcp', 'azure'],
    workload_type: 'steady',
    spot_eligible: false,
    interruption_tolerance: 'medium',  // NEW: Interruption tolerance
    hours_per_month: 730,
    max_monthly_budget: '',
  })
  
  // Interruption tolerance options
  const toleranceOptions = [
    { value: 'none', label: 'None', desc: 'No interruptions (On-Demand only)', icon: '🔒' },
    { value: 'low', label: 'Low', desc: 'Only very stable spot instances', icon: '🛡️' },
    { value: 'medium', label: 'Medium', desc: 'Some interruptions OK', icon: '⚖️' },
    { value: 'high', label: 'High', desc: 'Fully fault-tolerant workload', icon: '⚡' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Simulated API call - replace with actual API
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Mock response with interruption analysis
      const spotEnabled = formData.spot_eligible
      setRecommendations({
        overall_best: [
          {
            rank: 1,
            provider: 'gcp',
            instance_type: spotEnabled ? 'e2-standard-4 (Preemptible)' : 'e2-standard-4',
            region: 'us-central1',
            specs: { vcpus: 4, memory_gb: 16, category: 'General Purpose' },
            pricing: { 
              strategy: spotEnabled ? 'spot' : 'on_demand',
              monthly_cost: spotEnabled ? 29.57 : 98.55, 
              hourly_cost: spotEnabled ? 0.0405 : 0.135,
              on_demand_hourly: 0.135
            },
            savings: { percentage: spotEnabled ? 70 : 42 },
            score: 94,
            // NEW: Interruption Analysis
            interruption_analysis: spotEnabled ? {
              risk_level: 'medium',
              risk_score: 35,
              interruption_frequency: '5-15% - Occasional interruptions',
              provider_notes: 'GCP Preemptible: 30-second warning, max 24h runtime',
              recommendations: [
                '📌 GCP: Preemptible VMs have max 24h lifetime',
                '⚠️ Use checkpointing to save progress frequently'
              ]
            } : null,
          },
          {
            rank: 2,
            provider: 'aws',
            instance_type: spotEnabled ? 'm5.xlarge (Spot)' : 't3.xlarge',
            region: 'us-east-1',
            specs: { vcpus: 4, memory_gb: 16, category: 'General Purpose' },
            pricing: { 
              strategy: spotEnabled ? 'spot' : 'on_demand',
              monthly_cost: spotEnabled ? 36.35 : 121.18, 
              hourly_cost: spotEnabled ? 0.0498 : 0.166,
              on_demand_hourly: 0.166
            },
            savings: { percentage: spotEnabled ? 70 : 31 },
            score: 88,
            interruption_analysis: spotEnabled ? {
              risk_level: 'low',
              risk_score: 22,
              interruption_frequency: '<5% - Very rare interruptions',
              provider_notes: 'AWS Spot: 2-minute interruption notice via instance metadata',
              recommendations: [
                '✅ Good candidate for spot usage',
                'Set bid at current price + 10%'
              ]
            } : null,
          },
          {
            rank: 3,
            provider: 'azure',
            instance_type: spotEnabled ? 'Standard_D4s_v4 (Spot)' : 'Standard_D4s_v4',
            region: 'eastus',
            specs: { vcpus: 4, memory_gb: 16, category: 'General Purpose' },
            pricing: { 
              strategy: spotEnabled ? 'spot' : 'on_demand',
              monthly_cost: spotEnabled ? 42.05 : 140.16, 
              hourly_cost: spotEnabled ? 0.0576 : 0.192,
              on_demand_hourly: 0.192
            },
            savings: { percentage: spotEnabled ? 70 : 22 },
            score: 82,
            interruption_analysis: spotEnabled ? {
              risk_level: 'medium',
              risk_score: 40,
              interruption_frequency: '5-15% - Occasional interruptions',
              provider_notes: 'Azure Spot: Eviction notice via scheduled events API',
              recommendations: [
                '⚠️ Use checkpointing to save progress frequently',
                'Consider Spot VM pools for diversification'
              ]
            } : null,
          },
          // Add a high-risk example when spot is enabled
          ...(spotEnabled ? [{
            rank: 4,
            provider: 'aws',
            instance_type: 'c5.xlarge (Spot)',
            region: 'us-west-2',
            specs: { vcpus: 4, memory_gb: 8, category: 'Compute Optimized' },
            pricing: { 
              strategy: 'spot',
              monthly_cost: 25.55, 
              hourly_cost: 0.035,
              on_demand_hourly: 0.170
            },
            savings: { percentage: 79 },
            score: 76,
            interruption_analysis: {
              risk_level: 'high',
              risk_score: 68,
              interruption_frequency: '15-30% - Frequent interruptions likely',
              provider_notes: 'AWS Spot: 2-minute interruption notice via instance metadata',
              recommendations: [
                '🚨 High interruption risk - only for fault-tolerant workloads',
                '⚠️ Use Spot Fleet with instance diversification',
                'Implement aggressive checkpointing (every 5 min)'
              ]
            },
          }] : []),
        ],
        cross_cloud_comparison: {
          aws: { cheapest_monthly: spotEnabled ? 36.35 : 121.18 },
          gcp: { cheapest_monthly: spotEnabled ? 29.57 : 98.55 },
          azure: { cheapest_monthly: spotEnabled ? 42.05 : 140.16 },
          cheapest_overall: { provider: 'gcp', monthly_cost: spotEnabled ? 29.57 : 98.55 },
        },
      })
    } catch (err) {
      setError('Failed to get recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleProvider = (provider) => {
    setFormData(prev => ({
      ...prev,
      providers: prev.providers.includes(provider)
        ? prev.providers.filter(p => p !== provider)
        : [...prev.providers, provider],
    }))
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-purple-400" />
          Get Recommendations
        </h1>
        <p className="text-slate-400 mt-2">
          Tell us about your workload and we'll find the best cloud instances for you.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form */}
        <div className="lg:col-span-1">
          <form onSubmit={handleSubmit} className="glass-card p-6 space-y-6 sticky top-8">
            <h2 className="text-lg font-semibold text-white">Requirements</h2>
            
            {/* vCPUs */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                <Cpu className="w-4 h-4 text-slate-400" />
                Minimum vCPUs
              </label>
              <input
                type="number"
                min="1"
                max="256"
                value={formData.min_vcpus}
                onChange={(e) => setFormData({ ...formData, min_vcpus: parseInt(e.target.value) })}
                className="input-field"
              />
            </div>

            {/* Memory */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                <MemoryStick className="w-4 h-4 text-slate-400" />
                Minimum Memory (GB)
              </label>
              <input
                type="number"
                min="1"
                max="1024"
                value={formData.min_memory_gb}
                onChange={(e) => setFormData({ ...formData, min_memory_gb: parseInt(e.target.value) })}
                className="input-field"
              />
            </div>

            {/* Cloud Providers */}
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                Cloud Providers
              </label>
              <div className="flex flex-wrap gap-2">
                {['aws', 'gcp', 'azure'].map((provider) => (
                  <button
                    key={provider}
                    type="button"
                    onClick={() => toggleProvider(provider)}
                    className={`
                      px-3 py-2 rounded-lg border transition-all duration-200
                      ${formData.providers.includes(provider)
                        ? 'bg-slate-800 border-primary-500 ring-1 ring-primary-500/50'
                        : 'border-slate-700 hover:border-slate-600'
                      }
                    `}
                  >
                    <CloudBadge provider={provider} size="sm" showIcon={false} />
                  </button>
                ))}
              </div>
            </div>

            {/* Workload Type */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                <Clock className="w-4 h-4 text-slate-400" />
                Workload Type
              </label>
              <select
                value={formData.workload_type}
                onChange={(e) => setFormData({ ...formData, workload_type: e.target.value })}
                className="input-field"
              >
                <option value="steady">Steady (24/7)</option>
                <option value="variable">Variable</option>
                <option value="burst">Burst / Spiky</option>
                <option value="batch">Batch Processing</option>
                <option value="dev_test">Dev/Test</option>
              </select>
            </div>

            {/* Spot Eligible */}
            <div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.spot_eligible}
                  onChange={(e) => setFormData({ ...formData, spot_eligible: e.target.checked })}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500/50"
                />
                <span className="text-sm text-slate-300">
                  Include Spot/Preemptible Instances
                </span>
              </label>
              <p className="text-xs text-slate-500 mt-1 ml-8">
                Can save up to 90%, but may be interrupted
              </p>
            </div>

            {/* Interruption Tolerance - Only show when spot is enabled */}
            {formData.spot_eligible && (
              <div className="animate-fade-in">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                  <Shield className="w-4 h-4 text-slate-400" />
                  Interruption Tolerance
                </label>
                <div className="space-y-2">
                  {toleranceOptions.map((option) => (
                    <label
                      key={option.value}
                      className={`
                        flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all
                        ${formData.interruption_tolerance === option.value
                          ? 'bg-primary-500/10 border-primary-500/50'
                          : 'border-slate-700 hover:border-slate-600'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="tolerance"
                        value={option.value}
                        checked={formData.interruption_tolerance === option.value}
                        onChange={(e) => setFormData({ ...formData, interruption_tolerance: e.target.value })}
                        className="mt-1 w-4 h-4 border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500/50"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{option.icon}</span>
                          <span className="text-sm font-medium text-white">{option.label}</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{option.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <div className="flex gap-2">
                    <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-200">
                      Higher tolerance = more savings but higher interruption risk. 
                      We filter out instances that exceed your tolerance level.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Budget */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                <DollarSign className="w-4 h-4 text-slate-400" />
                Max Monthly Budget (optional)
              </label>
              <input
                type="number"
                min="0"
                placeholder="No limit"
                value={formData.max_monthly_budget}
                onChange={(e) => setFormData({ ...formData, max_monthly_budget: e.target.value })}
                className="input-field"
              />
            </div>

            <button
              type="submit"
              disabled={loading || formData.providers.length === 0}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Get Recommendations
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="glass-card p-4 border-red-500/50 flex items-center gap-3 text-red-400">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          {recommendations ? (
            <>
              {/* Summary */}
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <h2 className="text-lg font-semibold text-white">Analysis Complete</h2>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  {['aws', 'gcp', 'azure'].map((provider) => {
                    const data = recommendations.cross_cloud_comparison[provider]
                    const isCheapest = recommendations.cross_cloud_comparison.cheapest_overall?.provider === provider
                    
                    return (
                      <div
                        key={provider}
                        className={`
                          p-4 rounded-xl border transition-all
                          ${isCheapest 
                            ? 'bg-green-500/10 border-green-500/30' 
                            : 'bg-slate-800/50 border-slate-700'
                          }
                        `}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <CloudBadge provider={provider} size="sm" showIcon={false} />
                          {isCheapest && (
                            <span className="text-xs font-medium text-green-400">CHEAPEST</span>
                          )}
                        </div>
                        <p className="text-2xl font-bold text-white">
                          ${data?.cheapest_monthly?.toFixed(0)}
                        </p>
                        <p className="text-xs text-slate-400">per month</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Recommendations List */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-white">Top Recommendations</h2>
                {recommendations.overall_best.map((rec, index) => (
                  <RecommendationCard
                    key={`${rec.provider}-${rec.instance_type}`}
                    recommendation={rec}
                    rank={index + 1}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="glass-card p-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-slate-500" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">
                Ready to optimize?
              </h3>
              <p className="text-slate-400 max-w-sm mx-auto">
                Fill in your requirements and click "Get Recommendations" to see the best cloud instances for your workload.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

