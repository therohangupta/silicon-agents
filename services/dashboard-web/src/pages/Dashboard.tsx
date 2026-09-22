/**
 * @fileoverview Mission Control home page: fleet summary stats and recent tasks.
 *
 * Pulls agents, goals, plans, tasks, and agent health via TanStack Query, derives
 * online-agent / completed / in-progress counts, and links stat cards into deeper pages.
 */

// Server-state queries for fleet entities.
import { useQuery } from '@tanstack/react-query'
// Navigate on card / row clicks.
import { useNavigate } from 'react-router-dom'
// Lucide icons for stat cards and activity rows.
import { Bot, Target, GitBranch, CheckCircle, Clock, AlertCircle } from 'lucide-react'
// Frosted card surface.
import { Card } from '../components/common/Card'
// Page title block.
import { PageHeader } from '../components/layout/PageHeader'
// REST helpers + realtime invalidation hook.
import { agentsApi, goalsApi, plansApi, tasksApi, useRealtimeUpdates } from '../lib/api'
// Class merge helper.
import { cn } from '../lib/utils'
// Task type for recent activity list.
import type { Task } from '../types'

/**
 * Clickable summary metric card with icon wash and optional subtitle.
 *
 * @param props - StatCard props.
 * @param props.icon - Lucide icon component.
 * @param props.label - Metric label under the value.
 * @param props.value - Primary numeric/string value.
 * @param props.subValue - Optional secondary caption.
 * @param props.color - Tailwind `bg-*` color token used for icon wash.
 * @param props.onClick - Optional navigation handler.
 */
function StatCard({
  icon: Icon,
  label,
  value,
  subValue,
  color,
  onClick,
}: {
  icon: typeof Bot
  label: string
  value: number | string
  subValue?: string
  color: string
  onClick?: () => void
}) {
  return (
    // Hoverable card; pointer when clickable.
    <Card hover className={cn('relative overflow-hidden', onClick && 'cursor-pointer')} onClick={onClick}>
      {/* Soft colored blur orb in the top-right corner. */}
      <div className={cn('absolute top-0 right-0 w-28 h-28 rounded-full blur-3xl opacity-[0.07]', color)} />
      {/* Foreground content above the orb. */}
      <div className="relative">
        {/* Icon well using a translucent tint of `color`. */}
        <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center mb-3', color.replace('bg-', 'bg-').concat('/10'))}>
          <Icon className={cn('w-[18px] h-[18px]', color.replace('bg-', 'text-'))} />
        </div>
        {/* Big metric value. */}
        <p className="text-2xl font-bold text-[var(--color-text)] mb-0.5 tracking-tight">{value}</p>
        {/* Metric label. */}
        <p className="text-sm text-[var(--color-text-secondary)]">{label}</p>
        {/* Optional secondary caption. */}
        {subValue && <p className="text-xs text-[var(--color-text-muted)] mt-1">{subValue}</p>}
      </div>
    </Card>
  )
}

/**
 * Scrollable list of the 50 newest tasks with plan/agent chips and status.
 *
 * @param props - RecentActivity props.
 * @param props.tasks - All tasks from the Tasks API.
 * @param props.plans - All plans (for navigation lookup by plan_id).
 */
