/**
 * @fileoverview Execution Monitor page — live plan run telemetry for the fleet dashboard.
 *
 * Route: `/plans/:planId/execute`
 *
 * In the agent fleet lifecycle a **Plan** is a DAG of **Tasks** produced by a
 * planner method and assigned to concrete **Agents** by an allocator method.
 * This page is Mission Control's run-time view of that DAG while (or after)
 * the fleet server executes it:
 *
 * - Preview mode: plan is allocated but not yet started; operator reviews the
 *   task queue and clicks Start Execution.
 * - Live mode: a dedicated `GatewayRealtimeClient` WebSocket streams
 *   `tasks_update` messages; status diffs become Event Log entries and drive
 *   per-task elapsed timers (telemetry).
 * - Historical mode: for completed/failed plans, structured metrics and
 *   persisted `server_logs` seed the Event Log so operators can reconstruct
 *   what happened without a live socket.
 *
 * Key fleet concepts surfaced here:
 * - **Agents / Agent Fleet table** — who is working which task right now
 * - **Task Queue** — pending work ordered by dependency readiness
 * - **DAG Visualization** — task dependency graph for the plan
 * - **Event Log** — chronological execution lifecycle telemetry
 *
 * Behavior and JSX structure must stay intact; this file is heavily commented
 * for onboarding operators and dashboard contributors.
 */
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
import { AgentExecutionModal } from '../components/execution/AgentExecutionModal'
import { plansApi, tasksApi, agentsApi, methodsApi, metricsApi, useRealtimeUpdates } from '../lib/api'
import { cn, getPlanningStrategyName, getAllocationStrategyName, setMethodData } from '../lib/utils'
import { GatewayRealtimeClient } from '@agent-fleet/client-sdk'
import type { Task } from '../types'

// ---------------------------------------------------------------------------
// Event log types
// ---------------------------------------------------------------------------

/**
 * One Event Log row: timestamp, human message, and severity from execution telemetry.
 */
interface LogEntry {
  /** Epoch ms when the event occurred (or reconstructed ordering time). */
  ts: number
  /** Human-readable lifecycle line (plan/task started/completed/failed). */
  message: string
  /** Severity derived from message keywords: info | success | error. */
  level: 'info' | 'success' | 'error'
}

/**
 * Subset of metricsApi fields used to reconstruct plan/task execution events.
 */
interface MetricRow {
  /** ISO timestamp from the metrics service. */
  timestamp?: string
  /** Metric kind — typically plan_execution or task_execution. */
  event_type?: string
  /** Plan id or task id string the metric refers to. */
  entity_id?: string
  /** Measured duration for the execution event, if present. */
  duration_ms?: number
  /** Whether the plan/task execution succeeded. */
  success?: boolean
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Format milliseconds as short elapsed telemetry for execution timers.
 *
 * @param ms - Elapsed milliseconds since a task or plan started.
 * @returns Compact string such as `45s` or `2m 05s`.
 */
function formatElapsed(ms: number): string {
  // Local state/binding `secs` for this fleet UI flow.
  const secs = Math.floor(ms / 1000)
  // Conditional branch controlling fleet UI flow or data filtering.
  if (secs < 60) return `${secs}s`
  // Local state/binding `mins` for this fleet UI flow.
  const mins = Math.floor(secs / 60)
  // Local state/binding `remainder` for this fleet UI flow.
  const remainder = secs % 60
  // Return a computed value or early-exit for this fleet helper.
  return `${mins}m ${remainder}s`
}

/**
 * Format an epoch-ms timestamp as local wall-clock time for Event Log rows.
 *
 * @param ts - Unix epoch milliseconds.
 * @returns Locale time string (HH:MM:SS).
 */
function formatTimestamp(ts: number): string {
  // Return a computed value or early-exit for this fleet helper.
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

/**
 * Parse fleet-server `server_logs` into `LogEntry[]` for historical execution review.
 *
 * Only concrete plan/task lifecycle lines are kept (started/completed/failed).
 * Lines are filtered to the current `planId` / its task ids, then capped.
 *
 * @param serverLogs - Raw multiline log blob persisted on the plan.
 * @param planId - Plan whose execution we are reconstructing.
 * @param planTaskIds - Set of task ids belonging to this plan.
 * @returns Newest-first LogEntry array for the Event Log panel.
 */
function parsePersistedEventLog(serverLogs: string | undefined, planId: number, planTaskIds: Set<number>): LogEntry[] {
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!serverLogs || serverLogs.trim().length === 0) return []

  // Local state/binding `base` for this fleet UI flow.
  const base = Date.now()
  // Local state/binding `rawLines` for this fleet UI flow.
  const rawLines = serverLogs
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)

