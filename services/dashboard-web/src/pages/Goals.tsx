/**
 * @fileoverview Goals page (`/goals`): create, search, sort, delete, and inspect goals.
 *
 * Includes {@link GoalDetailsModal} (overview / plans / agents tabs) and
 * {@link CreateGoalModal}. Strategy name chips depend on method data seeded via
 * `setMethodData` after planners/allocators queries resolve.
 */

// Modal/tab state, method seeding effect, and memoized filtered goal list.
import { useState, useEffect, useMemo } from 'react'
// Goals/plans/tasks/agents/methods queries and create/delete mutations.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
// Icons for goals, plans, agents, status badges, and search/sort controls.
import { Target, Plus, Trash2, Search, ChevronDown, Info, GitBranch, Bot, CheckCircle, Play, AlertTriangle, XCircle } from 'lucide-react'
// Card surfaces for goal tiles and modal sections.
import { Card } from '../components/common/Card'
// Page title with create action slot.
import { PageHeader } from '../components/layout/PageHeader'
// Primary / ghost buttons for create and delete.
import { Button } from '../components/common/Button'
// Detail and create dialogs.
import { Modal } from '../components/common/Modal'
// Empty plans/agents and empty goals placeholders.
import { EmptyState } from '../components/common/EmptyState'
// Gateway APIs + realtime invalidation for agent health.
import { goalsApi, plansApi, methodsApi, tasksApi, agentsApi, useRealtimeUpdates } from '../lib/api'
// Class merge + strategy display names + method lookup seeding.
import { cn, getPlanningStrategyName, getAllocationStrategyName, setMethodData } from '../lib/utils'

/**
 * Per-agent reachability row from `/api/agents/health/all`.
 */
interface AgentHealth {
  /** Agent id matching Agent.agent_id. */
  agent_id: string
  /** Task-server host probed by the gateway. */
  host: string
  /** Task-server port probed by the gateway. */
  port: number
  /** True when the health probe succeeded. */
  reachable: boolean
  /** Optional RTT from the health probe. */
  latency_ms?: number
  /** Optional error string when unreachable. */
  error?: string
}

// =============================================================================
// Goal Details Modal with Tabs
// =============================================================================

/**
 * Tabbed modal inspecting one goal: overview stats, related plans, assigned agents.
 * @param props.goalId - Goal to show, or null when closed.
 * @param props.isOpen - Modal visibility.
 * @param props.onClose - Close handler.
 */