function RecentActivity({ tasks, plans }: { tasks: Task[]; plans: any[] }) {
  // Router navigate for clicking into plan task tabs.
  const navigate = useNavigate()
  // Newest task_ids first, capped at 50 rows.
  const recentTasks = [...tasks]
    .sort((a, b) => b.task_id - a.task_id)
    .slice(0, 50)

  // plan_id → plan object for O(1) navigation.
  const planMap = plans.reduce((acc, plan) => {
    acc[plan.plan_id] = plan
    return acc
  }, {} as Record<number, any>)

  /**
   * Humanize a raw task status string for the badge label.
   * @param status - API status value.
   * @returns Display label.
   */
  const getTaskStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed'
      case 'in_progress': return 'In Progress'
      case 'failed': return 'Failed'
      case 'pending': return 'Pending'
      case 'not_executed': return 'Not Executed'
      case 'cancelled': return 'Cancelled'
      default: return status.charAt(0).toUpperCase() + status.slice(1)
    }
  }

  /**
   * Open the owning plan's tasks tab when the task has a plan_id.
   * @param task - Clicked task row.
   */
  const handleTaskClick = (task: Task) => {
    if (task.plan_id) {
      const plan = planMap[task.plan_id]
      if (plan) {
        navigate(`/plans/${plan.plan_id}?tab=tasks`)
      }
    }
  }

  return (
    <Card>
      {/* Section title. */}
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Recently Created Tasks</h3>
      {/* Scrollable activity list. */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {recentTasks.map((task) => (
          <div
            key={task.task_id}
            className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 hover:bg-slate-50 cursor-pointer transition-colors duration-150"
            onClick={() => handleTaskClick(task)}
          >
            {/* Description + chips. */}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[var(--color-text)] truncate">{task.description}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {/* Plan id chip. */}
                <span className="tonal-plan-id">P{task.plan_id}</span>
                {/* Task id chip. */}
                <span className="tonal-sky font-mono">#{task.task_id}</span>
                {/* Agent chip or Unallocated placeholder. */}
                {task.agent_id ? (
                  <span className="tonal-violet font-mono flex items-center gap-1">
                    <Bot className="w-3 h-3" />
                    {task.agent_id}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 ring-1 ring-slate-200/80 text-xs">
                    Unallocated
                  </span>
                )}
              </div>
            </div>
            {/* Status badge with icon. */}
            <span className={cn(
              'shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5',
              task.status === 'completed' ? 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200/80' :
              task.status === 'in_progress' ? 'bg-amber-50 text-amber-800 ring-1 ring-amber-200/80' :
              task.status === 'failed' ? 'bg-red-50 text-red-800 ring-1 ring-red-200/80' :
              'bg-slate-100 text-slate-600 ring-1 ring-slate-200/80'
            )}>
              {task.status === 'completed' ? <CheckCircle className="w-3 h-3" /> :
               task.status === 'in_progress' ? <Clock className="w-3 h-3" /> :
               task.status === 'failed' ? <AlertCircle className="w-3 h-3" /> :
               <Clock className="w-3 h-3" />}
              {getTaskStatusText(task.status)}
            </span>
          </div>
        ))}
        {/* Empty list placeholder. */}
        {recentTasks.length === 0 && (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-8">No recent activity</p>
        )}
      </div>
    </Card>
  )
}

/**
 * Dashboard route component (`/`).
 *
 * @returns Stats grid + recent activity section.
 */
export function Dashboard() {
  // Ensure realtime invalidation is connected while viewing the home page.
  useRealtimeUpdates()
  // Navigation for stat card clicks.
  const navigate = useNavigate()

  // Registered agents list.
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
  })

  // Reachability map from `/api/agents/health/all`.
  const { data: robotHealth } = useQuery({
    queryKey: ['agent-health'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/agents/health/all')
        const data = await response.json()
        const healthMap: Record<string, { reachable: boolean }> = {}
        for (const health of data.agents || []) {
          healthMap[health.agent_id] = { reachable: health.reachable }
        }
        return healthMap
      } catch (error) {
        console.error('Failed to fetch agent health:', error)
        return {}
      }
    },
  })

  // Goals count for the Goals stat card.
  const { data: goals = [] } = useQuery({
    queryKey: ['goals'],
    queryFn: goalsApi.list,
  })

  // Plans count + lookup for recent activity navigation.
  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: plansApi.list,
  })

  // All tasks for activity feed and completion counts.
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list(),
  })

  // Agents that look healthy in status AND are reachable (or health unknown).
  const onlineAgents = agents.filter(r => {
    const isStatusOk = r.status && r.status !== 'unknown' && r.status !== 'error' && r.status !== 'stopped'
    const isReachable = robotHealth ? robotHealth[r.agent_id]?.reachable === true : true
    return isStatusOk && isReachable
  })
  // Completed task count for the green card.
  const completedTasks = tasks.filter(t => t.status === 'completed')
  // In-progress count used in the Plans card subtitle.
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress')

  return (
    <div className="space-y-6">
      {/* Welcome header with branded gradient text. */}
      <PageHeader
        title={
          <>
            Welcome to <span className="gradient-text">Mission Control</span>
          </>
        }
        description="Fleet status, task throughput, and recent activity in one place."
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Bot}
          label="Active Agents"
          value={onlineAgents.length}
          subValue={`${agents.length} total registered`}
          color="bg-cyber-500"
          onClick={() => navigate('/agents')}
        />
        <StatCard
          icon={Target}
          label="Goals"
          value={goals.length}
          subValue="Pending completion"
          color="bg-violet-500"
          onClick={() => navigate('/goals')}
        />
        <StatCard
          icon={GitBranch}
          label="Plans"
          value={plans.length}
          subValue={`${inProgressTasks.length} tasks running`}
          color="bg-amber-500"
          onClick={() => navigate('/plans')}
        />
        <StatCard
          icon={CheckCircle}
          label="Completed Tasks"
          value={completedTasks.length}
          subValue={`${tasks.length} total tasks`}
          color="bg-emerald-500"
          onClick={() => navigate('/plans')}
        />
      </div>

      {/* Recent Activity */}
      <RecentActivity tasks={tasks} plans={plans} />
    </div>
  )
}
