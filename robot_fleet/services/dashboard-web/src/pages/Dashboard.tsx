import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Bot, Target, GitBranch, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { robotsApi, goalsApi, plansApi, tasksApi, useRealtimeUpdates } from '../lib/api'
import { cn } from '../lib/utils'
import type { Task } from '../types'

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
    <Card hover className={cn('relative overflow-hidden', onClick && 'cursor-pointer')} onClick={onClick}>
      <div className={cn('absolute top-0 right-0 w-28 h-28 rounded-full blur-3xl opacity-[0.07]', color)} />
      <div className="relative">
        <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center mb-3', color.replace('bg-', 'bg-').concat('/10'))}>
          <Icon className={cn('w-[18px] h-[18px]', color.replace('bg-', 'text-'))} />
        </div>
        <p className="text-2xl font-bold text-[var(--color-text)] mb-0.5 tracking-tight">{value}</p>
        <p className="text-sm text-[var(--color-text-secondary)]">{label}</p>
        {subValue && <p className="text-xs text-[var(--color-text-muted)] mt-1">{subValue}</p>}
      </div>
    </Card>
  )
}

function RecentActivity({ tasks, plans }: { tasks: Task[]; plans: any[] }) {
  const navigate = useNavigate()
  const recentTasks = [...tasks]
    .sort((a, b) => b.task_id - a.task_id)
    .slice(0, 50)

  const planMap = plans.reduce((acc, plan) => {
    acc[plan.plan_id] = plan
    return acc
  }, {} as Record<number, any>)

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
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Recently Created Tasks</h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {recentTasks.map((task) => (
          <div
            key={task.task_id}
            className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 hover:bg-slate-50 cursor-pointer transition-colors duration-150"
            onClick={() => handleTaskClick(task)}
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[var(--color-text)] truncate">{task.description}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className="tonal-plan-id">P{task.plan_id}</span>
                <span className="tonal-sky font-mono">#{task.task_id}</span>
                {task.robot_id ? (
                  <span className="tonal-violet font-mono flex items-center gap-1">
                    <Bot className="w-3 h-3" />
                    {task.robot_id}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 ring-1 ring-slate-200/80 text-xs">
                    Unallocated
                  </span>
                )}
              </div>
            </div>
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
        {recentTasks.length === 0 && (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-8">No recent activity</p>
        )}
      </div>
    </Card>
  )
}

export function Dashboard() {
  useRealtimeUpdates()
  const navigate = useNavigate()

  const { data: robots = [] } = useQuery({
    queryKey: ['robots'],
    queryFn: () => robotsApi.list(),
  })

  const { data: robotHealth } = useQuery({
    queryKey: ['robot-health'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/robots/health/all')
        const data = await response.json()
        const healthMap: Record<string, { reachable: boolean }> = {}
        for (const health of data.robots || []) {
          healthMap[health.robot_id] = { reachable: health.reachable }
        }
        return healthMap
      } catch (error) {
        console.error('Failed to fetch robot health:', error)
        return {}
      }
    },
  })

  const { data: goals = [] } = useQuery({
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

  const onlineRobots = robots.filter(r => {
    const isStatusOk = r.status && r.status !== 'unknown' && r.status !== 'error' && r.status !== 'stopped'
    const isReachable = robotHealth ? robotHealth[r.robot_id]?.reachable === true : true
    return isStatusOk && isReachable
  })
  const completedTasks = tasks.filter(t => t.status === 'completed')
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress')

  return (
    <div className="space-y-6">
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
          label="Active Robots"
          value={onlineRobots.length}
          subValue={`${robots.length} total registered`}
          color="bg-cyber-500"
          onClick={() => navigate('/robots')}
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
