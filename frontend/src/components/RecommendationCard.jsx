import { clsx } from 'clsx'
import { useState } from 'react'
import { Award, Cpu, MemoryStick, DollarSign, Zap, ChevronRight, ChevronDown, AlertTriangle, Shield, Clock, Info } from 'lucide-react'
import CloudBadge from './CloudBadge'

export default function RecommendationCard({ recommendation, rank, onClick }) {
  const [expanded, setExpanded] = useState(false)
  
  const {
    provider,
    instance_type,
    region,
    specs,
    pricing,
    savings,
    score,
    interruption_analysis,
  } = recommendation

  const getRankBadge = () => {
    if (rank === 1) return { color: 'from-yellow-400 to-amber-500', label: '🥇 Best Value' }
    if (rank === 2) return { color: 'from-slate-300 to-slate-400', label: '🥈 Runner Up' }
    if (rank === 3) return { color: 'from-amber-600 to-amber-700', label: '🥉 Third' }
    return null
  }

  const rankBadge = getRankBadge()
  
  // Get risk level styling
  const getRiskStyle = (level) => {
    switch (level) {
      case 'low':
        return { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', icon: '✅' }
      case 'medium':
        return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', icon: '⚠️' }
      case 'high':
        return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', icon: '🔶' }
      case 'very_high':
        return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', icon: '🚨' }
      default:
        return { bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-400', icon: '❓' }
    }
  }
  
  const isSpot = pricing?.strategy === 'spot'
  const riskStyle = interruption_analysis ? getRiskStyle(interruption_analysis.risk_level) : null

  return (
    <div
      className={clsx(
        'glass-card relative overflow-hidden transition-all duration-300',
        rank === 1 && 'ring-2 ring-primary-500/50'
      )}
    >
      {/* Rank badge */}
      {rankBadge && (
        <div className={clsx(
          'absolute -top-1 -right-1 px-3 py-1 text-xs font-bold text-slate-900 rounded-bl-xl rounded-tr-xl bg-gradient-to-r',
          rankBadge.color
        )}>
          {rankBadge.label}
        </div>
      )}

      {/* Main content - clickable */}
      <div 
        onClick={() => interruption_analysis ? setExpanded(!expanded) : onClick?.()}
        className="p-6 cursor-pointer card-hover"
      >
        <div className="flex items-start gap-4">
          {/* Rank number */}
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 text-2xl font-bold text-slate-400">
            #{rank}
          </div>

          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center gap-3 mb-3">
              <CloudBadge provider={provider} size="sm" />
              <h3 className="text-lg font-semibold text-white">{instance_type}</h3>
              {/* Spot/Preemptible badge */}
              {isSpot && (
                <span className="px-2 py-0.5 text-xs font-medium bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                  {provider === 'gcp' ? 'Preemptible' : 'Spot'}
                </span>
              )}
            </div>

            {/* Specs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-300">{specs?.vcpus || '-'} vCPUs</span>
              </div>
              <div className="flex items-center gap-2">
                <MemoryStick className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-300">{specs?.memory_gb || '-'} GB RAM</span>
              </div>
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-300">
                  {pricing?.monthly_cost > 0 
                    ? `$${pricing.monthly_cost.toFixed(2)}/mo` 
                    : <span className="text-slate-500">N/A</span>
                  }
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-300">{region}</span>
              </div>
            </div>

            {/* Interruption Risk Badge - Only for spot */}
            {interruption_analysis && (
              <div className={clsx(
                'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border mb-4',
                riskStyle.bg, riskStyle.border
              )}>
                <span>{riskStyle.icon}</span>
                <span className={clsx('text-sm font-medium', riskStyle.text)}>
                  {interruption_analysis.risk_level.charAt(0).toUpperCase() + interruption_analysis.risk_level.slice(1)} Risk
                </span>
                <span className="text-xs text-slate-400">
                  (Score: {interruption_analysis.risk_score}/100)
                </span>
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <div className="flex items-center gap-4">
                {/* Savings badge */}
                {savings?.percentage > 0 && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400 rounded-lg border border-green-500/20">
                    <TrendingDownIcon className="w-3 h-3" />
                    Save {savings.percentage.toFixed(0)}%
                  </span>
                )}
                
                {/* Score */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Score:</span>
                  <div className="flex items-center gap-1">
                    <div className="w-20 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full"
                        style={{ width: `${score}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-white">{score?.toFixed(0)}</span>
                  </div>
                </div>
              </div>

              {interruption_analysis ? (
                <button className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition-colors">
                  {expanded ? 'Hide' : 'View'} Risk Analysis
                  <ChevronDown className={clsx('w-4 h-4 transition-transform', expanded && 'rotate-180')} />
                </button>
              ) : (
                <ChevronRight className="w-5 h-5 text-slate-400" />
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Expanded Interruption Analysis Section */}
      {interruption_analysis && expanded && (
        <div className="border-t border-slate-800 p-6 bg-slate-900/50 animate-fade-in">
          <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary-400" />
            Interruption Risk Analysis
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Risk Meter */}
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">Risk Level</span>
                <span className={clsx('text-sm font-bold', riskStyle.text)}>
                  {riskStyle.icon} {interruption_analysis.risk_level.toUpperCase()}
                </span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className={clsx(
                    'h-full rounded-full transition-all duration-500',
                    interruption_analysis.risk_score < 25 ? 'bg-green-500' :
                    interruption_analysis.risk_score < 50 ? 'bg-yellow-500' :
                    interruption_analysis.risk_score < 75 ? 'bg-orange-500' : 'bg-red-500'
                  )}
                  style={{ width: `${interruption_analysis.risk_score}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-xs text-slate-500">
                <span>Safe</span>
                <span>Risky</span>
              </div>
            </div>
            
            {/* Interruption Frequency */}
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-400">Expected Interruption Frequency</span>
              </div>
              <p className="text-sm text-white">{interruption_analysis.interruption_frequency}</p>
            </div>
          </div>
          
          {/* Provider Note */}
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 mb-4">
            <div className="flex gap-2">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-200">{interruption_analysis.provider_notes}</p>
            </div>
          </div>
          
          {/* Recommendations */}
          {interruption_analysis.recommendations?.length > 0 && (
            <div>
              <h5 className="text-xs font-medium text-slate-400 mb-2">Recommendations:</h5>
              <ul className="space-y-2">
                {interruption_analysis.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-primary-400 mt-1">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TrendingDownIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
      <polyline points="17 18 23 18 23 12" />
    </svg>
  )
}