  // Merge continuation lines back into their parent event.
  /**
   * Component/helper `startsNewEvent` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const startsNewEvent = (line: string): boolean => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (/^(Plan|Task)\b/.test(line)) return true
    // Conditional branch controlling fleet UI flow or data filtering.
    if (/^\d{4}-\d{2}-\d{2}/.test(line)) return true
    // Return a computed value or early-exit for this fleet helper.
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

  /**
   * Component/helper `isExecutionLifecycleLine` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
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

/**
 * Build Event Log entries from structured `metricsApi` rows (preferred historical source).
 *
 * Maps `plan_execution` / `task_execution` metric events into operator-readable messages.
 *
 * @param metrics - Metric rows from the fleet metrics service.
 * @param tasks - Tasks for this plan (for agent id / result enrichment).
 * @param planId - Plan id to filter plan_execution metrics.
 * @returns Newest-first LogEntry array (max 200).
 */
function buildEventLogFromMetrics(metrics: MetricRow[], tasks: Task[], planId: number): LogEntry[] {
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!metrics || metrics.length === 0) return []
  // Local state/binding `taskById` for this fleet UI flow.
  const taskById = new Map(tasks.map(t => [String(t.task_id), t]))
  // Local state/binding `rows` for this fleet UI flow.
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
        message: `Task #${taskId}${task?.agent_id ? ` (${task.agent_id})` : ''} ${m.success === false ? 'failed' : 'completed'}${secs ? ` in ${secs}s` : ''}${task?.result ? `: ${task.result}` : ''}`,
      }
    })
    .sort((a, b) => b.ts - a.ts)

  // Return a computed value or early-exit for this fleet helper.
  return rows.slice(0, 200)
}

/**
 * Expand truncated Event Log ellipses using the authoritative `task.result` payload.
 *
 * @param message - Possibly truncated event message.
 * @param taskMap - Map of task_id → Task for result lookup.
 * @returns Full message when a matching completed/failed task result exists.
 */
function getExpandedEventMessage(message: string, taskMap: Map<number, Task>): string {
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!message.includes('…')) return message
  // Local state/binding `m` for this fleet UI flow.
  const m = message.match(/Task #(\d+)\s+(completed|failed)\s+on\s+([^:\n]+):[\s\S]*/i)
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!m) return message

  // Local state/binding `taskId` for this fleet UI flow.
  const taskId = Number(m[1])
  // Local state/binding `status` for this fleet UI flow.
  const status = m[2].toLowerCase()
  // Local state/binding `agent` for this fleet UI flow.
  const agent = m[3]
  // O(1) lookup of tasks by id for dependency readiness and Event Log expansion.
  const task = taskMap.get(taskId)
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!task?.result) return message

  // Conditional branch controlling fleet UI flow or data filtering.
  if (status === 'completed') {
    // Return a computed value or early-exit for this fleet helper.
    return `Task #${taskId} completed on ${agent}: ${task.result}`
  }
  // Return a computed value or early-exit for this fleet helper.
  return `Task #${taskId} failed on ${agent}: ${task.result}`
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * Main Execution Monitor page — live and historical telemetry for one plan run.
 *
 * Reads `:planId` from the route, fetches plan/tasks/agents/methods/metrics,
 * opens a plan-execution WebSocket when not in preview, diffs task status
 * changes into the Event Log, and renders fleet/queue/DAG/log panels.
 */