function GoalDetailsModal({ goalId, isOpen, onClose }: { goalId: number | null; isOpen: boolean; onClose: () => void }) {
  // Which tab is active inside the modal.
  const [activeTab, setActiveTab] = useState<'overview' | 'plans' | 'agents'>('overview')

  // All goals (to resolve the selected goalId).
  const { data: goals = [] } = useQuery({
    queryKey: ['goals'],
    queryFn: goalsApi.list,
  })

  // All plans (filtered to those including this goal).
  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: plansApi.list,
  })

  // All agents (filtered to those allocated to this goal's plans).
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
  })

  // Enable real-time updates for agent health invalidation.
  useRealtimeUpdates()

  // Reachability map keyed by agent_id.
  const { data: robotHealth = {} } = useQuery({
    queryKey: ['agent-health'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/agents/health/all')
        const data = await response.json()
        const healthMap: Record<string, AgentHealth> = {}
        for (const health of data.agents || []) {
          healthMap[health.agent_id] = health
        }
        return healthMap
      } catch (error) {
        console.error('Failed to fetch agent health:', error)
        return {}
      }
    },
    // Enable background refetching for more responsive updates
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    staleTime: 1000, // Consider data stale after 1 second
    // WebSocket handles most updates, this is backup
  })

  const goal = goals.find(g => g.goal_id === goalId)
  const goalPlans = goalId ? plans.filter(plan => plan.goal_ids.includes(goalId)) : []

  // Get unique agents assigned to this goal across all plans
  const assignedAgents = new Set<string>()
  goalPlans.forEach(plan => {
    if (plan.allocation_artifacts?.final_allocation?.allocations) {
      plan.allocation_artifacts.final_allocation.allocations.forEach((alloc: any) => {
        assignedAgents.add(alloc.agent_id)
      })
    }
  })
  const goalAgents = agents.filter(agent => assignedAgents.has(agent.agent_id))

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <Info className="w-4 h-4" /> },
    { id: 'plans', label: 'Plans', icon: <GitBranch className="w-4 h-4" /> },
    { id: 'agents', label: 'Agents', icon: <Bot className="w-4 h-4" /> },
  ]

  if (!goal) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Goal #${goal.goal_id}`} size="wide" className="max-h-[90vh]">
      <div className="space-y-6 max-h-[75vh] overflow-y-auto">
        {/* Tab Navigation — overview / plans / agents */}
        <div className="flex space-x-1 border-b border-slate-200 pb-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-t-md transition-colors flex items-center space-x-2',
                activeTab === tab.id
                  ? 'bg-slate-50 text-[var(--color-text)] border-b-2 border-blue-500'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Active tab body */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Goal Description card */}
            <Card className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-violet-100 rounded-lg flex items-center justify-center flex-shrink-0 border border-violet-200">
                  <Target className="w-6 h-6 text-violet-900" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-[var(--color-text)] mb-2">Goal Description</h3>
                  <p className="text-[var(--color-text)] leading-relaxed">{goal.description}</p>
                </div>
              </div>
            </Card>

            {/* Overview statistic cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="p-4 border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-sky-100 rounded-lg flex items-center justify-center border border-sky-200">
                    <GitBranch className="w-5 h-5 text-sky-900" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-sky-950">{goalPlans.length}</div>
                    <div className="text-sm text-[var(--color-text-secondary)]">Plans Generated</div>
                  </div>
                </div>
              </Card>

              <Card className="p-4 border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center border border-emerald-200">
                    <CheckCircle className="w-5 h-5 text-emerald-900" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-emerald-950">
                      {goalPlans.reduce((total, plan) => {
                        if (plan.allocation_artifacts?.task_descriptions) {
                          return total + plan.allocation_artifacts.task_descriptions.filter((task: any) => task.goal_id === goalId?.toString()).length
                        }
                        return total
                      }, 0)}
                    </div>
                    <div className="text-sm text-[var(--color-text-secondary)]">Tasks Created</div>
                  </div>
                </div>
              </Card>

              <Card className="p-4 border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center border border-violet-200">
                    <Bot className="w-5 h-5 text-violet-900" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-violet-950">{goalAgents.length}</div>
                    <div className="text-sm text-[var(--color-text-secondary)]">Agents Assigned</div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'plans' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-[var(--color-text)]">Generated Plans</h3>
              <span className="text-sm text-[var(--color-text-muted)] bg-slate-50 px-3 py-1 rounded-full">
                {goalPlans.length} plans
              </span>
            </div>

            {goalPlans.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {goalPlans.map(plan => {
                  const executionStatus = plan.execution_status || 'not_executed'
                  const goalCount = Array.isArray(plan.goal_ids) ? new Set(plan.goal_ids).size : 0

                  let badgeConfig = { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-[var(--color-text-secondary)]', label: 'Unknown', icon: AlertTriangle }

                  if (executionStatus === 'completed') {
                    badgeConfig = { bg: 'bg-emerald-100', border: 'border-emerald-300', text: 'text-emerald-950', label: 'Completed', icon: CheckCircle }
                  } else if (executionStatus === 'executing') {
                    badgeConfig = { bg: 'bg-amber-100', border: 'border-amber-300', text: 'text-amber-950', label: 'Running', icon: Play }
                  } else {
                    badgeConfig = { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-[var(--color-text-secondary)]', label: 'Not Started', icon: AlertTriangle }
                  }

                  return (
                    <Card key={plan.plan_id} className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                          onClick={() => window.open(`/plans/${plan.plan_id}`, '_blank')}>
                      {/* Plan id chip + execution badge */}
                      <div className="flex items-center justify-between mb-3">
                        <span className="px-2 py-1 tonal-plan-id rounded text-xs font-semibold">
                          P{plan.plan_id}
                        </span>
                        <div className={cn('px-2 py-1 rounded text-xs flex items-center gap-1 font-medium border', badgeConfig.bg, badgeConfig.border, badgeConfig.text)}>
                          <badgeConfig.icon className="w-3 h-3" />
                          {badgeConfig.label}
                        </div>
                      </div>

                      {/* Plan Name & Description */}
                      <div className="mb-3">
                        <h4 className="font-medium text-[var(--color-text)] mb-1">{plan.name || `Plan ${plan.plan_id}`}</h4>
                        {plan.description && (
                          <p className="text-sm text-[var(--color-text-secondary)] line-clamp-2">{plan.description}</p>
                        )}
                      </div>

                      {/* Planning / allocation strategy chips */}
                      <div className="flex items-center gap-2 mb-3">
                        <button className="px-2 py-1 tonal-sky rounded text-xs font-semibold hover:bg-sky-200/90 transition-colors">
                          {getPlanningStrategyName(plan.planning_strategy)}
                        </button>
                        {plan.allocation_strategy && plan.allocation_strategy !== 4 && (
                          <button className="px-2 py-1 tonal-violet rounded text-xs font-semibold hover:bg-violet-200/90 transition-colors">
                            {getAllocationStrategyName(plan.allocation_strategy)}
                          </button>
                        )}
                      </div>

                      {/* Per-plan goals/tasks/agents mini stats */}
                      <div className="grid grid-cols-3 gap-2">
                        <div className="tonal-emerald rounded p-2 text-center">
                          <div className="text-lg font-bold mb-1">
                            {goalCount}
                          </div>
                          <div className="text-xs opacity-90">Goals</div>
                        </div>
                        <div className="tonal-sky rounded p-2 text-center">
                          <div className="text-lg font-bold mb-1">
                            {Array.isArray(plan.task_ids) ? plan.task_ids.length : 0}
                          </div>
                          <div className="text-xs opacity-90">Tasks</div>
                        </div>
                        <div className="tonal-violet rounded p-2 text-center">
                          <div className="text-lg font-bold mb-1">
                            {plan.allocation_artifacts?.final_allocation?.allocations?.length || 0}
                          </div>
                          <div className="text-xs opacity-90">Agents</div>
                        </div>
                      </div>
                    </Card>
                  )
                })}
              </div>
            ) : (
              <EmptyState
                icon={<GitBranch className="w-12 h-12 text-[var(--color-text-muted)]" />}
                title="No Plans Generated"
                description="No plans have been created to achieve this goal yet."
              />
            )}
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-[var(--color-text)]">Assigned Agents</h3>
              <span className="text-sm text-[var(--color-text-muted)] bg-slate-50 px-3 py-1 rounded-full">
                {goalAgents.length} agents
              </span>
            </div>

            {goalAgents.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {goalAgents.map(agent => {
                  const health = robotHealth[agent.agent_id]
                  const isReachable = health?.reachable === true

                  return (
                    <Card key={agent.agent_id} hover className="relative overflow-hidden cursor-pointer" onClick={() => window.open(`/agents?agent=${agent.agent_id}`, '_blank')}>
                      <div className={cn(
                        'absolute top-0 left-0 w-1 h-full',
                        isReachable ? 'bg-emerald-500' : 'bg-red-500'
                      )} />

                      <div className="pl-4">
                        {/* Agent id + type header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'w-8 h-8 rounded-lg flex items-center justify-center',
                              isReachable ? 'bg-emerald-500/10' : 'bg-slate-50'
                            )}>
                              <Bot className={cn('w-4 h-4', isReachable ? 'text-emerald-400' : 'text-[var(--color-text-muted)]')} />
                            </div>
                            <div>
                              <h3 className="font-medium text-[var(--color-text)]">{agent.agent_id}</h3>
                              <p className="text-xs text-[var(--color-text-muted)]">{agent.agent_type}</p>
                            </div>
                          </div>

                          {/* Reachability indicator */}
                          <div className="flex items-center gap-1.5">
                            {isReachable ? (
                              <CheckCircle className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-400" />
                            )}
                            <span className={cn(
                              'text-xs font-medium',
                              isReachable ? 'text-emerald-400' : 'text-red-400'
                            )}>
                              {isReachable ? 'Connected' : 'Unreachable'}
                            </span>
                          </div>
                        </div>

                        {/* Capability tags (first 3 + overflow) */}
                        <div className="flex flex-wrap gap-1 mt-2">
                          {agent.capabilities.slice(0, 3).map((capability: string, index: number) => (
                            <span
                              key={index}
                              className="px-2 py-0.5 bg-slate-100 text-[var(--color-text)] rounded text-xs font-medium"
                            >
                              {capability}
                            </span>
                          ))}
                          {agent.capabilities.length > 3 && (
                            <span className="px-2 py-0.5 bg-slate-100 text-[var(--color-text-secondary)] rounded text-xs">
                              +{agent.capabilities.length - 3} more
                            </span>
                          )}
                        </div>

                        {/* Host:port (+ latency when known) */}
                        <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-200">
                          <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                            <span className="font-mono">
                              {agent.task_server_info?.host}:{agent.task_server_info?.port}
                            </span>
                            {health?.latency_ms && (
                              <span className="text-emerald-400">({Math.round(health.latency_ms)}ms)</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                  )
                })}
              </div>
            ) : (
              <EmptyState
                icon={<Bot className="w-12 h-12 text-[var(--color-text-muted)]" />}
                title="No Agents Assigned"
                description="No agents have been assigned to solve this goal yet."
              />
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}

/**
 * Simple form modal to create a goal from a free-text description.
 * @param props.isOpen - Modal visibility.
 * @param props.onClose - Close handler (also clears draft on success).
 */
function CreateGoalModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  // Controlled textarea value for the new goal description.
  const [description, setDescription] = useState('')
  // Used to invalidate the goals list after a successful create.
  const queryClient = useQueryClient()

  // POST /goals then refresh list + close + reset form.
  const mutation = useMutation({
    mutationFn: goalsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      onClose()
      setDescription('')
    },
  })

  /**
   * Prevent default form submit and fire the create mutation.
   * @param e - Form submit event.
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({ description })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Goal">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
            Goal Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you want the agents to accomplish..."
            rows={4}
            className="w-full px-4 py-3 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 resize-none"
            required
          />
        </div>

        {mutation.error && (
          <p className="text-sm text-red-400">{(mutation.error as Error).message}</p>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create Goal'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

/**
 * Goals route (`/goals`): searchable goal grid with create/delete and detail modal.
 * @returns Goals page layout.
 */
export function Goals() {
  // Create-goal modal visibility.
  const [isModalOpen, setIsModalOpen] = useState(false)
  // Goal id shown in GoalDetailsModal (null = closed).
  const [plansModalGoal, setPlansModalGoal] = useState<number | null>(null)
  // Description substring filter.
  const [searchTerm, setSearchTerm] = useState('')
  // Sort key (created_date currently proxies to goal_id).
  const [sortBy, setSortBy] = useState<'goal_id' | 'created_date'>('goal_id')
  // Ascending vs descending (default newest-first by id).
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  // Invalidate goals after delete.
  const queryClient = useQueryClient()

  const { data: goals = [], isLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: goalsApi.list,
  })

  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: plansApi.list,
  })

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
  })

  // Load planner methods so plan chips can show human strategy names.
  const { data: planners = [] } = useQuery({
    queryKey: ['planners'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'planner')),
  })

  // Load allocator methods for the same reason.
  const { data: allocators = [] } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  // Seed module-level strategy name maps whenever method lists refresh.
  useEffect(() => {
    setMethodData(planners, allocators)
  }, [planners, allocators])

  /**
   * Count plans that include the given goal id.
   * @param goalId - Goal to count plans for.
   */
  const getPlansCountForGoal = (goalId: number) => {
    return plans.filter(plan => plan.goal_ids.includes(goalId)).length
  }

  /**
   * Count unique agents assigned to tasks across plans for a goal.
   * @param goalId - Goal to count agents for.
   */
  const getAgentsCountForGoal = (goalId: number) => {
    const goalPlans = plans.filter(plan => plan.goal_ids.includes(goalId))
    const uniqueAgents = new Set<string>()

    goalPlans.forEach(plan => {
      const planTasks = tasks.filter(task => task.plan_id === plan.plan_id && task.agent_id)
      planTasks.forEach(task => {
        if (task.agent_id) {
          uniqueAgents.add(task.agent_id)
        }
      })
    })

    return uniqueAgents.size
  }

  const deleteMutation = useMutation({
    mutationFn: goalsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
    },
  })

  // Filter and sort goals
  const filteredAndSortedGoals = useMemo(() => {
    let filtered = goals

    // Apply search filter
    if (searchTerm.trim()) {
      filtered = filtered.filter(goal =>
        goal.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      let aValue: number
      let bValue: number

      if (sortBy === 'goal_id') {
        aValue = a.goal_id
        bValue = b.goal_id
      } else {
        // Since we don't have created_at, use goal_id as proxy for creation order
        aValue = a.goal_id
        bValue = b.goal_id
      }

      if (sortOrder === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })

    return sorted
  }, [goals, searchTerm, sortBy, sortOrder])

  if (isLoading) {
    return <div className="text-[var(--color-text-secondary)]">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goals"
        meta={
          <>
            {filteredAndSortedGoals.length} of {goals.length}
            {searchTerm && ` · “${searchTerm}”`}
          </>
        }
        actions={
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4" />
            Create Goal
          </Button>
        }
      />

      {/* Search and Sort Controls */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--color-text-secondary)]" />
          <input
            type="text"
            placeholder="Search goals by description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
          />
        </div>

        {/* Sort field + direction toggle */}
        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'goal_id' | 'created_date')}
            className="px-3 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
          >
            <option value="goal_id">ID</option>
            <option value="created_date">Date Created</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-3 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] hover:bg-slate-100 transition-colors flex items-center gap-1"
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Goals card grid (or empty / no-match states) */}
      {filteredAndSortedGoals.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredAndSortedGoals.map((goal) => (
            <Card key={goal.goal_id} hover className="group relative overflow-hidden p-0 cursor-pointer"
                  onClick={() => setPlansModalGoal(goal.goal_id)}>
              {/* Top accent bar */}
              <div className="h-1 bg-gradient-to-r from-violet-500 via-cyan-500 to-violet-500 opacity-60 group-hover:opacity-100 transition-opacity" />

              <div className="p-5">
                {/* Goal id chip + hover delete */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <span className="tonal-goal-id">G{goal.goal_id}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteMutation.mutate(goal.goal_id)
                    }}
                    className="text-red-400 hover:text-red-600 hover:bg-red-50 p-1.5 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>

                {/* Goal Description (3-line clamp) */}
                <p className="text-sm text-slate-700 leading-relaxed line-clamp-3 mb-4">
                  {goal.description}
                </p>

                {/* Tasks / plans / agents count chips */}
                <div className="flex items-center gap-2">
                  <span className="tonal-sky">
                    {goal.task_ids.length} tasks
                  </span>
                  <span className="tonal-emerald">
                    {getPlansCountForGoal(goal.goal_id)} plans
                  </span>
                  <span className="tonal-violet">
                    {getAgentsCountForGoal(goal.goal_id)} agents
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : goals.length === 0 ? (
        <EmptyState
          icon={<Target className="w-8 h-8" />}
          title="No goals created"
          description="Create your first goal to define what you want your agents to accomplish."
          action={
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus className="w-4 h-4" />
              Create Goal
            </Button>
          }
        />
      ) : (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          <Search className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium text-[var(--color-text-secondary)] mb-2">No goals match your search</p>
          <p className="text-[var(--color-text-muted)] mb-4">Try adjusting your search terms or clearing the filter</p>
          <Button
            variant="secondary"
            onClick={() => setSearchTerm('')}
            className="mr-2"
          >
            Clear Search
          </Button>
        </div>
      )}

      <CreateGoalModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      <GoalDetailsModal
        goalId={plansModalGoal}
        isOpen={plansModalGoal !== null}
        onClose={() => setPlansModalGoal(null)}
      />
    </div>
  )
}
