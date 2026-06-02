import { useCallback, useMemo, useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  Circle,
  Bot,
  ChevronDown,
  ChevronRight,
  Activity,
  ScrollText,
  Play,
  RotateCcw,
} from 'lucide-react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/common/Button'
import { StatusBadge } from '../components/common/StatusBadge'
import { DAGVisualization } from '../components/common/DAGVisualization'
import { TaskIdChip } from '../components/execution/TaskIdChip'
import { RobotExecutionModal } from '../components/execution/RobotExecutionModal'
import { plansApi, tasksApi, robotsApi, methodsApi, metricsApi, useRealtimeUpdates } from '../lib/api'
import { cn, getPlanningStrategyName, getAllocationStrategyName, setMethodData } from '../lib/utils'
import { GatewayRealtimeClient } from '@robot-fleet/client-sdk'
import type { Task } from '../types'

// ---------------------------------------------------------------------------
// Event log types
// ---------------------------------------------------------------------------

interface LogEntry {
  ts: number
  message: string
  level: 'info' | 'success' | 'error'
}

interface MetricRow {
  timestamp?: string
  event_type?: string
  entity_id?: string
  duration_ms?: number
  success?: boolean
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatElapsed(ms: number): string {
  const secs = Math.floor(ms / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  const remainder = secs % 60
  return `${mins}m ${remainder}s`
}

function formatTimestamp(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function parsePersistedEventLog(serverLogs: string | undefined, planId: number, planTaskIds: Set<number>): LogEntry[] {
  if (!serverLogs || serverLogs.trim().length === 0) return []

  const base = Date.now()
  const rawLines = serverLogs
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)

  // Merge continuation lines back into their parent event.
  const startsNewEvent = (line: string): boolean => {
    if (/^(Plan|Task)\b/.test(line)) return true
    if (/^\d{4}-\d{2}-\d{2}/.test(line)) return true
    return false
  }

  const merged: string[] = []
  for (const line of rawLines) {
    if (merged.length === 0 || startsNewEvent(line)) {
      merged.push(line)
    } else {
      merged[merged.length - 1] += `\n${line}`
    }
  }

  const isExecutionLifecycleLine = (line: string): boolean => {
    // Only accept concrete execution lifecycle messages.
    // Drop planner/generator chatter like "Task Given by Planner".
    return (
      /\bPlan\s+#?\d+\s+execution\s+started\b/i.test(line) ||
      /\bPlan\s+#?\d+\s+(completed|failed)\b/i.test(line) ||
      /\bTask\s+#?\d+\s+(started|completed|failed)\b/i.test(line)
    )
  }

  const lines = merged
    .filter(isExecutionLifecycleLine)
    .filter((line) => {
      // If a line explicitly references a plan id, keep only current plan.
      const planMatch = line.match(/\bPlan\s+#?(\d+)\b/i)
      if (planMatch) return Number(planMatch[1]) === planId

      // If a line explicitly references a task id, keep only tasks in this plan.
      const taskMatch = line.match(/\bTask\s+#?(\d+)\b/i)
      if (taskMatch) return planTaskIds.has(Number(taskMatch[1]))

      // For generic lines, keep them.
      return true
    })
    .slice(-200)

  return lines
    .map((line, idx) => {
      const lower = line.toLowerCase()
      const level: LogEntry['level'] =
        lower.includes('error') || lower.includes('fail') ? 'error' :
        lower.includes('success') || lower.includes('complete') ? 'success' :
        'info'
      return {
        ts: base - (lines.length - idx) * 1000,
        message: line,
        level,
      }
    })
    .reverse()
}

function buildEventLogFromMetrics(metrics: MetricRow[], tasks: Task[], planId: number): LogEntry[] {
  if (!metrics || metrics.length === 0) return []
  const taskById = new Map(tasks.map(t => [String(t.task_id), t]))
  const rows = metrics
    .filter(m => {
      if (m.event_type === 'plan_execution') return m.entity_id === String(planId)
      if (m.event_type === 'task_execution') return !!m.entity_id && taskById.has(String(m.entity_id))
      return false
    })
    .map(m => {
      const ts = m.timestamp ? new Date(m.timestamp).getTime() : Date.now()
      if (m.event_type === 'plan_execution') {
        const secs = Math.max(0, Math.round((m.duration_ms ?? 0) / 1000))
        return {
          ts,
          level: (m.success === false ? 'error' : 'success') as LogEntry['level'],
          message: `Plan ${planId} ${m.success === false ? 'failed' : 'completed'}${secs ? ` in ${secs}s` : ''}`,
        }
      }
      const taskId = String(m.entity_id ?? '')
      const task = taskById.get(taskId)
      const secs = Math.max(0, Math.round((m.duration_ms ?? 0) / 1000))
      return {
        ts,
        level: (m.success === false ? 'error' : 'success') as LogEntry['level'],
        message: `Task #${taskId}${task?.robot_id ? ` (${task.robot_id})` : ''} ${m.success === false ? 'failed' : 'completed'}${secs ? ` in ${secs}s` : ''}${task?.result ? `: ${task.result}` : ''}`,
      }
    })
    .sort((a, b) => b.ts - a.ts)

  return rows.slice(0, 200)
}

function getExpandedEventMessage(message: string, taskMap: Map<number, Task>): string {
  if (!message.includes('…')) return message
  const m = message.match(/Task #(\d+)\s+(completed|failed)\s+on\s+([^:\n]+):[\s\S]*/i)
  if (!m) return message

  const taskId = Number(m[1])
  const status = m[2].toLowerCase()
  const robot = m[3]
  const task = taskMap.get(taskId)
  if (!task?.result) return message

  if (status === 'completed') {
    return `Task #${taskId} completed on ${robot}: ${task.result}`
  }
  return `Task #${taskId} failed on ${robot}: ${task.result}`
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function Execution() {
  useRealtimeUpdates()
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Tracks whether execution was started during this session (so WS connects immediately)
  const [executionStarted, setExecutionStarted] = useState(false)

  const startMutation = useMutation({
    mutationFn: () => plansApi.start(Number(planId)),
    onSuccess: () => {
      setExecutionStarted(true)
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      queryClient.invalidateQueries({ queryKey: ['plans'] })
    },
  })

  const copyAndRetryMutation = useMutation({
    mutationFn: () => plansApi.copy(Number(planId), {
      name: `${plan?.name || `Plan #${planId}`} (Retry)`,
      description: plan?.description || 'Retry of failed plan',
    }),
    onSuccess: (newPlan: any) => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      navigate(`/plans/${newPlan.plan_id}/execute`)
    },
  })

  // UI state
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['fleet', 'queue'])
  )
  const [selectedRobot, setSelectedRobot] = useState<string | null>(null)
  const [eventLog, setEventLog] = useState<LogEntry[]>([])
  const [expandedEventItems, setExpandedEventItems] = useState<Set<number>>(new Set())

  // Elapsed time tracking: taskId -> startTime (Date.now())
  const taskStartTimes = useRef<Map<number, number>>(new Map())
  const [elapsedTimes, setElapsedTimes] = useState<Map<number, number>>(new Map())

  // Wall-clock timer for the whole execution
  const executionStartRef = useRef<number | null>(null)
  const [wallElapsed, setWallElapsed] = useState(0)

  // WebSocket tasks state (from dedicated execution WS)
  const [wsTasks, setWsTasks] = useState<Task[] | null>(null)
  const prevTasksRef = useRef<Map<number, Task>>(new Map())

  // ---------------------------------------------------------------------------
  // Data fetching (initial load + fallback)
  // ---------------------------------------------------------------------------

  const { data: plan } = useQuery({
    queryKey: ['plan', planId],
    queryFn: () => plansApi.get(Number(planId)),
    enabled: !!planId,
    refetchInterval: (query) => {
      const p = query.state.data
      return p?.execution_status === 'executing' ? 3000 : false
    },
  })
  const planExecutionStatus = plan?.execution_status ?? 'not_executed'

  const isPreview = !executionStarted &&
    plan?.execution_status !== 'executing' &&
    plan?.execution_status !== 'completed' &&
    plan?.execution_status !== 'failed'

  // Fresh plan route should never inherit previous plan's in-memory log/timers.
  useEffect(() => {
    setExecutionStarted(false)
    setEventLog([])
    setExpandedEventItems(new Set())
    setWsTasks(null)
    setElapsedTimes(new Map())
    prevTasksRef.current = new Map()
    taskStartTimes.current = new Map()
    executionStartRef.current = null
    setWallElapsed(0)
  }, [planId])

  const { data: fetchedTasks = [] } = useQuery({
    queryKey: ['tasks', planId],
    queryFn: () => tasksApi.list({ plan_id: Number(planId) }),
    enabled: !!planId,
  })

  const { data: robots = [] } = useQuery({
    queryKey: ['robots'],
    queryFn: () => robotsApi.list(),
  })

  const { data: planners = [] } = useQuery({
    queryKey: ['planners'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'planner')),
  })

  const { data: allocators = [] } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  const { data: historicalMetrics } = useQuery({
    queryKey: ['metrics', 'execution', planId],
    queryFn: () => metricsApi.list({ service: 'fleet_server', limit: 1000 }),
    enabled: !!planId,
  })

  useEffect(() => {
    setMethodData(planners, allocators)
  }, [planners, allocators])

  // Authoritative task list: prefer WS data when available
  const tasks: Task[] = wsTasks ?? fetchedTasks

  // Task lookup map
  const taskMap = useMemo(() => new Map(tasks.map(t => [t.task_id, t])), [tasks])

  // ---------------------------------------------------------------------------
  // Dedicated execution WebSocket
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!planId || isPreview) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsBaseUrl = `${protocol}//${window.location.host}`
    const client = new GatewayRealtimeClient({ wsBaseUrl })

    const currentPlanId = Number(planId)
    const ws = client.connectPlanExecution(currentPlanId, (msg) => {
      if (msg.type === 'tasks_update' && Array.isArray((msg as any).tasks)) {
        const filtered = ((msg as any).tasks as Task[]).filter(
          (t) => Number((t as any).plan_id) === currentPlanId
        )
        setWsTasks(filtered)
      }
    })

    return () => {
      ws.close()
    }
  }, [planId, isPreview])

  // ---------------------------------------------------------------------------
  // Diff tasks on every update → build event log + track elapsed
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const prevMap = prevTasksRef.current
    const newEntries: LogEntry[] = []
    const now = Date.now()

    for (const task of tasks) {
      const prev = prevMap.get(task.task_id)
      if (!prev) continue

      if (prev.status !== task.status) {
        if (task.status === 'in_progress') {
          taskStartTimes.current.set(task.task_id, now)
          newEntries.push({
            ts: now,
            message: `Task #${task.task_id} started on ${task.robot_id ?? '?'}`,
            level: 'info',
          })
        } else if (task.status === 'completed') {
          taskStartTimes.current.delete(task.task_id)
          newEntries.push({
            ts: now,
            message: `Task #${task.task_id} completed on ${task.robot_id ?? '?'}${task.result ? `: ${task.result}` : ''}`,
            level: 'success',
          })
        } else if (task.status === 'failed') {
          taskStartTimes.current.delete(task.task_id)
          newEntries.push({
            ts: now,
            message: `Task #${task.task_id} failed on ${task.robot_id ?? '?'}${task.result ? `: ${task.result}` : ''}`,
            level: 'error',
          })
        }
      }
    }

    if (newEntries.length > 0) {
      setEventLog(prev => [...newEntries.reverse(), ...prev].slice(0, 200))
    }

    // Update prev snapshot
    prevTasksRef.current = new Map(tasks.map(t => [t.task_id, t]))
  }, [tasks])

  // Seed prev tasks ref on first load so the initial state doesn't generate log entries
  useEffect(() => {
    if (fetchedTasks.length > 0 && prevTasksRef.current.size === 0) {
      prevTasksRef.current = new Map(fetchedTasks.map(t => [t.task_id, t]))

      // Seed start times for tasks already in_progress
      const now = Date.now()
      for (const t of fetchedTasks) {
        if (t.status === 'in_progress') {
          taskStartTimes.current.set(t.task_id, now)
        }
      }
    }
  }, [fetchedTasks])

  // Load historical execution log for historical plans.
  useEffect(() => {
    if (planExecutionStatus === 'not_executed') return
    if (eventLog.length > 0) return

    // Prefer structured metrics first (cleaner + better ordering), then fallback to filtered raw logs.
    if (historicalMetrics?.metrics?.length && planId) {
      const fromMetrics = buildEventLogFromMetrics(
        historicalMetrics.metrics as MetricRow[],
        tasks,
        Number(planId)
      )
      if (fromMetrics.length > 0) {
        setEventLog(fromMetrics)
        return
      }
    }

    const numericPlanId = Number(planId)
    const planTaskIds = new Set(tasks.map(t => t.task_id))
    const persisted = parsePersistedEventLog(plan?.server_logs, numericPlanId, planTaskIds)
    if (persisted.length > 0) {
      setEventLog(persisted)
    }
  }, [planExecutionStatus, plan?.server_logs, historicalMetrics, tasks, planId, eventLog.length])

  // ---------------------------------------------------------------------------
  // 1-second timer to tick elapsed counters
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const next = new Map<number, number>()
      taskStartTimes.current.forEach((start, taskId) => {
        next.set(taskId, now - start)
      })
      setElapsedTimes(next)

      // Wall-clock
      if (executionStartRef.current) {
        setWallElapsed(now - executionStartRef.current)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Detect execution start
  useEffect(() => {
    if (!executionStartRef.current && tasks.some(t => t.status === 'in_progress' || t.status === 'completed')) {
      executionStartRef.current = Date.now()
    }
  }, [tasks])

  // ---------------------------------------------------------------------------
  // Derived data
  // ---------------------------------------------------------------------------

  const isCancelled = useCallback((t: Task) =>
    t.status === 'failed' && (t.result?.startsWith('Cancelled:') || t.result?.startsWith('Skipped:')),
    []
  )

  const taskGroups = useMemo(() => ({
    executing: tasks.filter(t => t.status === 'in_progress'),
    pending: tasks.filter(t => t.status === 'pending'),
    completed: tasks.filter(t => t.status === 'completed'),
    failed: tasks.filter(t => t.status === 'failed' && !isCancelled(t)),
    cancelled: tasks.filter(t => isCancelled(t)),
  }), [tasks, isCancelled])

  const totalTasks = tasks.length
  const completedCount = taskGroups.completed.length
  const executingCount = taskGroups.executing.length
  const pendingCount = taskGroups.pending.length
  const failedCount = taskGroups.failed.length
  const cancelledCount = taskGroups.cancelled.length

  const overallStatus = useMemo(() => {
    if ((failedCount > 0 || cancelledCount > 0) && executingCount === 0 && pendingCount === 0) return 'failed'
    if (completedCount === totalTasks && totalTasks > 0) return 'completed'
    if (executingCount > 0) return 'in_progress'
    return 'pending'
  }, [totalTasks, completedCount, executingCount, pendingCount, failedCount, cancelledCount])

  // Group tasks by robot for the fleet table
  const robotRows = useMemo(() => {
    const byRobot = new Map<string, Task[]>()
    for (const task of tasks) {
      const rid = task.robot_id ?? '__unassigned__'
      if (!byRobot.has(rid)) byRobot.set(rid, [])
      byRobot.get(rid)!.push(task)
    }

    return Array.from(byRobot.entries())
      .filter(([rid]) => rid !== '__unassigned__')
      .map(([rid, rTasks]) => {
        const robot = robots.find(r => r.robot_id === rid)
        const current = rTasks.find(t => t.status === 'in_progress')
        const succeeded = rTasks.filter(t => t.status === 'completed').length
        const failed = rTasks.filter(t => t.status === 'failed' && !isCancelled(t)).length
        const cancelled = rTasks.filter(t => isCancelled(t)).length
        const total = rTasks.length
        const finished = succeeded + failed + cancelled === total
        const hasFailed = failed > 0 || cancelled > 0

        return {
          robotId: rid,
          robotType: robot?.robot_type ?? rTasks[0]?.robot_type ?? 'unknown',
          taskServerInfo: robot?.task_server_info ?? null,
          currentTask: current ?? null,
          succeededCount: succeeded,
          failedCount: failed,
          cancelledCount: cancelled,
          totalCount: total,
          finished,
          hasFailed,
          tasks: rTasks,
        }
      })
      .sort((a, b) => {
        const score = (r: typeof a) => r.currentTask ? 0 : r.finished ? (r.hasFailed ? 3 : 2) : 1
        return score(a) - score(b)
      })
  }, [tasks, robots])

  // Pending tasks for the queue table
  const pendingTasksSorted = useMemo(() => {
    return [...taskGroups.pending].sort((a, b) => {
      const aReady = a.dependency_task_ids.every(d => taskMap.get(d)?.status === 'completed')
      const bReady = b.dependency_task_ids.every(d => taskMap.get(d)?.status === 'completed')
      if (aReady && !bReady) return -1
      if (!aReady && bReady) return 1
      return a.task_id - b.task_id
    })
  }, [taskGroups.pending, taskMap])

  // Completed tasks for the completed table (most recent first)
  const completedTasksSorted = useMemo(() => {
    return [...taskGroups.completed, ...taskGroups.failed, ...taskGroups.cancelled].reverse()
  }, [taskGroups.completed, taskGroups.failed, taskGroups.cancelled])

  // ---------------------------------------------------------------------------
  // Section toggle
  // ---------------------------------------------------------------------------

  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(section)) next.delete(section)
      else next.add(section)
      return next
    })
  }, [])

  // Auto-expand completed section when plan finishes
  useEffect(() => {
    if (overallStatus === 'completed' || overallStatus === 'failed') {
      setExpandedSections(prev => new Set([...prev, 'completed']))
    }
  }, [overallStatus])

  // ---------------------------------------------------------------------------
  // Helpers for dependency readiness
  // ---------------------------------------------------------------------------

  const depsReady = useCallback((task: Task) =>
    task.dependency_task_ids.every(d => taskMap.get(d)?.status === 'completed'),
    [taskMap]
  )

  // ---------------------------------------------------------------------------
  // Selected robot data for modal
  // ---------------------------------------------------------------------------

  const selectedRobotRow = selectedRobot
    ? robotRows.find(r => r.robotId === selectedRobot)
    : null

  // ---------------------------------------------------------------------------
  // Progress bar segment widths
  // ---------------------------------------------------------------------------

  const pctCompleted = totalTasks > 0 ? (completedCount / totalTasks) * 100 : 0
  const pctExecuting = totalTasks > 0 ? (executingCount / totalTasks) * 100 : 0
  const pctFailed = totalTasks > 0 ? (failedCount / totalTasks) * 100 : 0
  const pctCancelled = totalTasks > 0 ? (cancelledCount / totalTasks) * 100 : 0

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      <PageHeader
        title="Execution Monitor"
        description={plan?.name || undefined}
        leading={
          <Button
            variant="secondary"
            size="sm"
            className="shrink-0 mt-1"
            onClick={() => navigate(`/plans/${planId}`)}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
        }
        meta={
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="tonal-plan-id">P{planId}</span>
            <span className="tonal-sky">{getPlanningStrategyName(plan?.planning_strategy || 0)}</span>
            <span className="tonal-violet">{getAllocationStrategyName(plan?.allocation_strategy || 0)}</span>
          </div>
        }
        actions={
          <>
            {wallElapsed > 0 && (
              <span className="text-sm font-mono text-[var(--color-text-secondary)] hidden sm:inline-flex items-center">
                <Clock className="w-3.5 h-3.5 mr-1" />
                {formatElapsed(wallElapsed)}
              </span>
            )}
            <StatusBadge status={overallStatus} />
            {isPreview && (
              <Button
                onClick={() => startMutation.mutate()}
                disabled={startMutation.isPending}
                className="flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                {startMutation.isPending ? 'Starting...' : 'Start Execution'}
              </Button>
            )}
            {overallStatus === 'failed' && (
              <Button
                onClick={() => copyAndRetryMutation.mutate()}
                disabled={copyAndRetryMutation.isPending}
                className="flex items-center gap-2 bg-red-100 hover:bg-red-200 text-red-950 border border-red-300"
              >
                <RotateCcw className="w-4 h-4" />
                {copyAndRetryMutation.isPending ? 'Copying...' : 'Copy & Retry'}
              </Button>
            )}
          </>
        }
      />

      {/* Progress Strip */}
      <Card className="!p-4">
        {isPreview && (
          <div className="mb-3 px-3 py-2 mission-panel border-l-[3px] border-l-cyan-500 text-sm text-slate-800">
            Review the task queue below, then click <strong>Start Execution</strong> when ready.
          </div>
        )}
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-[var(--color-text-secondary)]">Overall Progress</span>
          <span className="text-sm font-mono text-[var(--color-text)]">
            {completedCount}/{totalTasks} tasks
          </span>
        </div>
        <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden flex">
          {pctCompleted > 0 && (
            <div
              className="h-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${pctCompleted}%` }}
            />
          )}
          {pctExecuting > 0 && (
            <div
              className="h-full bg-amber-500 animate-pulse transition-all duration-500"
              style={{ width: `${pctExecuting}%` }}
            />
          )}
          {pctFailed > 0 && (
            <div
              className="h-full bg-red-500 transition-all duration-500"
              style={{ width: `${pctFailed}%` }}
            />
          )}
          {pctCancelled > 0 && (
            <div
              className="h-full bg-slate-500/60 transition-all duration-500"
              style={{ width: `${pctCancelled}%` }}
            />
          )}
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="px-2.5 py-1 rounded-full text-xs font-medium tonal-emerald">
            {completedCount} completed
          </span>
          <span className="px-2.5 py-1 rounded-full text-xs font-medium tonal-amber">
            {executingCount} executing
          </span>
          <span className="px-2.5 py-1 rounded-full text-xs font-medium tonal-sky">
            {pendingCount} pending
          </span>
          {failedCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-xs font-medium tonal-red">
              {failedCount} failed
            </span>
          )}
          {cancelledCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-200 text-slate-900 border border-slate-400/70">
              {cancelledCount} cancelled
            </span>
          )}
        </div>
      </Card>

      {/* ================================================================= */}
      {/* Robot Fleet Table                                                  */}
      {/* ================================================================= */}
      <Card>
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('fleet')}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-sky-100 border border-sky-300 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-sky-900" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Robot Fleet</h3>
            <span className="px-2 py-1 tonal-sky rounded text-xs">
              {robotRows.length} robots
            </span>
          </div>
          {expandedSections.has('fleet')
            ? <ChevronDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
            : <ChevronRight className="w-4 h-4 text-[var(--color-text-secondary)]" />}
        </div>

        {expandedSections.has('fleet') && (
          <div className="mt-4">
            {robotRows.length === 0 ? (
              <div className="text-center py-8 text-[var(--color-text-muted)]">
                <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No robots assigned to tasks yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wider border-b border-slate-200">
                      <th className="pb-3 pr-4">Robot</th>
                      <th className="pb-3 pr-4">Current Task</th>
                      <th className="pb-3 pr-4 text-right">Elapsed</th>
                      <th className="pb-3 pr-4 text-center">Progress</th>
                      <th className="pb-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {robotRows.map(row => {
                      const pctOk = row.totalCount > 0 ? (row.succeededCount / row.totalCount) * 100 : 0
                      const pctBad = row.totalCount > 0 ? ((row.failedCount + row.cancelledCount) / row.totalCount) * 100 : 0

                      return (
                      <tr
                        key={row.robotId}
                        className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedRobot(row.robotId)}
                      >
                        {/* Robot */}
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <Bot className="w-4 h-4 text-slate-700 flex-shrink-0" />
                            <span className="font-mono text-slate-900">{row.robotId}</span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 border border-slate-200 text-[var(--color-text-muted)]">
                              {row.robotType}
                            </span>
                          </div>
                        </td>

                        {/* Current Task */}
                        <td className="py-3 pr-4 max-w-xs">
                          {row.currentTask ? (
                            <div className="flex items-center gap-2">
                              <TaskIdChip
                                taskId={row.currentTask.task_id}
                                task={row.currentTask}
                                colorClass="text-amber-900"
                              />
                              <span className="text-[var(--color-text)] truncate">
                                {row.currentTask.description.length > 40
                                  ? row.currentTask.description.slice(0, 40) + '…'
                                  : row.currentTask.description}
                              </span>
                            </div>
                          ) : (
                            <span className="text-[var(--color-text-muted)] italic">
                              {row.finished && row.hasFailed
                                ? `${row.failedCount} failed, ${row.cancelledCount} cancelled`
                                : row.finished
                                  ? 'All tasks complete'
                                  : 'Waiting for deps'}
                            </span>
                          )}
                        </td>

                        {/* Elapsed */}
                        <td className="py-3 pr-4 text-right font-mono text-xs">
                          {row.currentTask && elapsedTimes.has(row.currentTask.task_id) ? (
                            <span className="text-amber-900 font-medium">
                              {formatElapsed(elapsedTimes.get(row.currentTask.task_id)!)}
                            </span>
                          ) : (
                            <span className="text-[var(--color-text-muted)]">—</span>
                          )}
                        </td>

                        {/* Progress */}
                        <td className="py-3 pr-4">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-20 h-1.5 bg-slate-50 rounded-full overflow-hidden flex">
                              {pctOk > 0 && (
                                <div
                                  className="h-full bg-emerald-500 transition-all duration-500"
                                  style={{ width: `${pctOk}%` }}
                                />
                              )}
                              {pctBad > 0 && (
                                <div
                                  className="h-full bg-red-500/70 transition-all duration-500"
                                  style={{ width: `${pctBad}%` }}
                                />
                              )}
                            </div>
                            <span className="text-xs text-[var(--color-text-secondary)] font-mono w-10 text-right">
                              {row.succeededCount}/{row.totalCount}
                            </span>
                          </div>
                        </td>

                        {/* Status */}
                        <td className="py-3 text-center">
                          {row.currentTask ? (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium tonal-amber">
                              Executing
                            </span>
                          ) : row.finished && row.hasFailed ? (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium tonal-red">
                              Failed
                            </span>
                          ) : row.finished ? (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium tonal-emerald">
                              Done
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-200 text-slate-800 border border-slate-400/60">
                              Waiting
                            </span>
                          )}
                        </td>
                      </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ================================================================= */}
      {/* Task Queue                                                         */}
      {/* ================================================================= */}
      <Card>
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('queue')}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-amber-100 border border-amber-300 rounded-lg flex items-center justify-center">
              <Clock className="w-4 h-4 text-amber-900" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Task Queue</h3>
            <span className="px-2 py-1 tonal-amber rounded text-xs">
              {pendingCount} pending
            </span>
          </div>
          {expandedSections.has('queue')
            ? <ChevronDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
            : <ChevronRight className="w-4 h-4 text-[var(--color-text-secondary)]" />}
        </div>

        {expandedSections.has('queue') && (
          <div className="mt-4">
            {pendingTasksSorted.length === 0 ? (
              <div className="text-center py-6 text-[var(--color-text-muted)]">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>{totalTasks === 0 ? 'Loading tasks…' : 'All tasks dispatched'}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wider border-b border-slate-200">
                      <th className="pb-3 pr-4">Task</th>
                      <th className="pb-3 pr-4">Description</th>
                      <th className="pb-3 pr-4">Assigned Robot</th>
                      <th className="pb-3 pr-4">Blocked By</th>
                      <th className="pb-3 text-center">Ready</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingTasksSorted.map(task => {
                      const ready = depsReady(task)
                      const blockers = task.dependency_task_ids.filter(
                        d => taskMap.get(d)?.status !== 'completed'
                      )
                      return (
                        <tr key={task.task_id} className="border-b border-slate-200 hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4">
                            <TaskIdChip taskId={task.task_id} task={task} />
                          </td>
                          <td className="py-2.5 pr-4 text-[var(--color-text)] max-w-sm truncate">
                            {task.description}
                          </td>
                          <td className="py-2.5 pr-4">
                            {task.robot_id ? (
                              <span className="font-mono text-xs text-slate-800">{task.robot_id}</span>
                            ) : (
                              <span className="text-xs text-[var(--color-text-muted)]">—</span>
                            )}
                          </td>
                          <td className="py-2.5 pr-4">
                            {blockers.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {blockers.map(d => (
                                  <TaskIdChip key={d} taskId={d} task={taskMap.get(d)} colorClass="text-[var(--color-text-secondary)]" />
                                ))}
                              </div>
                            ) : (
                              <span className="text-xs text-[var(--color-text-muted)]">—</span>
                            )}
                          </td>
                          <td className="py-2.5 text-center">
                            {ready ? (
                              <CheckCircle className="w-4 h-4 text-emerald-700 mx-auto" />
                            ) : (
                              <Circle className="w-4 h-4 text-[var(--color-text-muted)] mx-auto" />
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ================================================================= */}
      {/* Completed / Failed Tasks                                           */}
      {/* ================================================================= */}
      <Card>
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('completed')}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-emerald-100 border border-emerald-300 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-emerald-800" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Completed & Failed Tasks</h3>
            {completedCount > 0 && (
              <span className="px-2 py-1 tonal-emerald rounded text-xs">
                {completedCount} completed
              </span>
            )}
            {(failedCount + cancelledCount) > 0 && (
              <span className="px-2 py-1 tonal-red rounded text-xs">
                {failedCount + cancelledCount} failed
              </span>
            )}
          </div>
          {expandedSections.has('completed')
            ? <ChevronDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
            : <ChevronRight className="w-4 h-4 text-[var(--color-text-secondary)]" />}
        </div>

        {expandedSections.has('completed') && (
          <div className="mt-4">
            {completedTasksSorted.length === 0 ? (
              <div className="text-center py-6 text-[var(--color-text-muted)]">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No completed tasks yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wider border-b border-slate-200">
                      <th className="pb-3 pr-4">Task</th>
                      <th className="pb-3 pr-4">Robot</th>
                      <th className="pb-3 pr-4">Description</th>
                      <th className="pb-3 pr-4">Result</th>
                      <th className="pb-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedTasksSorted.map(task => (
                      <tr
                        key={task.task_id}
                        className={cn(
                          'border-b border-slate-200 hover:bg-slate-50 transition-colors',
                          task.status === 'failed' && 'border-l-2 border-l-red-500'
                        )}
                      >
                        <td className="py-2.5 pr-4">
                          <TaskIdChip
                            taskId={task.task_id}
                            colorClass={task.status === 'failed' ? 'text-red-800' : 'text-emerald-800'}
                            showTooltip={false}
                          />
                        </td>
                        <td className="py-2.5 pr-4">
                          {task.robot_id ? (
                            <span
                              className={cn(
                                'font-mono text-xs font-medium',
                                task.status === 'failed' ? 'text-red-950' : 'text-slate-900'
                              )}
                            >
                              {task.robot_id}
                            </span>
                          ) : (
                            <span className="text-xs text-[var(--color-text-muted)]">—</span>
                          )}
                        </td>
                        <td className="py-2.5 pr-4 text-[var(--color-text)] max-w-xs truncate">
                          {task.description}
                        </td>
                        <td className="py-2.5 pr-4 max-w-sm">
                          {task.result ? (
                            <details className="group">
                              <summary className="text-xs text-[var(--color-text-secondary)] cursor-pointer hover:text-[var(--color-text)] transition-colors truncate max-w-[200px]">
                                {task.result.length > 60 ? task.result.slice(0, 60) + '…' : task.result}
                              </summary>
                              <pre className="mt-2 text-xs text-[var(--color-text)] whitespace-pre-wrap font-mono bg-surface/80 rounded p-2 border border-slate-200">
                                {task.result}
                              </pre>
                            </details>
                          ) : (
                            <span className="text-xs text-[var(--color-text-muted)]">—</span>
                          )}
                        </td>
                        <td className="py-2.5 text-center">
                          <StatusBadge status={task.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ================================================================= */}
      {/* DAG Visualization                                                  */}
      {/* ================================================================= */}
      <Card>
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('dag')}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-violet-500/20 rounded-lg flex items-center justify-center">
              <Activity className="w-4 h-4 text-violet-400" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Task Dependencies</h3>
          </div>
          {expandedSections.has('dag')
            ? <ChevronDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
            : <ChevronRight className="w-4 h-4 text-[var(--color-text-secondary)]" />}
        </div>

        {expandedSections.has('dag') && (
          <div className="mt-4 overflow-hidden">
            <DAGVisualization tasks={tasks} height="500px" />
          </div>
        )}
      </Card>

      {/* ================================================================= */}
      {/* Event Log                                                          */}
      {/* ================================================================= */}
      <Card>
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('log')}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center">
              <ScrollText className="w-4 h-4 text-[var(--color-text-secondary)]" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Event Log</h3>
            {eventLog.length > 0 && (
              <span className="px-2 py-1 bg-slate-100 text-[var(--color-text-secondary)] rounded text-xs">
                {eventLog.length} events
              </span>
            )}
          </div>
          {expandedSections.has('log')
            ? <ChevronDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
            : <ChevronRight className="w-4 h-4 text-[var(--color-text-secondary)]" />}
        </div>

        {expandedSections.has('log') && (
          <div className="mt-4 max-h-64 overflow-y-auto">
            {eventLog.length === 0 ? (
              <div className="text-center py-6 text-[var(--color-text-muted)]">
                <ScrollText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No events yet — waiting for task state changes</p>
              </div>
            ) : (
              <div className="space-y-1 font-mono text-xs">
                {eventLog.map((entry, i) => (
                  <div
                    key={i}
                    className={cn(
                      'flex gap-3 py-1.5 px-2 rounded',
                      entry.level === 'error' && 'bg-red-50',
                      entry.level === 'success' && 'bg-emerald-50',
                    )}
                  >
                    <span className="text-[var(--color-text-muted)] shrink-0">
                      {formatTimestamp(entry.ts)}
                    </span>
                    <span className={cn(
                      entry.level === 'error' && 'text-red-800',
                      entry.level === 'success' && 'text-emerald-800',
                      entry.level === 'info' && 'text-[var(--color-text)]',
                    )}>
                      {(() => {
                        const expandedMessage = getExpandedEventMessage(entry.message, taskMap)
                        const canExpand =
                          expandedMessage !== entry.message ||
                          expandedMessage.length > 180 ||
                          expandedMessage.includes('\n')
                        const isExpanded = expandedEventItems.has(i)
                        if (!canExpand) {
                          return <span className="whitespace-pre-wrap break-words">{expandedMessage}</span>
                        }
                        if (isExpanded) {
                          return (
                            <div>
                              <pre className="whitespace-pre-wrap break-words font-mono text-xs">{expandedMessage}</pre>
                              <button
                                type="button"
                                className="mt-1 text-xs underline opacity-80 hover:opacity-100"
                                onClick={() => setExpandedEventItems(prev => {
                                  const next = new Set(prev)
                                  next.delete(i)
                                  return next
                                })}
                              >
                                show less
                              </button>
                            </div>
                          )
                        }

                        const oneLine = expandedMessage.replace(/\s+/g, ' ').trim()
                        const preview = oneLine.length > 180 ? oneLine.slice(0, 180) : oneLine
                        return (
                          <span className="whitespace-pre-wrap break-words">
                            {preview}
                            <button
                              type="button"
                              className="underline opacity-90 hover:opacity-100 ml-1"
                              onClick={() => setExpandedEventItems(prev => {
                                const next = new Set(prev)
                                next.add(i)
                                return next
                              })}
                            >
                              ...
                            </button>
                          </span>
                        )
                      })()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ================================================================= */}
      {/* Robot Execution Modal                                              */}
      {/* ================================================================= */}
      {selectedRobotRow && (
        <RobotExecutionModal
          isOpen={!!selectedRobot}
          onClose={() => setSelectedRobot(null)}
          robotId={selectedRobotRow.robotId}
          robotType={selectedRobotRow.robotType}
          tasks={selectedRobotRow.tasks}
          allTasks={tasks}
          elapsedTimes={elapsedTimes}
          taskServerInfo={selectedRobotRow.taskServerInfo}
        />
      )}
    </div>
  )
}