export function Execution() {
  // Subscribe to fleet realtime invalidations so plan/agent/task caches stay fresh.
  useRealtimeUpdates()
  // Read route params (typically `planId`) identifying which fleet plan this page owns.
  const { planId } = useParams<{ planId: string }>()
  // React Router navigate helper for Plans ↔ PlanDetails ↔ Execution transitions.
  const navigate = useNavigate()
  // TanStack Query client used to invalidate fleet entity caches after mutations.
  const queryClient = useQueryClient()

  // Tracks whether execution was started during this session (so WS connects immediately)
  const [executionStarted, setExecutionStarted] = useState(false)

  // Mutation wrapping a fleet API write (create / allocate / start / delete / copy).
  const startMutation = useMutation({
    mutationFn: () => plansApi.start(Number(planId)),
    onSuccess: () => {
      setExecutionStarted(true)
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      queryClient.invalidateQueries({ queryKey: ['plans'] })
    },
  })

  // Mutation wrapping a fleet API write (create / allocate / start / delete / copy).
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
  // Agent id opened in AgentExecutionModal for drill-down telemetry.
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  // Update the chronological execution Event Log (operator-facing telemetry feed).
  const [eventLog, setEventLog] = useState<LogEntry[]>([])
  // Local state/binding `[expandedEventItems, setExpandedEventItems]` for this fleet UI flow.
  const [expandedEventItems, setExpandedEventItems] = useState<Set<number>>(new Set())

  // Elapsed time tracking: taskId -> startTime (Date.now())
  const taskStartTimes = useRef<Map<number, number>>(new Map())
  // Renderable map of taskId → elapsed ms updated by the 1s timer.
  const [elapsedTimes, setElapsedTimes] = useState<Map<number, number>>(new Map())

  // Wall-clock timer for the whole execution
  const executionStartRef = useRef<number | null>(null)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [wallElapsed, setWallElapsed] = useState(0)

  // WebSocket tasks state (from dedicated execution WS)
  const [wsTasks, setWsTasks] = useState<Task[] | null>(null)
  // Previous task snapshot used to diff status transitions into Event Log rows.
  const prevTasksRef = useRef<Map<number, Task>>(new Map())

  // ---------------------------------------------------------------------------
  // Data fetching (initial load + fallback)
  // ---------------------------------------------------------------------------

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: plan } = useQuery({
    queryKey: ['plan', planId],
    queryFn: () => plansApi.get(Number(planId)),
    enabled: !!planId,
    refetchInterval: (query) => {
      const p = query.state.data
      return p?.execution_status === 'executing' ? 3000 : false
    },
  })
  // Plan execution lifecycle field: not_executed → executing → completed/failed.
  const planExecutionStatus = plan?.execution_status ?? 'not_executed'

  // True when the plan has not started — operator reviews queue before Start Execution.
  const isPreview = !executionStarted &&
    // Plan execution lifecycle field: not_executed → executing → completed/failed.
    plan?.execution_status !== 'executing' &&
    // Plan execution lifecycle field: not_executed → executing → completed/failed.
    plan?.execution_status !== 'completed' &&
    // Plan execution lifecycle field: not_executed → executing → completed/failed.
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

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: fetchedTasks = [] } = useQuery({
    queryKey: ['tasks', planId],
    queryFn: () => tasksApi.list({ plan_id: Number(planId) }),
    enabled: !!planId,
  })

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
  })

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: planners = [] } = useQuery({
    queryKey: ['planners'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'planner')),
  })

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: allocators = [] } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: historicalMetrics } = useQuery({
    queryKey: ['metrics', 'execution', planId],
    queryFn: () => metricsApi.list({ service: 'fleet_server', limit: 1000 }),
    enabled: !!planId,
  })

  // Effect: sync URL, seed logs/timers, open WebSockets, or react to status changes.
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

  // Effect: sync URL, seed logs/timers, open WebSockets, or react to status changes.
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
            message: `Task #${task.task_id} started on ${task.agent_id ?? '?'}`,
            level: 'info',
          })
        } else if (task.status === 'completed') {
          taskStartTimes.current.delete(task.task_id)
          newEntries.push({
            ts: now,
            message: `Task #${task.task_id} completed on ${task.agent_id ?? '?'}${task.result ? `: ${task.result}` : ''}`,
            level: 'success',
          })
        } else if (task.status === 'failed') {
          taskStartTimes.current.delete(task.task_id)
          newEntries.push({
            ts: now,
            message: `Task #${task.task_id} failed on ${task.agent_id ?? '?'}${task.result ? `: ${task.result}` : ''}`,
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

  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const taskGroups = useMemo(() => ({
    executing: tasks.filter(t => t.status === 'in_progress'),
    pending: tasks.filter(t => t.status === 'pending'),
    completed: tasks.filter(t => t.status === 'completed'),
    failed: tasks.filter(t => t.status === 'failed' && !isCancelled(t)),
    cancelled: tasks.filter(t => isCancelled(t)),
  }), [tasks, isCancelled])

  const totalTasks = tasks.length
  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const completedCount = taskGroups.completed.length
  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const executingCount = taskGroups.executing.length
  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const pendingCount = taskGroups.pending.length
  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const failedCount = taskGroups.failed.length
  // Tasks partitioned by lifecycle: executing/pending/completed/failed/cancelled.
  const cancelledCount = taskGroups.cancelled.length

  // Aggregate plan status for StatusBadge (pending/in_progress/completed/failed).
  const overallStatus = useMemo(() => {
    if ((failedCount > 0 || cancelledCount > 0) && executingCount === 0 && pendingCount === 0) return 'failed'
    if (completedCount === totalTasks && totalTasks > 0) return 'completed'
    if (executingCount > 0) return 'in_progress'
    return 'pending'
  }, [totalTasks, completedCount, executingCount, pendingCount, failedCount, cancelledCount])

  // Group tasks by agent for the fleet table
  const robotRows = useMemo(() => {
    const byAgent = new Map<string, Task[]>()
    for (const task of tasks) {
      const rid = task.agent_id ?? '__unassigned__'
      if (!byAgent.has(rid)) byAgent.set(rid, [])
      byAgent.get(rid)!.push(task)
    }

    return Array.from(byAgent.entries())
      .filter(([rid]) => rid !== '__unassigned__')
      .map(([rid, rTasks]) => {
        const agent = agents.find(r => r.agent_id === rid)
        const current = rTasks.find(t => t.status === 'in_progress')
        const succeeded = rTasks.filter(t => t.status === 'completed').length
        const failed = rTasks.filter(t => t.status === 'failed' && !isCancelled(t)).length
        const cancelled = rTasks.filter(t => isCancelled(t)).length
        const total = rTasks.length
        const finished = succeeded + failed + cancelled === total
        const hasFailed = failed > 0 || cancelled > 0

        return {
          agentId: rid,
          agentType: agent?.agent_type ?? rTasks[0]?.agent_type ?? 'unknown',
          taskServerInfo: agent?.task_server_info ?? null,
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
  }, [tasks, agents])

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

  // DAG dependency edges controlling when a pending task becomes dispatchable.
  const depsReady = useCallback((task: Task) =>
    task.dependency_task_ids.every(d => taskMap.get(d)?.status === 'completed'),
    [taskMap]
  )

  // ---------------------------------------------------------------------------
  // Selected agent data for modal
  // ---------------------------------------------------------------------------

  // Agent id opened in AgentExecutionModal for drill-down telemetry.
  const selectedAgentRow = selectedAgent
    ? robotRows.find(r => r.agentId === selectedAgent)
    : null

  // ---------------------------------------------------------------------------
  // Progress bar segment widths
  // ---------------------------------------------------------------------------

  // Progress-bar segment widths as percentages of total tasks.
  const pctCompleted = totalTasks > 0 ? (completedCount / totalTasks) * 100 : 0
  // Progress-bar segment widths as percentages of total tasks.
  const pctExecuting = totalTasks > 0 ? (executingCount / totalTasks) * 100 : 0
  // Progress-bar segment widths as percentages of total tasks.
  const pctFailed = totalTasks > 0 ? (failedCount / totalTasks) * 100 : 0
  // Progress-bar segment widths as percentages of total tasks.
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
      {/* Agent Fleet Table                                                  */}
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
            {/* Agent Fleet section heading — agents currently assigned on this plan. */}
            <h3 className="text-lg font-semibold text-[var(--color-text)]">Agent Fleet</h3>
            <span className="px-2 py-1 tonal-sky rounded text-xs">
              {robotRows.length} agents
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
                <p>No agents assigned to tasks yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wider border-b border-slate-200">
                      <th className="pb-3 pr-4">Agent</th>
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
                        key={row.agentId}
                        className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedAgent(row.agentId)}
                      >
                        {/* Agent */}
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <Bot className="w-4 h-4 text-slate-700 flex-shrink-0" />
                            <span className="font-mono text-slate-900">{row.agentId}</span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 border border-slate-200 text-[var(--color-text-muted)]">
                              {row.agentType}
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
            {/* Task Queue section — pending tasks waiting on DAG dependencies. */}
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
                      <th className="pb-3 pr-4">Assigned Agent</th>
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
                            {task.agent_id ? (
                              <span className="font-mono text-xs text-slate-800">{task.agent_id}</span>
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
                      <th className="pb-3 pr-4">Agent</th>
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
                          {task.agent_id ? (
                            <span
                              className={cn(
                                'font-mono text-xs font-medium',
                                task.status === 'failed' ? 'text-red-950' : 'text-slate-900'
                              )}
                            >
                              {task.agent_id}
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
            {/* Event Log — chronological execution telemetry for operators. */}
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
      {/* Agent Execution Modal                                              */}
      {/* ================================================================= */}
      {selectedAgentRow && (
        <AgentExecutionModal
          isOpen={!!selectedAgent}
          onClose={() => setSelectedAgent(null)}
          agentId={selectedAgentRow.agentId}
          agentType={selectedAgentRow.agentType}
          tasks={selectedAgentRow.tasks}
          allTasks={tasks}
          elapsedTimes={elapsedTimes}
          taskServerInfo={selectedAgentRow.taskServerInfo}
        />
      )}
    </div>
  )
}
