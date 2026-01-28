import { useState, useMemo, useEffect } from 'react'
import { 
  Search, 
  Filter, 
  Server, 
  Cpu, 
  MemoryStick,
  ChevronDown,
  X,
  Loader2
} from 'lucide-react'
import CloudBadge from '../components/CloudBadge'
import { api } from '../api/client'

const categories = [
  { id: 'all', name: 'All Categories' },
  { id: 'general_purpose', name: 'General Purpose' },
  { id: 'compute_optimized', name: 'Compute Optimized' },
  { id: 'memory_optimized', name: 'Memory Optimized' },
  { id: 'storage_optimized', name: 'Storage Optimized' },
  { id: 'gpu', name: 'GPU Instances' },
]

export default function InstanceFinder() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProviders, setSelectedProviders] = useState(['aws', 'gcp', 'azure'])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [filters, setFilters] = useState({
    minVcpus: '',
    maxVcpus: '',
    minMemory: '',
    maxMemory: '',
  })
  const [showFilters, setShowFilters] = useState(false)
  const [instances, setInstances] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch instances from API
  useEffect(() => {
    const fetchInstances = async () => {
      try {
        setLoading(true)
        const response = await api.getMulticloudInstances({ limit: 5000 })
        const instancesWithPrice = response.data.instances.map(instance => ({
          ...instance,
          price: instance.hourly_price || 0
        }))
        setInstances(instancesWithPrice)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch instances:', err)
        setError('Failed to load instances. Please try again.')
      } finally {
        setLoading(false)
      }
    }
    fetchInstances()
  }, [])

  const filteredInstances = useMemo(() => {
    return instances.filter(instance => {
      // Provider filter
      if (!selectedProviders.includes(instance.provider)) return false
      
      // Category filter
      if (selectedCategory !== 'all' && instance.category !== selectedCategory) return false
      
      // Search filter
      if (searchQuery && !instance.instance_type.toLowerCase().includes(searchQuery.toLowerCase())) return false
      
      // vCPU filter
      if (filters.minVcpus && instance.vcpus < parseInt(filters.minVcpus)) return false
      if (filters.maxVcpus && instance.vcpus > parseInt(filters.maxVcpus)) return false
      
      // Memory filter
      if (filters.minMemory && instance.memory_gb < parseInt(filters.minMemory)) return false
      if (filters.maxMemory && instance.memory_gb > parseInt(filters.maxMemory)) return false
      
      return true
    })
  }, [searchQuery, selectedProviders, selectedCategory, filters, instances])

  const toggleProvider = (provider) => {
    setSelectedProviders(prev => 
      prev.includes(provider)
        ? prev.filter(p => p !== provider)
        : [...prev, provider]
    )
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedProviders(['aws', 'gcp', 'azure'])
    setSelectedCategory('all')
    setFilters({ minVcpus: '', maxVcpus: '', minMemory: '', maxMemory: '' })
  }

  const hasActiveFilters = searchQuery || selectedCategory !== 'all' || 
    selectedProviders.length !== 3 || Object.values(filters).some(v => v)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Search className="w-8 h-8 text-blue-400" />
          Instance Finder
        </h1>
        <p className="text-slate-400 mt-2">
          Search and compare {instances.length}+ instance types across AWS, GCP, and Azure.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="glass-card p-6 space-y-4">
        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search instance types (e.g., t3.large, e2-standard, D4s)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-12 pr-4"
          />
        </div>

        {/* Quick filters row */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Provider buttons */}
          {['aws', 'gcp', 'azure'].map((provider) => (
            <button
              key={provider}
              onClick={() => toggleProvider(provider)}
              className={`
                px-3 py-2 rounded-lg border transition-all duration-200
                ${selectedProviders.includes(provider)
                  ? 'bg-slate-800 border-primary-500/50'
                  : 'border-slate-700 opacity-50 hover:opacity-100'
                }
              `}
            >
              <CloudBadge provider={provider} size="sm" />
            </button>
          ))}

          <div className="w-px h-8 bg-slate-700" />

          {/* Category dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="input-field w-auto pr-10"
          >
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          {/* Advanced filters toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              btn-secondary flex items-center gap-2
              ${showFilters ? 'bg-slate-700' : ''}
            `}
          >
            <Filter className="w-4 h-4" />
            Filters
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-slate-400 hover:text-white flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Clear all
            </button>
          )}
        </div>

        {/* Advanced filters */}
        {showFilters && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Min vCPUs</label>
              <input
                type="number"
                placeholder="Any"
                value={filters.minVcpus}
                onChange={(e) => setFilters({ ...filters, minVcpus: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Max vCPUs</label>
              <input
                type="number"
                placeholder="Any"
                value={filters.maxVcpus}
                onChange={(e) => setFilters({ ...filters, maxVcpus: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Min Memory (GB)</label>
              <input
                type="number"
                placeholder="Any"
                value={filters.minMemory}
                onChange={(e) => setFilters({ ...filters, minMemory: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Max Memory (GB)</label>
              <input
                type="number"
                placeholder="Any"
                value={filters.maxMemory}
                onChange={(e) => setFilters({ ...filters, maxMemory: e.target.value })}
                className="input-field"
              />
            </div>
          </div>
        )}
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Showing <span className="text-white font-medium">{filteredInstances.length}</span> instances
        </p>
      </div>

      {/* Results table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-spin" />
            <p className="text-slate-400">Loading instances...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <Server className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">{error}</p>
            <button onClick={() => window.location.reload()} className="text-primary-400 text-sm hover:underline">
              Retry
            </button>
          </div>
        ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-800/50 border-b border-slate-700">
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Instance Type
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  <div className="flex items-center gap-1">
                    <Cpu className="w-4 h-4" /> vCPUs
                  </div>
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  <div className="flex items-center gap-1">
                    <MemoryStick className="w-4 h-4" /> Memory
                  </div>
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Hourly
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Monthly
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredInstances.map((instance, index) => (
                <tr 
                  key={`${instance.provider}-${instance.instance_type}`}
                  className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <CloudBadge provider={instance.provider} size="sm" />
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm text-white">{instance.instance_type}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {instance.vcpus}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {instance.memory_gb} GB
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs px-2 py-1 rounded-md bg-slate-800 text-slate-300">
                      {instance.category.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-sm text-slate-300">
                    ${instance.price.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-sm font-semibold text-white">
                      ${(instance.price * 730).toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredInstances.length === 0 && (
            <div className="p-12 text-center">
              <Server className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No instances match your filters</p>
              <button onClick={clearFilters} className="text-primary-400 text-sm mt-2 hover:underline">
                Clear filters
              </button>
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  )
}

