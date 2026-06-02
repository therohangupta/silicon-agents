import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Cog, FileText, ChevronRight, Variable, Search, SortAsc, SortDesc, Filter } from 'lucide-react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/common/Button'
import { Modal } from '../components/common/Modal'
import { EmptyState } from '../components/common/EmptyState'
import { methodsApi, type MethodSummary } from '../lib/api'
import { cn } from '../lib/utils'
import { MethodDetailModal } from './Planners'

// =============================================================================
// Prompt Card Component
// =============================================================================

// Color palette for automatic assignment
const COLOR_PALETTE = [
  { bg: 'bg-sky-100', border: 'border-sky-300', text: 'text-sky-950', icon: 'bg-sky-200/80' },
  { bg: 'bg-emerald-100', border: 'border-emerald-300', text: 'text-emerald-950', icon: 'bg-emerald-200/80' },
  { bg: 'bg-violet-100', border: 'border-violet-300', text: 'text-violet-950', icon: 'bg-violet-200/80' },
  { bg: 'bg-amber-100', border: 'border-amber-300', text: 'text-amber-950', icon: 'bg-amber-200/80' },
  { bg: 'bg-rose-100', border: 'border-rose-300', text: 'text-rose-950', icon: 'bg-rose-200/80' },
  { bg: 'bg-cyan-100', border: 'border-cyan-300', text: 'text-cyan-950', icon: 'bg-cyan-200/80' },
  { bg: 'bg-pink-100', border: 'border-pink-300', text: 'text-pink-950', icon: 'bg-pink-200/80' },
  { bg: 'bg-teal-100', border: 'border-teal-300', text: 'text-teal-950', icon: 'bg-teal-200/80' },
  { bg: 'bg-indigo-100', border: 'border-indigo-300', text: 'text-indigo-950', icon: 'bg-indigo-200/80' },
  { bg: 'bg-orange-100', border: 'border-orange-300', text: 'text-orange-950', icon: 'bg-orange-200/80' },
]

// Generate colors for a planner type using a simple hash
function getPlannerColors(plannerType: string) {
  // Simple hash function for consistent color assignment
  let hash = 0
  for (let i = 0; i < plannerType.length; i++) {
    hash = ((hash << 5) - hash) + plannerType.charCodeAt(i)
    hash = hash & hash // Convert to 32-bit integer
  }
  return COLOR_PALETTE[Math.abs(hash) % COLOR_PALETTE.length]
}

function MethodCard({
  method,
  onClick
}: {
  method: MethodSummary
  onClick: () => void
}) {
  const colors = getPlannerColors(method.type)

  return (
    <Card hover className="group relative overflow-hidden p-0 cursor-pointer" onClick={onClick}>
      <div className={cn('h-1', colors.bg)} />
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <div className={cn('w-2 h-2 rounded-full', colors.icon)} />
              <h3 className="font-semibold text-slate-900">{method.name}</h3>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">{method.description}</p>
          </div>
          <span className={cn(
            'shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold',
            method.method_type === 'foundation model' && 'bg-sky-50 text-sky-800 ring-1 ring-sky-200/80',
            method.method_type === 'hybrid' && 'bg-violet-50 text-violet-800 ring-1 ring-violet-200/80',
            method.method_type === 'algorithmic' && 'bg-orange-50 text-orange-800 ring-1 ring-orange-200/80',
            !['foundation model', 'hybrid', 'algorithmic'].includes(method.method_type || '') && 'bg-slate-100 text-slate-600 ring-1 ring-slate-200/80'
          )}>
            {method.method_type}
          </span>
        </div>
      </div>
    </Card>
  )
}


// =============================================================================
// Main Allocators Page
// =============================================================================

