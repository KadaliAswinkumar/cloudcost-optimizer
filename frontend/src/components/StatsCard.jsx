import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function StatsCard({ 
  title, 
  value, 
  subtitle, 
  trend, 
  trendValue, 
  icon: Icon,
  className,
  style
}) {
  const getTrendIcon = () => {
    if (!trend) return null
    if (trend === 'up') return <TrendingUp className="w-4 h-4" />
    if (trend === 'down') return <TrendingDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-400'
    if (trend === 'down') return 'text-red-400'
    return 'text-slate-400'
  }

  return (
    <div 
      className={clsx(
        'glass-card p-6 relative overflow-hidden group card-hover',
        className
      )}
      style={style}
    >
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 w-24 h-24 bg-gradient-to-br from-primary-500/10 to-purple-500/10 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-400 mb-1">{title}</p>
            <p className="text-3xl font-bold text-white">{value}</p>
            {subtitle && (
              <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
            )}
          </div>
          {Icon && (
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <Icon className="w-6 h-6 text-primary-400" />
            </div>
          )}
        </div>

        {trend && trendValue && (
          <div className={clsx('flex items-center gap-1 mt-3', getTrendColor())}>
            {getTrendIcon()}
            <span className="text-sm font-medium">{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  )
}

