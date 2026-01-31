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
  Info,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import RecommendationCard from '../components/RecommendationCard'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

const ITEMS_PER_PAGE = 10

export default function Recommendations() {
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState(null)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  
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
      // Call the real multicloud recommendations API
      const requestData = {
        min_vcpus: formData.min_vcpus,
        min_memory_gb: formData.min_memory_gb,
        providers: formData.providers,
        workload_type: formData.workload_type,
        spot_eligible: formData.spot_eligible,
        hours_per_month: formData.hours_per_month,
      }
      
      // Add budget if specified
      if (formData.max_monthly_budget && formData.max_monthly_budget > 0) {
        requestData.max_monthly_budget = parseFloat(formData.max_monthly_budget)
      }
      
      console.log('Sending recommendation request:', requestData)
      const response = await api.getMulticloudRecommendations(requestData)
      console.log('Received recommendations:', response.data)
      
      setRecommendations(response.data)
      setCurrentPage(1) // Reset to page 1 when new recommendations are loaded
    } catch (err) {
      console.error('Error fetching recommendations:', err)
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
                          {data?.cheapest_monthly > 0 
                            ? `$${data.cheapest_monthly.toFixed(0)}` 
                            : <span className="text-slate-500 text-lg">N/A</span>
                          }
                        </p>
                        <p className="text-xs text-slate-400">
                          {data?.cheapest_monthly > 0 ? 'per month' : 'Pricing unavailable'}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Recommendations List */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">Top Recommendations</h2>
                  {recommendations.overall_best.length > ITEMS_PER_PAGE && (
                    <p className="text-sm text-slate-400">
                      Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, recommendations.overall_best.length)} of {recommendations.overall_best.length}
                    </p>
                  )}
                </div>
                {recommendations.overall_best
                  .slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
                  .map((rec, index) => (
                    <RecommendationCard
                      key={`${rec.provider}-${rec.instance_type}`}
                      recommendation={rec}
                      rank={((currentPage - 1) * ITEMS_PER_PAGE) + index + 1}
                    />
                  ))}
              </div>

              {/* Pagination */}
              {recommendations.overall_best.length > ITEMS_PER_PAGE && (() => {
                const totalPages = Math.ceil(recommendations.overall_best.length / ITEMS_PER_PAGE)
                const getPageNumbers = () => {
                  const pages = []
                  const showPages = 7
                  
                  if (totalPages <= showPages) {
                    for (let i = 1; i <= totalPages; i++) {
                      pages.push(i)
                    }
                  } else {
                    pages.push(1)
                    if (currentPage > 3) pages.push('...')
                    const start = Math.max(2, currentPage - 1)
                    const end = Math.min(totalPages - 1, currentPage + 1)
                    for (let i = start; i <= end; i++) {
                      pages.push(i)
                    }
                    if (currentPage < totalPages - 2) pages.push('...')
                    if (totalPages > 1) pages.push(totalPages)
                  }
                  
                  return pages
                }

                return (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    {/* Previous Button */}
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className={`
                        px-4 py-2 rounded-lg border transition-all
                        ${currentPage === 1
                          ? 'border-slate-700 text-slate-600 cursor-not-allowed'
                          : 'border-slate-600 text-slate-300 hover:bg-slate-800 hover:border-slate-500'
                        }
                      `}
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>

                    {/* Page Numbers */}
                    {getPageNumbers().map((page, idx) => (
                      page === '...' ? (
                        <span key={`ellipsis-${idx}`} className="px-3 text-slate-500">...</span>
                      ) : (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`
                            px-4 py-2 rounded-lg border transition-all min-w-[44px]
                            ${currentPage === page
                              ? 'bg-purple-500 border-purple-500 text-white font-semibold'
                              : 'border-slate-600 text-slate-300 hover:bg-slate-800 hover:border-slate-500'
                            }
                          `}
                        >
                          {page}
                        </button>
                      )
                    ))}

                    {/* Next Button */}
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className={`
                        px-4 py-2 rounded-lg border transition-all
                        ${currentPage === totalPages
                          ? 'border-slate-700 text-slate-600 cursor-not-allowed'
                          : 'border-slate-600 text-slate-300 hover:bg-slate-800 hover:border-slate-500'
                        }
                      `}
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                )
              })()}
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