export function Allocators() {
  const [selectedMethod, setSelectedMethod] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'name' | 'type'>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Handle URL query parameters for method modal
  useEffect(() => {
    const method = searchParams.get('method')
    if (method) {
      const methodId = parseInt(method, 10)
      if (!isNaN(methodId)) {
        setSelectedMethod(methodId)
      }
    }
  }, [searchParams])

  const { data: allMethods = [], isLoading } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  // Filter and sort methods based on search, type filter, and sort criteria
  const methods = useMemo(() => {
    let filtered = allMethods

    // Apply search filter first
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase()
      filtered = filtered.filter(method => {
        const nameMatch = method.name?.toLowerCase().includes(searchLower)
        const descMatch = method.description?.toLowerCase().includes(searchLower)
        const typeMatch = method.type?.toLowerCase().includes(searchLower)

        return nameMatch || descMatch || typeMatch
      })
    }

    // Apply type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(method => method.method_type === typeFilter)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: string, bValue: string

      if (sortBy === 'name') {
        aValue = a.name || ''
        bValue = b.name || ''
      } else {
        aValue = a.method_type || ''
        bValue = b.method_type || ''
      }

      const comparison = aValue.localeCompare(bValue)
      return sortOrder === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [allMethods, searchTerm, typeFilter, sortBy, sortOrder])

  // Get unique method types for filter buttons
  const availableTypes = useMemo(() => {
    const types = new Set(allMethods.map(method => method.method_type))
    return Array.from(types).sort()
  }, [allMethods])

  if (isLoading) {
    return <div className="text-[var(--color-text-secondary)]">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Allocators"
        description="Allocation methods assign tasks to robots—reasoning models, hybrids, or optimizers."
      />

      {/* Info Banner */}
      <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 ring-1 ring-slate-200/70 border-l-[3px] border-l-violet-500">
        <p className="text-sm text-[var(--color-text)]">
          <strong className="text-[var(--color-text)]">Allocator Types:</strong> Some use{' '}
          <span className="text-cyan-800 font-medium">LLM reasoning</span> for intelligent task assignment, others use{' '}
          <span className="text-violet-800 font-medium">hybrid approaches</span> combining algorithmic orchestration with LLM assistance, and some use{' '}
          <span className="text-orange-800 font-medium">mathematical optimization</span> for balanced workloads.
        </p>
      </div>

      {/* Filters and Search */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--color-text-secondary)]" />
          <input
            type="text"
            placeholder="Search allocators by name, description, or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
          />
        </div>

        {/* Type Filters and Sort Controls */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          {/* Type Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setTypeFilter('all')}
              className={cn(
                'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                typeFilter === 'all'
                  ? 'bg-gradient-to-r from-cyan-500 to-cyan-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 ring-1 ring-slate-200/80 hover:ring-cyan-300 hover:text-slate-900'
              )}
            >
              <Filter className="w-3.5 h-3.5 inline mr-1" />
              All Types ({allMethods.length})
            </button>
            {availableTypes.map(methodType => {
              const count = allMethods.filter(method => method.method_type === methodType).length
              return (
                <button
                  key={methodType}
                  onClick={() => setTypeFilter(methodType)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                    typeFilter === methodType
                      ? 'bg-gradient-to-r from-cyan-500 to-cyan-600 text-white shadow-sm'
                      : 'bg-white text-slate-600 ring-1 ring-slate-200/80 hover:ring-cyan-300 hover:text-slate-900'
                  )}
                >
                  {methodType} ({count})
                </button>
              )
            })}
          </div>

          {/* Sort Controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--color-text-secondary)]">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'method_type')}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-[var(--color-text)] text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
            >
              <option value="name">Name</option>
              <option value="method_type">Method Type</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1.5 bg-slate-50 border border-slate-200 rounded-md text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:border-slate-200 transition-colors"
              title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
            >
              {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Results Summary */}
        {(searchTerm || typeFilter !== 'all') && (
          <div className="text-sm text-[var(--color-text-secondary)]">
            Showing {methods.length} of {allMethods.length} allocators
            {searchTerm && ` matching "${searchTerm}"`}
            {typeFilter !== 'all' && ` of type "${typeFilter}"`}
          </div>
        )}
      </div>

      {/* Methods Grid */}
      {methods.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {methods.map((method) => (
            <MethodCard
              key={`${method.category}-${method.type}`}
              method={method}
              onClick={() => navigate(`/allocators?method=${method.id}`)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Cog className="w-8 h-8" />}
          title="No allocators found"
          description="Allocator configuration files may be missing from the allocators types directory."
        />
      )}

      {/* Detail Modal */}
      <MethodDetailModal
        methodId={selectedMethod}
        methodType="allocator"
        isOpen={!!selectedMethod}
        onClose={() => {
          setSelectedMethod(null)
          // Clear URL parameters when modal closes
          navigate('/allocators', { replace: true })
        }}
      />
    </div>
  )
}
