/**
 * @fileoverview Plan Details page — deep inspection and editing of a single fleet plan.
 *
 * Route: `/plans/:planId`
 *
 * After a **Plan** is created on the Plans list, this page is the operator's
 * workspace for that plan's artifacts: goal bindings, planning/allocation
 * strategies, the task DAG, per-task edit/delete (pre-execution), allocation
 * workflows, Graphviz exports, and navigation into the Execution Monitor.
 *
 * Tabs and regions typically cover:
 * - Overview / metadata for the plan and its goals
 * - Tasks list (VerticalTaskList) with status chips and agent assignments
 * - DAG visualization of task dependencies
 * - Allocation UI (AllocatePlanForm / MethodSelectionCard) when unallocated
 * - Method detail deep-links into planner/allocator YAML
 *
 * Task statuses normalize to fleet conventions (`pending`, `in_progress`,
 * `completed`, `failed`, etc.). Editing is gated until execution starts so
 * live runs are not mutated underfoot.
 *
 * Behavior and JSX structure must stay intact; this file is heavily commented
 * for onboarding operators and dashboard contributors.
 */
import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  ArrowLeft, Wand2, GitBranch, Link, Bot, Target, Activity, Play, Edit, Check, CheckCircle, X, XCircle, Zap, Download, Loader2, Users, Plus, Trash2
} from 'lucide-react'
// Graphviz is imported dynamically below

import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/common/Button'
import { Modal } from '../components/common/Modal'
import { EmptyState } from '../components/common/EmptyState'
import { DAGVisualization } from '../components/common/DAGVisualization'
import { MethodDetailModal } from './Planners'
import type { Agent } from '../types'

// Import AllocatePlanForm from Plans page
// Note: This creates a circular import issue, so we'll inline the allocation logic instead
import { plansApi, agentsApi, goalsApi, methodsApi, tasksApi, useRealtimeUpdates, type MethodSummary } from '../lib/api'
import { cn, capitalize, getPlanningStrategyName, getAllocationStrategyName, getPlanningMethodId, getAllocationMethodId, setMethodData, getStatusBgColor } from '../lib/utils'
import JSZip from 'jszip'

// =============================================================================
// Task List Component
// =============================================================================

/**
 * Normalize free-form task status strings into canonical fleet snake_case.
 *
 * @param status - Raw status from API or artifacts.
 * @returns Lowercase underscored status or `unknown`.
 */
function normalizeTaskStatus(status: string | undefined): string {
  // Conditional branch controlling fleet UI flow or data filtering.
  if (!status) return 'unknown'
  // Return a computed value or early-exit for this fleet helper.
  return status.trim().toLowerCase().replace(/[\s-]+/g, '_')
}

/**
 * Vertical list of plan tasks with status, agent assignment, and edit/delete.
 *
 * Edit/delete are disabled once the plan has started executing (`canEdit`).
 *
 * @param props.tasks - Tasks belonging to the plan.
 * @param props.onEdit - Open edit flow for a task.
 * @param props.onDelete - Delete a task by id.
 * @param props.canEdit - Whether mutations are allowed (pre-execution).
 */
function VerticalTaskList({
  tasks,
  onEdit,
  onDelete,
  canEdit,
}: {
  tasks: any[]
  onEdit: (task: any) => void
  onDelete: (taskId: number) => void
  canEdit: boolean
}) {
  // Return the React element tree for this fleet UI component.
  return (
    <div className="space-y-4">
      {tasks.map((task, index) => (
        <Card key={task.task_id || index} className="p-6 hover:bg-slate-50 transition-colors">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <span className="text-xl font-bold text-[var(--color-text)]">Task {task.task_id}</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 bg-sky-100 border border-sky-300 text-blue-800 text-sm font-semibold rounded-lg">
                      {task.agent_type}
                    </span>
                    {task.agent_id && (
                      <span className="px-3 py-1 bg-emerald-100 border border-emerald-300 text-emerald-800 text-sm font-semibold rounded-lg">
                        {task.agent_id}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-[var(--color-text)] text-base leading-relaxed">{task.description}</div>
              </div>
              <div className="flex flex-col items-end space-y-2">
                {task.status && (
                  <span
                    className={cn(
                      'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold',
                      getStatusBgColor(normalizeTaskStatus(task.status))
                    )}
                  >
                    {capitalize(normalizeTaskStatus(task.status))}
                  </span>
                )}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(task)}
                    disabled={!task.task_id || !canEdit}
                    title={!canEdit ? 'Tasks can only be edited before the plan is executed.' : undefined}
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onDelete(task.task_id)}
                    disabled={!task.task_id || !canEdit}
                    title={!canEdit ? 'Tasks can only be deleted before the plan is executed.' : undefined}
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </Button>
                </div>
              </div>
            </div>

            {task.dependency_task_ids && task.dependency_task_ids.length > 0 && (
              <div className="bg-slate-50/40 p-3 rounded-lg border border-slate-200">
                <div className="flex items-center space-x-2 mb-2">
                  <Link className="w-4 h-4 text-[var(--color-text-secondary)]" />
                  <span className="text-sm font-medium text-[var(--color-text)]">Dependencies</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {task.dependency_task_ids.map((depId: number) => (
                    <span key={depId} className="px-3 py-1 bg-orange-100 border border-orange-300 text-orange-950 text-sm font-semibold rounded-lg">
                      Task {depId}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}


// =============================================================================
// Main Component
// =============================================================================

/**
 * Main Plan Details page — inspect/edit one plan's tasks, DAG, and allocation.
 *
 * Default export routed at `/plans/:planId`. Handles tabs, Graphviz export,
 * allocation modal, method deep-links, and navigation to Execution.
 */
export default function PlanDetails() {
  // Developer diagnostic log (not operator-facing telemetry).
  console.log('PlanDetails: Component rendering')

  // Read route params (typically `planId`) identifying which fleet plan this page owns.
  const { planId } = useParams<{ planId: string }>()
  // React Router navigate helper for Plans ↔ PlanDetails ↔ Execution transitions.
  const navigate = useNavigate()
  // URL search params for deep-linking method modals, tabs, and filters.
  const [searchParams] = useSearchParams()
  // Which planner/allocator method modal is open (YAML introspection).
  const [selectedMethod, setSelectedMethod] = useState<{ id: number; type: 'planner' | 'allocator' | null } | null>(null)
  // Plan currently open in the allocate modal (null when closed).
  const [allocatePlanId, setAllocatePlanId] = useState<number | null>(null)
  // Active Plan Details tab: overview, tasks, prompts, artifacts, or goals.
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'prompts' | 'artifacts' | 'goals'>('overview')
  // Tasks tab layout: vertical list vs interactive DAG visualization.
  const [taskView, setTaskView] = useState<'vertical' | 'dag'>('vertical')
  // Prompts tab: show planning-strategy prompts vs allocation-strategy prompts.
  const [promptsView, setPromptsView] = useState<'planning' | 'allocation'>('planning')
  // Artifacts tab: show planning artifacts vs allocation artifacts from the fleet server.
  const [artifactsView, setArtifactsView] = useState<'planning' | 'allocation'>('planning')
  // Whether the plan name/description inline editor is open.
  const [isEditing, setIsEditing] = useState(false)
  // Draft plan name while editing plan metadata.
  const [editName, setEditName] = useState('')
  // Draft plan description while editing plan metadata.
  const [editDescription, setEditDescription] = useState('')
  // Brief UI flash flag after a successful metadata save.
  const [justUpdated, setJustUpdated] = useState(false)

  // Task create/edit modal visibility (pre-execution only).
  const [isTaskEditorOpen, setIsTaskEditorOpen] = useState(false)
  // Whether the task editor is creating a new DAG node or editing an existing task.
  const [taskEditorMode, setTaskEditorMode] = useState<'create' | 'edit'>('create')
  // Task id being edited (null when creating).
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null)
  // Task description field in the create/edit form.
  const [taskFormDescription, setTaskFormDescription] = useState('')
  // Optional goal id linkage for the task being created/edited.
  const [taskFormGoalId, setTaskFormGoalId] = useState<number | ''>('')
  // Local state/binding `[taskFormAgentId, setTaskFormAgentId]` for this fleet UI flow.
  const [taskFormAgentId, setTaskFormAgentId] = useState<string>('') // "" = unassigned
  // Local state/binding `[taskFormDependencyIds, setTaskFormDependencyIds]` for this fleet UI flow.
  const [taskFormDependencyIds, setTaskFormDependencyIds] = useState<number[]>([])
  // Local state/binding `[deleteTaskId, setDeleteTaskId]` for this fleet UI flow.
  const [deleteTaskId, setDeleteTaskId] = useState<number | null>(null)

  // Enable real-time updates
  const { isConnected } = useRealtimeUpdates()


  // Handle URL query parameters for method modal
  useEffect(() => {
    const method = searchParams.get('method')
    const methodType = searchParams.get('method_type') as 'planner' | 'allocator' | null
    if (method) {
      const methodId = parseInt(method, 10)
      if (!isNaN(methodId)) {
        setSelectedMethod({ id: methodId, type: methodType })
      }
    } else {
      setSelectedMethod(null)
    }
  }, [searchParams])
  // TanStack Query client used to invalidate fleet entity caches after mutations.
  const queryClient = useQueryClient()

  // Developer diagnostic log (not operator-facing telemetry).
  console.log('PlanDetails: planId =', planId)

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: plan, isLoading, error, isFetching } = useQuery({
    queryKey: ['plan', planId],
    queryFn: () => plansApi.get(parseInt(planId!)),
    enabled: !!planId,
  })

  /**
   * Component/helper `planExecutionStatus` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  // Plan execution lifecycle field: not_executed → executing → completed/failed.
  const planExecutionStatus = (plan?.execution_status ?? 'not_executed') as string
  /** Add/edit/delete tasks only before any execution has started (plan still `not_executed`). */
  const canEditPlanTasks = Boolean(plan) && planExecutionStatus === 'not_executed'

  // Fetch allocation status separately
  const { data: allocationStatus } = useQuery({
    queryKey: ['plan-status', planId],
    queryFn: () => plansApi.getStatus(parseInt(planId!)),
    enabled: !!planId,
    // No refetchInterval - using WebSocket real-time updates
  })

  // Fetch agent statuses for execution readiness check
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
    // No refetchInterval - using WebSocket real-time updates
  })

  // Load method data for strategy name lookups
  const { data: planners = [] } = useQuery({
    queryKey: ['planners'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'planner')),
  })

  const { data: allocators = [] } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  // Update method data for name lookups
  useEffect(() => {
    setMethodData(planners, allocators)
  }, [planners, allocators])

  // Fetch agent health statuses for accurate connectivity checks
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
    // No refetchInterval - using WebSocket real-time updates
  })

  // High-level objectives that planners decompose into task DAGs.
  const { data: goals = [] } = useQuery({
    queryKey: ['goals'],
    queryFn: goalsApi.list,
  })

  /**
   * Component/helper `openCreateTask` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const openCreateTask = () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!canEditPlanTasks) return
    /**
     * Component/helper `defaultGoal` used by this fleet dashboard page.
     *
     * @remarks Part of Mission Control for the agent fleet.
     */
    // Local state/binding `defaultGoal` for this fleet UI flow.
    const defaultGoal = (plan as any)?.goal_ids?.[0]
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskEditorMode('create')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setEditingTaskId(null)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormDescription('')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormGoalId(typeof defaultGoal === 'number' ? defaultGoal : '')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormAgentId('')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormDependencyIds([])
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsTaskEditorOpen(true)
  }

  /**
   * Component/helper `openEditTask` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const openEditTask = (task: any) => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!canEditPlanTasks) return
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskEditorMode('edit')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setEditingTaskId(task.task_id)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormDescription(task.description || '')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormGoalId(typeof task.goal_id === 'number' ? task.goal_id : '')
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setTaskFormAgentId(task.agent_id || '')
    // DAG dependency edges controlling when a pending task becomes dispatchable.
    setTaskFormDependencyIds(Array.isArray(task.dependency_task_ids) ? task.dependency_task_ids : [])
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsTaskEditorOpen(true)
  }

  /**
   * Component/helper `requestDeleteTask` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const requestDeleteTask = (taskId: number) => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!canEditPlanTasks) return
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setDeleteTaskId(taskId)
  }

  /**
   * Component/helper `submitTaskEditor` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const submitTaskEditor = (e: React.FormEvent) => {
    e.preventDefault()
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!canEditPlanTasks) return
    // Plan identity from the route — scopes all tasks/metrics/WebSocket traffic.
    if (!planId) return
    // Plan identity from the route — scopes all tasks/metrics/WebSocket traffic.
    const parsedPlanId = parseInt(planId, 10)
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!parsedPlanId) return
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!taskFormDescription.trim()) return
    // Conditional branch controlling fleet UI flow or data filtering.
    if (taskFormGoalId === '') return

    // Local state/binding `agentIdValue` for this fleet UI flow.
    const agentIdValue = taskFormAgentId // "" clears/unassigns; non-empty sets
    // Conditional branch controlling fleet UI flow or data filtering.
    if (taskEditorMode === 'create') {
      createTaskMutation.mutate({
        description: taskFormDescription.trim(),
        goal_id: taskFormGoalId,
        plan_id: parsedPlanId,
        agent_id: agentIdValue ? agentIdValue : null,
        dependency_task_ids: taskFormDependencyIds,
      })
    } else if (editingTaskId != null) {
      updateTaskMutation.mutate({
        taskId: editingTaskId,
        data: {
          description: taskFormDescription.trim(),
          goal_id: taskFormGoalId,
          agent_id: agentIdValue,
          dependency_task_ids: taskFormDependencyIds,
        },
      })
    }
  }

  // Check if plan is executable (has allocated tasks and agents are available)
  const isPlanExecutable = plan && allocationStatus && robotHealth && agents ? (() => {
    if (allocationStatus.status !== 'fully_allocated') return false

    // Get all agents assigned to tasks in this plan
    const planTasks = plan.tasks || []
    const assignedTasks = planTasks.filter(t => t.agent_id)
    const assignedAgentIds = [
      ...new Set(
        assignedTasks
          .map((t: any) => t.agent_id)
          .filter((id: unknown): id is string => typeof id === 'string' && id.length > 0)
      ),
    ]

    // Check if all assigned agents are reachable
    return assignedAgentIds.every(agentId => {
      const agent = agents.find(r => r.agent_id === agentId)
      const health = robotHealth[agentId]
      return agent && health?.reachable === true
    })
  })() : false

  const updateMutation = useMutation({
    mutationFn: ({ planId, name, description }: { planId: number; name: string; description: string }) =>
      plansApi.update(planId, { name, description }),
    onSuccess: (updatedPlan) => {
      console.log('Update successful, received:', updatedPlan)
      // Update the query cache with the new plan info
      queryClient.setQueryData(['plans', planId], updatedPlan)
      queryClient.setQueryData(['plan', planId], updatedPlan)
      console.log('Cache updated, invalidating queries...')
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      // Force a refetch to ensure the data is fresh
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })

      // Mark that we just updated
      setJustUpdated(true)
    },
    onError: (error) => {
      console.error('Failed to update plan:', error)
      setIsEditing(false)
      setJustUpdated(false)
    },
  })

  // Allocation mutation
  const allocateMutation = useMutation({
    mutationFn: ({ planId, allocationStrategy }: { planId: number; allocationStrategy: string }) =>
      plansApi.allocate(planId, allocationStrategy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      setAllocatePlanId(null)
    },
  })

  const createTaskMutation = useMutation({
    mutationFn: (payload: { description: string; goal_id: number; plan_id: number; agent_id?: string | null; dependency_task_ids: number[] }) =>
      tasksApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      queryClient.invalidateQueries({ queryKey: ['plan-status', planId] })
      setIsTaskEditorOpen(false)
      setEditingTaskId(null)
    },
  })

  const updateTaskMutation = useMutation({
    mutationFn: (payload: { taskId: number; data: { description?: string; goal_id?: number; agent_id?: string; dependency_task_ids: number[] } }) =>
      tasksApi.update(payload.taskId, {
        ...payload.data,
        update_dependency_task_ids: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      queryClient.invalidateQueries({ queryKey: ['plan-status', planId] })
      setIsTaskEditorOpen(false)
      setEditingTaskId(null)
    },
  })

  const deleteTaskMutation = useMutation({
    mutationFn: (taskIdToDelete: number) => tasksApi.delete(taskIdToDelete),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['plan', planId] })
      queryClient.invalidateQueries({ queryKey: ['plan-status', planId] })
      setDeleteTaskId(null)
    },
  })

  useEffect(() => {
    if (!canEditPlanTasks) {
      setIsTaskEditorOpen(false)
      setDeleteTaskId(null)
    }
  }, [canEditPlanTasks])

  // Exit edit mode only after the query has finished refetching with the new data
  useEffect(() => {
    if (justUpdated && !isFetching) {
      console.log('Query finished refetching, exiting edit mode')
      setIsEditing(false)
      setJustUpdated(false)
    }
  }, [justUpdated, isFetching])

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Bot },
    { id: 'tasks', label: 'Tasks', icon: GitBranch },
    { id: 'goals', label: 'Goals', icon: Target },
    { id: 'prompts', label: 'Prompts', icon: Wand2 },
    { id: 'artifacts', label: 'Artifacts', icon: Link },
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--color-bg)] p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-[var(--color-text-secondary)]">Loading plan details...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--color-bg)] p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-red-800">Error loading plan: {error.message}</div>
          </div>
        </div>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-[var(--color-bg)] p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-[var(--color-text-secondary)]">Plan not found</div>
          </div>
        </div>
      </div>
    )
  }

  // Download handlers (defined here for access to plan data and svgContent)
  /**
   * Component/helper `downloadFile` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadFile = (content: string, filename: string, mimeType: string = 'text/plain') => {
    // Local state/binding `blob` for this fleet UI flow.
    const blob = new Blob([content], { type: mimeType })
    // Local state/binding `url` for this fleet UI flow.
    const url = URL.createObjectURL(blob)
    // Local state/binding `a` for this fleet UI flow.
    const a = document.createElement('a')
    // Assign/update a value consumed by the surrounding fleet UI logic.
    a.href = url
    // Assign/update a value consumed by the surrounding fleet UI logic.
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  /**
   * Component/helper `downloadJSON` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadJSON = (data: any, filename: string) => {
    // Local state/binding `jsonString` for this fleet UI flow.
    const jsonString = JSON.stringify(data, null, 2)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    downloadFile(jsonString, filename, 'application/json')
  }

  /**
   * Component/helper `downloadSVG` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadSVG = (svgContent: string, filename: string) => {
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    downloadFile(svgContent, filename, 'image/svg+xml')
  }

  /**
   * Component/helper `downloadDAG` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadDAG = async () => {
    // Developer diagnostic log (not operator-facing telemetry).
    console.log('Download DAG called')

    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Dynamically import Graphviz and generate SVG on-demand
      const { Graphviz } = await import('@hpcc-js/wasm-graphviz')
      // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
      const graphviz = await Graphviz.load()

      // Generate the DOT source (same logic as in DAGVisualization)
      const tasks = plan.tasks || []
      /**
       * Component/helper `generateDot` used by this fleet dashboard page.
       *
       * @remarks Part of Mission Control for the agent fleet.
       */
      // Local state/binding `generateDot` for this fleet UI flow.
      const generateDot = (tasks: any[]) => {
        // Declare let dot used by this fleet UI logic.
        let dot = `digraph G {
  rankdir=LR;
  bgcolor="#ffffff";
  node [shape=plaintext, fontname="Arial"];
  edge [color="#334155",penwidth=5.0, arrowhead=vee, arrowsize=4.0, headclip=true, tailclip=true, fontname="Arial"];
  graph [splines=spline, nodesep=1.2, ranksep=1.4];
`

        // Add nodes with status-based styling
        tasks.forEach(task => {
          // Status-based colors for light background
          let statusColors = {
            border: '#1e293b',
            bg: '#ffffff',
            text: '#0f172a',
            headerBg: '#f1f5f9'
          }

          switch ((task.status || 'pending').toLowerCase()) {
            case 'completed':
              statusColors = { border: '#047857', bg: '#d1fae5', text: '#064e3b', headerBg: '#a7f3d0' }
              break
            case 'running':
            case 'executing':
              statusColors = { border: '#d97706', bg: '#fef3c7', text: '#92400e', headerBg: '#fde68a' }
              break
            case 'failed':
            case 'error':
              statusColors = { border: '#dc2626', bg: '#fee2e2', text: '#991b1b', headerBg: '#fecaca' }
              break
            case 'pending':
            default:
              statusColors = { border: '#64748b', bg: '#f8fafc', text: '#374151', headerBg: '#f3f4f6' }
              break
          }

          const htmlLabel = `<TABLE BORDER="3" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0" BGCOLOR="${statusColors.bg}" COLOR="${statusColors.border}">
  <TR>
    <TD ALIGN="CENTER" BGCOLOR="${statusColors.headerBg}" CELLPADDING="12">
      <FONT COLOR="#1d4ed8" FACE="Arial" SIZE="28"><B>Task ${task.task_id}</B></FONT>
    </TD>
  </TR>
  <TR>
    <TD ALIGN="CENTER" CELLPADDING="16">
      <FONT COLOR="${statusColors.text}" FACE="Arial" SIZE="20">${task.description}</FONT>
    </TD>
  </TR>
  <TR>
    <TD ALIGN="CENTER" CELLPADDING="12">
      <TABLE BORDER="0" CELLSPACING="10">
        <TR>
          <TD BGCOLOR="#7c3aed" CELLPADDING="10">
            <FONT COLOR="#ffffff" FACE="Arial" SIZE="16"><B>${task.agent_type || 'unknown'}</B></FONT>
          </TD>
          <TD BGCOLOR="#0d9488" CELLPADDING="10">
            <FONT COLOR="#ffffff" FACE="Arial" SIZE="16"><B>${task.agent_id || 'unassigned'}</B></FONT>
          </TD>
        </TR>
      </TABLE>
    </TD>
  </TR>
</TABLE>`

          dot += `  ${task.task_id} [label=<${htmlLabel}>];\n`
        })

        // Add edges with status-based colors
        tasks.forEach(task => {
          if (task.dependency_task_ids && task.dependency_task_ids.length > 0) {
            task.dependency_task_ids.forEach((depId: number) => {
              // Use a dark, visible edge color for better contrast on white background
              dot += `  ${depId} -> ${task.task_id} [color="#374151", penwidth="3"];\n`
            })
          }
        })

        dot += '}'
        // Return a computed value or early-exit for this fleet helper.
        return dot
      }

      const dotSource = generateDot(tasks)
      const svg = graphviz.dot(dotSource, 'svg')

      if (svg && svg.length > 100 && svg.includes('<svg')) {
        console.log('Generated fresh SVG for download, length:', svg.length)
        downloadSVG(svg, `plan-${planId}-dag.svg`)
      } else {
        console.error('Generated SVG is invalid')
        alert('Failed to generate DAG visualization for download.')
      }

    } catch (error) {
      console.error('Error generating SVG for download:', error)
      alert('Failed to generate DAG visualization. Please try again.')
    }
  }

  /**
   * Component/helper `downloadPlanningPrompts` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadPlanningPrompts = async () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (plan.planning_prompts && typeof plan.planning_prompts === 'object') {
      // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
      const zip = new JSZip()

      // Conditional branch controlling fleet UI flow or data filtering.
      if (plan.planning_prompts.system) {
        zip.file('system_prompt.txt', plan.planning_prompts.system)
      }
      // Conditional branch controlling fleet UI flow or data filtering.
      if (plan.planning_prompts.user) {
        zip.file('user_prompt.txt', plan.planning_prompts.user)
      }

      // Local state/binding `content` for this fleet UI flow.
      const content = await zip.generateAsync({ type: 'blob' })
      // Local state/binding `url` for this fleet UI flow.
      const url = URL.createObjectURL(content)
      // Local state/binding `a` for this fleet UI flow.
      const a = document.createElement('a')
      a.href = url
      a.download = `plan-${planId}-planning-prompts.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  /**
   * Component/helper `downloadAllocationPrompts` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadAllocationPrompts = async () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (plan.allocation_prompts && typeof plan.allocation_prompts === 'object') {
      // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
      const zip = new JSZip()

      // Conditional branch controlling fleet UI flow or data filtering.
      if (plan.allocation_prompts.system) {
        zip.file('system_prompt.txt', plan.allocation_prompts.system)
      }
      // Conditional branch controlling fleet UI flow or data filtering.
      if (plan.allocation_prompts.user) {
        zip.file('user_prompt.txt', plan.allocation_prompts.user)
      }

      // Local state/binding `content` for this fleet UI flow.
      const content = await zip.generateAsync({ type: 'blob' })
      // Local state/binding `url` for this fleet UI flow.
      const url = URL.createObjectURL(content)
      // Local state/binding `a` for this fleet UI flow.
      const a = document.createElement('a')
      a.href = url
      a.download = `plan-${planId}-allocation-prompts.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  /**
   * Component/helper `downloadPlanningArtifacts` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadPlanningArtifacts = () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (plan.planning_artifacts) {
      downloadJSON(plan.planning_artifacts, `plan-${planId}-planning-artifacts.json`)
    }
  }

  /**
   * Component/helper `downloadAllocationArtifacts` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadAllocationArtifacts = () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (plan.allocation_artifacts) {
      downloadJSON(plan.allocation_artifacts, `plan-${planId}-allocation-artifacts.json`)
    }
  }

  /**
   * Component/helper `downloadFullPlan` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const downloadFullPlan = async () => {
    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
      const zip = new JSZip()

      // Create directory structure
      const promptsFolder = zip.folder('prompts')
      // Local state/binding `planningPromptsFolder` for this fleet UI flow.
      const planningPromptsFolder = promptsFolder?.folder('planning')
      // Local state/binding `allocationPromptsFolder` for this fleet UI flow.
      const allocationPromptsFolder = promptsFolder?.folder('allocation')

      // Local state/binding `artifactsFolder` for this fleet UI flow.
      const artifactsFolder = zip.folder('artifacts')

      // Add planning prompts
      if (plan.planning_prompts && typeof plan.planning_prompts === 'object') {
        // Conditional branch controlling fleet UI flow or data filtering.
        if (plan.planning_prompts.system) {
          planningPromptsFolder?.file('system_prompt.txt', plan.planning_prompts.system)
        }
        // Conditional branch controlling fleet UI flow or data filtering.
        if (plan.planning_prompts.user) {
          planningPromptsFolder?.file('user_prompt.txt', plan.planning_prompts.user)
        }
      }

      // Add allocation prompts
      if (plan.allocation_prompts && typeof plan.allocation_prompts === 'object') {
        // Conditional branch controlling fleet UI flow or data filtering.
        if (plan.allocation_prompts.system) {
          allocationPromptsFolder?.file('system_prompt.txt', plan.allocation_prompts.system)
        }
        // Conditional branch controlling fleet UI flow or data filtering.
        if (plan.allocation_prompts.user) {
          allocationPromptsFolder?.file('user_prompt.txt', plan.allocation_prompts.user)
        }
      }

      // Add artifacts
      if (plan.planning_artifacts) {
        artifactsFolder?.file('planning_artifacts.json', JSON.stringify(plan.planning_artifacts, null, 2))
      }
      // Conditional branch controlling fleet UI flow or data filtering.
      if (plan.allocation_artifacts) {
        artifactsFolder?.file('allocation_artifacts.json', JSON.stringify(plan.allocation_artifacts, null, 2))
      }

      // Generate and add DAG SVG
      try {
        // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
        const { Graphviz } = await import('@hpcc-js/wasm-graphviz')
        // Export plan/task artifacts (zip or Graphviz DAG) for offline review.
        const graphviz = await Graphviz.load()

        // Local state/binding `tasks` for this fleet UI flow.
        const tasks = plan.tasks || []
        /**
         * Component/helper `generateDot` used by this fleet dashboard page.
         *
         * @remarks Part of Mission Control for the agent fleet.
         */
        // Local state/binding `generateDot` for this fleet UI flow.
        const generateDot = (tasks: any[]) => {
          // Declare let dot used by this fleet UI logic.
          let dot = `digraph G {
  rankdir=LR;
  bgcolor="#ffffff";
  node [shape=plaintext, fontname="Arial"];
  edge [color="#334155",penwidth=5.0, arrowhead=vee, arrowsize=4.0, headclip=true, tailclip=true, fontname="Arial"];
  graph [splines=spline, nodesep=1.2, ranksep=1.4];
`

          tasks.forEach(task => {
            let statusColors = {
              border: '#1e293b',
              bg: '#ffffff',
              text: '#0f172a',
              headerBg: '#f1f5f9'
            }

            switch ((task.status || 'pending').toLowerCase()) {
              case 'completed':
                statusColors = { border: '#047857', bg: '#d1fae5', text: '#064e3b', headerBg: '#a7f3d0' }
                break
              case 'running':
              case 'executing':
                statusColors = { border: '#d97706', bg: '#fef3c7', text: '#92400e', headerBg: '#fde68a' }
                break
              case 'failed':
              case 'error':
                statusColors = { border: '#dc2626', bg: '#fee2e2', text: '#991b1b', headerBg: '#fecaca' }
                break
              case 'pending':
              default:
                statusColors = { border: '#64748b', bg: '#f8fafc', text: '#374151', headerBg: '#f3f4f6' }
                break
            }

            const htmlLabel = `<TABLE BORDER="3" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0" BGCOLOR="${statusColors.bg}" COLOR="${statusColors.border}">
  <TR>
    <TD ALIGN="CENTER" BGCOLOR="${statusColors.headerBg}" CELLPADDING="12">
      <FONT COLOR="#1d4ed8" FACE="Arial" SIZE="28"><B>Task ${task.task_id}</B></FONT>
    </TD>
  </TR>
  <TR>
    <TD ALIGN="CENTER" CELLPADDING="16">
      <FONT COLOR="${statusColors.text}" FACE="Arial" SIZE="20">${task.description}</FONT>
    </TD>
  </TR>
  <TR>
    <TD ALIGN="CENTER" CELLPADDING="12">
      <TABLE BORDER="0" CELLSPACING="10">
        <TR>
          <TD BGCOLOR="#7c3aed" CELLPADDING="10">
            <FONT COLOR="#ffffff" FACE="Arial" SIZE="16"><B>${task.agent_type || 'unknown'}</B></FONT>
          </TD>
          <TD BGCOLOR="#0d9488" CELLPADDING="10">
            <FONT COLOR="#ffffff" FACE="Arial" SIZE="16"><B>${task.agent_id || 'unassigned'}</B></FONT>
          </TD>
        </TR>
      </TABLE>
    </TD>
  </TR>
</TABLE>`

            dot += `  ${task.task_id} [label=<${htmlLabel}>];\n`
          })

          tasks.forEach(task => {
            if (task.dependency_task_ids && task.dependency_task_ids.length > 0) {
              task.dependency_task_ids.forEach((depId: number) => {
                dot += `  ${depId} -> ${task.task_id} [color="#374151", penwidth="3"];\n`
              })
            }
          })

          dot += '}'
          // Return a computed value or early-exit for this fleet helper.
          return dot
        }

        const dotSource = generateDot(tasks)
        const dagSvg = graphviz.dot(dotSource, 'svg')

        if (dagSvg && dagSvg.length > 100 && dagSvg.includes('<svg')) {
          zip.file('dag.svg', dagSvg)
        }
      } catch (svgError) {
        console.warn('Could not generate DAG SVG for zip:', svgError)
      }

      // Generate and download the zip
      const content = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(content)
      const a = document.createElement('a')
      a.href = url
      a.download = `plan-${planId}-complete.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

    } catch (error) {
      console.error('Error creating full plan download:', error)
      alert('Failed to create full plan download. Please try individual downloads.')
    }
  }

  return (
    <>
      <div className="max-w-7xl mx-auto space-y-6 pb-10">
        <PageHeader
          title="Plan Details"
          leading={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                const fromParam = searchParams.get('from')
                if (fromParam?.startsWith('agent-')) {
                  const agentId = fromParam.replace('agent-', '')
                  navigate(`/agents?agent=${agentId}&tab=allocations`)
                } else {
                  navigate('/plans')
                }
              }}
              className="flex items-center space-x-2 shrink-0 mt-1"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">
                {searchParams.get('from')?.startsWith('agent-') ? 'Back to Agent' : 'Back to Plans'}
              </span>
            </Button>
          }
          actions={
            plan ? (
              <>
                {allocationStatus?.status !== 'fully_allocated' ? (
                  <Button
                    onClick={() => setAllocatePlanId(plan.plan_id)}
                    disabled={allocateMutation.isPending}
                    className="flex items-center space-x-2"
                  >
                    <Users className="w-4 h-4" />
                    {allocateMutation.isPending ? 'Allocating...' : 'Allocate Agents'}
                  </Button>
                ) : (plan.execution_status || 'not_executed') === 'not_executed' ? (
                  <Button
                    onClick={() => navigate(`/plans/${planId}/execute`)}
                    className="flex items-center space-x-2"
                  >
                    <Play className="w-4 h-4" />
                    Execute Plan
                  </Button>
                ) : (
                  <Button
                    onClick={() => navigate(`/plans/${planId}/execute`)}
                    variant="secondary"
                    className="flex items-center space-x-2"
                  >
                    <Activity className="w-4 h-4" />
                    View Execution
                  </Button>
                )}
              </>
            ) : undefined
          }
        />

        {/* Plan Info Card */}
        <Card className="p-6">
          {/* Top Row: P{ID} + Status + Edit Button */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              {/* P{Plan_id} Badge */}
              <span className="tonal-plan-id text-sm">
                P{plan.plan_id}
              </span>

              {/* Planning Method */}
              {plan.planning_strategy && (
                <button
                  type="button"
                  className="tonal-sky text-sm font-semibold hover:opacity-90 transition-opacity"
                  onClick={() => {
                    // Manual planning is not a method-details modal
                    if (plan.planning_strategy === 4) return
                    const methodId = getPlanningMethodId(plan.planning_strategy)
                    navigate(`/plans/${planId}?method_type=planner&method=${methodId}`)
                  }}
                >
                  {getPlanningStrategyName(plan.planning_strategy)}
                </button>
              )}

              {/* Allocation Method */}
              {allocationStatus?.status && allocationStatus.status !== 'unallocated' && plan.allocation_strategy && plan.allocation_strategy !== 4 && (
                <button
                  type="button"
                  className="tonal-violet text-sm font-semibold hover:opacity-90 transition-opacity"
                  onClick={() => {
                    // Manual allocation is not a method-details modal
                    if (plan.allocation_strategy === 5) return
                    const methodId = getAllocationMethodId(plan.allocation_strategy)
                    navigate(`/plans/${planId}?method_type=allocator&method=${methodId}`)
                  }}
                >
                  {getAllocationStrategyName(plan.allocation_strategy)}
                </button>
              )}

              {/* Execution / run status (must reflect plan.execution_status, not just agent health) */}
              {(() => {
                const runStatus = plan.execution_status || 'not_executed'
                const tasks = plan.tasks || [];
                const assignedTasks = tasks.filter(t => t.agent_id);
                const assignedAgentIds = [...new Set(assignedTasks.map(t => t.agent_id).filter(Boolean))];
                const allocationStatusValue = allocationStatus?.status || 'unknown';
                const agentsReady = assignedAgentIds.length > 0 && assignedAgentIds.every((agentId) => {
                  const agent = agents?.find(r => r.agent_id === agentId);
                  // @ts-ignore - TypeScript false positive, we check robotHealth exists
                  const health = robotHealth ? robotHealth[agentId] : undefined;
                  return agent && health?.reachable === true;
                });
                const executionReady = allocationStatusValue === 'fully_allocated' && agentsReady;

                if (runStatus === 'completed') {
                  return (
                    <span className="px-3 py-1.5 border rounded-lg text-sm font-semibold tonal-emerald">
                      <CheckCircle className="w-4 h-4 mr-1 inline" />
                      Execution Completed
                    </span>
                  )
                }
                if (runStatus === 'executing') {
                  return (
                    <span className="px-3 py-1.5 border rounded-lg text-sm font-semibold tonal-amber">
                      <Play className="w-4 h-4 mr-1 inline" />
                      Executing
                    </span>
                  )
                }
                if (runStatus === 'failed') {
                  return (
                    <span className="px-3 py-1.5 border rounded-lg text-sm font-semibold tonal-red">
                      <XCircle className="w-4 h-4 mr-1 inline" />
                      Execution Failed
                    </span>
                  )
                }

                return (
                  <span className={`px-3 py-1.5 border rounded-lg text-sm font-semibold ${
                    executionReady ? 'bg-sky-100 border-sky-300 text-blue-900' :
                    allocationStatusValue === 'fully_allocated' ? 'bg-amber-100 border-amber-300 text-amber-950' :
                    'bg-red-100 border-red-300 text-red-950'
                  }`}>
                    {executionReady ? (
                      <>
                        <Zap className="w-4 h-4 mr-1 inline" />
                        Ready to Execute
                      </>
                    ) : allocationStatusValue === 'fully_allocated' ? 'Agents Unavailable' : 'Not Ready'}
                  </span>
                );
              })()}
            </div>

            {/* Edit Button */}
            {isEditing ? (
              <div className="flex items-center space-x-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsEditing(false)
                    setEditName('')
                    setEditDescription('')
                  }}
                  className="text-sm"
                >
                  <X className="w-4 h-4 mr-1" />
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    updateMutation.mutate({
                      planId: plan.plan_id,
                      name: editName.trim(),
                      description: editDescription.trim()
                    })
                  }}
                  disabled={!editName.trim() || updateMutation.isPending}
                  className="text-sm bg-emerald-600 hover:bg-emerald-700 border border-emerald-500"
                >
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-1" />
                      Save
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setIsEditing(true)
                  setEditName(plan.name || '')
                  setEditDescription(plan.description || '')
                }}
                className="text-sm"
              >
                <Edit className="w-4 h-4 mr-1" />
                Edit
              </Button>
            )}
          </div>

          {/* Plan Name and Description */}
          {isEditing ? (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-1">
                  Plan Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="Enter plan name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-1">
                  Description
                </label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                  placeholder="Enter plan description"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <h2 className="text-xl font-bold text-[var(--color-text)]">
                {plan.name}
              </h2>
              <div className="text-[var(--color-text)] text-base leading-relaxed">
                {plan.description}
              </div>
            </div>
          )}

          {/* Bottom Row: Created date + Download Button */}
          <div className="flex items-center justify-between mt-4">
            {plan.created_at && (
              <div className="text-[var(--color-text-muted)] text-xs">
                Created on: {new Date(plan.created_at).toLocaleString()}
              </div>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                console.log('Download Full Plan button clicked')
                if (typeof downloadFullPlan === 'function') {
                  downloadFullPlan()
                } else {
                  console.error('downloadFullPlan function not found')
                }
              }}
              className="text-sm bg-emerald-600 hover:bg-emerald-700 border border-emerald-500 shadow-md font-semibold"
            >
                <Download className="w-4 h-4 mr-2" />
                Download Full Plan (ZIP)
            </Button>
          </div>
        </Card>

        {/* Tabs */}
        <div className="space-y-4">
          <div className="border-b border-slate-200">
            <div className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
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
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Tab Content */}
          <div className="min-h-[400px]">
            {activeTab === 'overview' && (() => {
              // Calculate execution readiness data outside IIFE for use in both overview and execution readiness

              return (
                <div className="space-y-6">
                  {(() => {
                  // Calculate useful metrics for research scientists
                  const tasks = plan.tasks || [];
                  const assignedTasks = tasks.filter(t => t.agent_id);
                  const unassignedTasks = tasks.filter(t => !t.agent_id);

                  // Check execution readiness - all assigned agents must be online and ready
                  const assignedAgentIds = [...new Set(assignedTasks.map(t => t.agent_id).filter(Boolean))];


                  const agentsReady = assignedAgentIds.length > 0 && assignedAgentIds.every(agentId => {
                    // Check both that agent exists AND is reachable via health check
                    const agent = agents?.find(r => r.agent_id === agentId);
                    const health = robotHealth && agentId ? (robotHealth as any)[agentId] : undefined;
                    return agent && health?.reachable === true;
                  });

                  // Count actually offline agents for better messaging
                  const offlineAgents = assignedAgentIds.filter(agentId => {
                    const agent = agents?.find(r => r.agent_id === agentId);
                    const health = robotHealth && agentId ? (robotHealth as any)[agentId] : undefined;
                    return !agent || health?.reachable !== true;
                  });

                  const allocationStatusValue = allocationStatus?.status || 'unknown';
                  const executionReady = allocationStatusValue === 'fully_allocated' && agentsReady;
                  const runStatus = plan.execution_status || 'not_executed'


                  // Agent utilization stats
                  const agentTypes = [...new Set(tasks.map(t => t.agent_type).filter(Boolean))];
                  const agentIds = [...new Set(assignedTasks.map(t => t.agent_id).filter(Boolean))];

                  // Task distribution by agent type
                  const tasksByType = tasks.reduce((acc, task) => {
                    const type = task.agent_type || 'unassigned';
                    acc[type] = (acc[type] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>);

                  // Tasks by specific agent ID
                  const tasksByAgentId = assignedTasks.reduce((acc, task) => {
                    const agentId = task.agent_id;
                    if (agentId) {
                      acc[agentId] = (acc[agentId] || 0) + 1;
                    }
                    return acc;
                  }, {} as Record<string, number>);

                  return (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Agent Fleet Utilization */}
                      <Card className="p-6 border-slate-200">
                        <div className="flex items-center space-x-3 mb-6">
                          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                            <Bot className="w-4 h-4 text-emerald-800" />
                          </div>
                          {/* Agent Fleet section heading — agents currently assigned on this plan. */}
                          <h3 className="text-lg font-semibold text-[var(--color-text)]">Agent Fleet Utilization</h3>
                        </div>

                        {/* Top metrics in horizontal layout */}
                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-emerald-900 mb-1">
                              {agentTypes.length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Agent Types Used
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-emerald-900 mb-1">
                              {agentIds.length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Agents Assigned
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-blue-900 mb-1">
                              {tasks.length > 0 ? Math.round((assignedTasks.length / tasks.length) * 100) : 0}%
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Assignment Rate
                            </div>
                          </div>
                        </div>

                        {/* Bottom details with styled sections */}
                        {(agentTypes.length > 0 || agentIds.length > 0) && (
                          <div className="space-y-4">
                            {agentTypes.length > 0 && (
                              <div className="bg-slate-50/40 rounded-lg p-3 border border-slate-200/30">
                                <div className="flex items-center space-x-2 mb-3">
                                  <div className="w-5 h-5 bg-slate-50 rounded border border-slate-200 flex items-center justify-center">
                                    <span className="text-xs font-bold text-[var(--color-text)]">T</span>
                                  </div>
                                  <h4 className="text-sm font-semibold text-[var(--color-text)]">Agent Types Used</h4>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {agentTypes.map(type => (
                                    <span key={type} className="px-3 py-2 bg-slate-100 border border-slate-200 text-[var(--color-text)] text-sm font-medium rounded-lg">
                                      {type}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {agentIds.length > 0 && (
                              <div className="bg-slate-50/40 rounded-lg p-3 border border-slate-200/30">
                                <div className="flex items-center space-x-2 mb-3">
                                  <div className="w-5 h-5 bg-emerald-100 rounded border border-emerald-300 flex items-center justify-center">
                                    <span className="text-xs font-bold text-emerald-900">R</span>
                                  </div>
                                  <h4 className="text-sm font-semibold text-emerald-900">Specific Agents Used</h4>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {agentIds.map(agentId => (
                                    <span key={agentId} className="px-3 py-2 bg-emerald-100 border border-emerald-300 text-emerald-900 text-sm font-medium rounded-lg">
                                      {agentId}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </Card>

                      {/* Task Distribution */}
                      <Card className="p-6 border-slate-200">
                        <div>
                          <div className="flex items-center space-x-3 mb-6">
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                            <GitBranch className="w-4 h-4 text-blue-800" />
                          </div>
                          <h3 className="text-lg font-semibold text-[var(--color-text)]">Task Distribution</h3>
                        </div>

                        {/* Top metrics in horizontal layout */}
                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-blue-900 mb-1">
                              {tasks.length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Total Tasks
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-emerald-900 mb-1">
                              {assignedTasks.length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Assigned Tasks
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-amber-950 mb-1">
                              {unassignedTasks.length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Unassigned Tasks
                            </div>
                          </div>
                        </div>
                          {(Object.keys(tasksByType).length > 1 || Object.keys(tasksByAgentId).length > 0) && (
                            <div className="pt-3 border-t border-slate-200 space-y-4">
                              {Object.keys(tasksByType).length > 1 && (
                                <div className="bg-slate-50/40 rounded-lg p-3 border border-slate-200/30">
                                  <div className="flex items-center space-x-2 mb-3">
                                    <div className="w-5 h-5 bg-blue-100 rounded border border-blue-300 flex items-center justify-center">
                                      <span className="text-xs font-bold text-blue-900">T</span>
                                    </div>
                                    <h4 className="text-sm font-semibold text-blue-900">By Agent Type</h4>
                                  </div>
                                  <div className="grid grid-cols-1 gap-2">
                                    {Object.entries(tasksByType)
                                      .sort(([,a], [,b]) => b - a)
                                      .map(([type, count]) => {
                                        const percentage = tasks.length > 0 ? (count / tasks.length) * 100 : 0;
                                        return (
                                          <div key={type} className="flex items-center justify-between p-2 bg-slate-50/30 rounded border border-slate-200/20">
                                            <div className="flex items-center space-x-2">
                                              <span className="text-[var(--color-text)] text-sm font-medium px-2 py-1 bg-slate-100 rounded">
                                                {type}
                                              </span>
                                              <span className="text-[var(--color-text-secondary)] text-xs">
                                                {percentage.toFixed(0)}%
                                              </span>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                              <div className="w-12 bg-slate-50 rounded-full h-2">
                                                <div
                                                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                                  style={{ width: `${percentage}%` }}
                                                />
                                              </div>
                                              <span className="text-lg font-bold text-blue-900 min-w-[1.5rem] text-right">
                                                {count}
                                              </span>
                                            </div>
                                          </div>
                                        );
                                      })}
                                  </div>
                                </div>
                              )}
                              {Object.keys(tasksByAgentId).length > 0 && (
                                <div className="bg-slate-50/40 rounded-lg p-3 border border-slate-200/30">
                                  <div className="flex items-center space-x-2 mb-3">
                                    <div className="w-5 h-5 bg-emerald-100 rounded border border-emerald-300 flex items-center justify-center">
                                      <span className="text-xs font-bold text-emerald-900">R</span>
                                    </div>
                                    <h4 className="text-sm font-semibold text-emerald-900">By Specific Agent</h4>
                                  </div>
                                  <div className="grid grid-cols-1 gap-2">
                                    {Object.entries(tasksByAgentId)
                                      .sort(([,a], [,b]) => b - a) // Sort by task count descending
                                      .map(([agentId, count]) => {
                                        const percentage = assignedTasks.length > 0 ? (count / assignedTasks.length) * 100 : 0;
                                        return (
                                          <div key={agentId} className="flex items-center justify-between p-2 bg-slate-50/30 rounded border border-slate-200/20">
                                            <div className="flex items-center space-x-2">
                                              <span className="text-[var(--color-text)] text-sm font-medium px-2 py-1 bg-emerald-600/50 rounded">
                                                {agentId}
                                              </span>
                                              <span className="text-[var(--color-text-secondary)] text-xs">
                                                {percentage.toFixed(0)}%
                                              </span>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                              <div className="w-12 bg-slate-50 rounded-full h-2">
                                                <div
                                                  className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                                                  style={{ width: `${percentage}%` }}
                                                />
                                              </div>
                                              <span className="text-lg font-bold text-emerald-900 min-w-[1.5rem] text-right">
                                                {count}
                                              </span>
                                            </div>
                                          </div>
                                        );
                                      })}
                                  </div>
                                </div>
                              )}
                            </div>
                        )}
                        </div>
                      </Card>

                      {/* Execution Readiness */}
                      <Card className="p-6 border-slate-200">
                        <div className="flex items-center space-x-3 mb-6">
                          <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
                            <Wand2 className="w-4 h-4 text-purple-900" />
                          </div>
                          <h3 className="text-lg font-semibold text-[var(--color-text)]">Execution Readiness</h3>
                        </div>

                        {/* Top metrics in horizontal layout */}
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                               <div className={`text-2xl font-bold mb-1 ${
                                 allocationStatusValue === 'fully_allocated' ? 'text-blue-900' :
                                 allocationStatusValue === 'partially_allocated' ? 'text-yellow-950' :
                                 allocationStatusValue === 'unallocated' ? 'text-red-900' : 'text-[var(--color-text)]'
                               }`}>
                              {capitalize(allocationStatusValue?.replace('_', ' ') || 'Unknown')}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Plan Status
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className={`text-2xl font-bold mb-1 ${
                              runStatus === 'completed' ? 'text-emerald-900' :
                              runStatus === 'executing' ? 'text-amber-900' :
                              runStatus === 'failed' ? 'text-red-900' :
                              executionReady ? 'text-blue-900' :
                              allocationStatusValue === 'fully_allocated' ? 'text-yellow-950' : 'text-red-900'
                            }`}>
                              {runStatus === 'completed' ? 'Completed' :
                               runStatus === 'executing' ? 'Running' :
                               runStatus === 'failed' ? 'Failed' :
                               executionReady ? 'Ready' :
                               allocationStatusValue === 'fully_allocated' ? 'Agents offline' : 'Not ready'}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Run status
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-[var(--color-text)] mb-1">
                              {tasks.length > 0 ? Math.round((tasks.filter(t => !t.dependency_task_ids?.length).length / tasks.length) * 100) : 0}%
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Dependencies Met
                            </div>
                          </div>
                        </div>

                        {/* Show which agents are offline */}
                        {runStatus === 'not_executed' && allocationStatusValue === 'fully_allocated' && offlineAgents.length > 0 && (
                          <div className="mt-6 p-4 bg-red-100 border border-red-200 rounded-lg">
                            <div className="flex items-center space-x-2 mb-3">
                              <div className="w-5 h-5 bg-red-100 rounded border border-red-300 flex items-center justify-center">
                                <span className="text-xs font-bold text-red-900">!</span>
                              </div>
                              <h4 className="text-sm font-semibold text-red-900">Offline Agents</h4>
                            </div>
                            <div className="text-red-800 text-sm mb-3">
                              The following agents are unreachable and must be online before execution:
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                              {offlineAgents.map(agentId => (
                                <div key={agentId} className="flex items-center space-x-2 p-3 bg-red-500/5 border border-red-500/30 rounded-lg">
                                  <div className="w-8 h-8 bg-red-100 rounded border border-red-300 flex items-center justify-center">
                                    <span className="text-xs font-bold text-red-900">⚠</span>
                                  </div>
                                  <div>
                                    <div className="text-red-900 text-sm font-medium">{agentId}</div>
                                    <div className="text-red-800 text-xs">Unreachable</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </Card>

                      {/* Goals Overview */}
                      <Card className="p-6 border-slate-200">
                        <div className="flex items-center space-x-3 mb-6">
                          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                            <Target className="w-4 h-4 text-emerald-800" />
                          </div>
                          <h3 className="text-lg font-semibold text-[var(--color-text)]">Goals Overview</h3>
                        </div>

                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                              <div className="text-2xl font-bold text-emerald-900 mb-1">
                                {plan?.goal_ids?.length || 0}
                              </div>
                              <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                                Total Goals
                              </div>
                            </div>
                            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                              <div className="text-2xl font-bold text-emerald-900 mb-1">
                                {(() => {
                                  const goalTasks = tasks.filter(task => task.goal_id !== undefined)
                                  return goalTasks.length
                                })()}
                              </div>
                              <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                                Tasks with Goals
                              </div>
                            </div>
                          </div>

                          {plan?.goal_ids && plan.goal_ids.length > 0 && (
                            <div>
                              <div className="text-sm font-medium text-[var(--color-text)] mb-3">Goal IDs:</div>
                              <div className="flex flex-wrap gap-2">
                                {plan.goal_ids.map(goalId => {
                                  const taskCount = tasks.filter((task: any) => task.goal_id === goalId).length
                                  return (
                                    <div key={goalId} className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
                                      <div className="text-sm font-medium text-emerald-900">#{goalId}</div>
                                      <div className="text-xs text-[var(--color-text-secondary)]">{taskCount} tasks</div>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      </Card>

                      {/* Research Metrics */}
                      <Card className="p-6 border-slate-200">
                        <div className="flex items-center space-x-3 mb-6">
                          <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                            <Link className="w-4 h-4 text-orange-900" />
                          </div>
                          <h3 className="text-lg font-semibold text-[var(--color-text)]">Research Metrics</h3>
                        </div>

                        {/* Top metrics in horizontal layout */}
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-orange-950 mb-1">
                              {Math.max(...tasks.map(t => t.dependency_task_ids?.length || 0), 0)}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Max Dependencies
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-orange-950 mb-1">
                              {tasks.length > 0 ? (tasks.reduce((sum, t) => sum + (t.dependency_task_ids?.length || 0), 0) / tasks.length).toFixed(1) : 0}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Avg Dependencies
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                            <div className="text-2xl font-bold text-orange-950 mb-1">
                              {tasks.filter(t => !t.dependency_task_ids?.length).length}
                            </div>
                            <div className="text-[var(--color-text-secondary)] text-xs font-medium">
                              Parallel Tasks
                            </div>
                          </div>
                        </div>
                      </Card>

                    </div>
                  );
                })()}
                </div>
              );
            })()}

            {activeTab === 'tasks' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <GitBranch className="w-5 h-5 text-emerald-800" />
                    </div>
                    <h3 className="text-xl font-bold text-[var(--color-text)]">Task Details</h3>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {canEditPlanTasks ? (
                      <Button variant="secondary" size="sm" onClick={openCreateTask}>
                        <Plus className="w-4 h-4" />
                        Add Task
                      </Button>
                    ) : plan ? (
                      <span className="text-xs text-slate-500 max-w-md text-right">
                        Tasks are read-only: this plan has started or finished execution ({planExecutionStatus.replace(/_/g, ' ')}).
                      </span>
                    ) : null}
                    <button
                      onClick={() => setTaskView('vertical')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        taskView === 'vertical'
                          ? 'bg-blue-100 text-blue-900 border border-blue-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      List View
                    </button>
                    <button
                      onClick={() => setTaskView('dag')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        taskView === 'dag'
                          ? 'bg-blue-100 text-blue-900 border border-blue-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      DAG View
                    </button>
                    <button
                      onClick={downloadDAG}
                      className="px-3 py-1 text-sm rounded transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-slate-200 hover:border-slate-200-strong"
                    >
                      📥 Download DAG (SVG)
                    </button>
                  </div>
                </div>

                {taskView === 'vertical' && (
                  <VerticalTaskList
                    tasks={plan.tasks || []}
                    onEdit={openEditTask}
                    onDelete={requestDeleteTask}
                    canEdit={canEditPlanTasks}
                  />
                )}
                {taskView === 'dag' && <DAGVisualization tasks={plan.tasks || []} />}
              </div>
            )}

            {activeTab === 'goals' && (
              <div className="space-y-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-emerald-800" />
                  </div>
                  <h3 className="text-xl font-bold text-[var(--color-text)]">Goals</h3>
                </div>

                {plan?.goal_ids && plan.goal_ids.length > 0 ? (
                  <div className="grid gap-4">
                    {plan.goal_ids.map(goalId => {
                      const goal = (goals as any[]).find((g: any) => g.goal_id === goalId)
                      const goalTasks = (plan.tasks || []).filter((task: any) => task.goal_id === goalId)

                      return (
                        <Card key={goalId} className="p-4 border-slate-200">
                          <div className="flex items-start space-x-4">
                            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                              <Target className="w-6 h-6 text-emerald-800" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-3 mb-2">
                                <h4 className="text-lg font-semibold text-[var(--color-text)]">Goal #{goalId}</h4>
                                <span className="px-2 py-1 bg-emerald-100 border border-emerald-300 text-emerald-900 rounded text-sm">
                                  {goalTasks.length} tasks
                                </span>
                              </div>
                              <p className="text-[var(--color-text)] mb-3">{goal?.description || 'Goal description not available'}</p>

                              {goalTasks.length > 0 && (
                                <div>
                                  <div className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">Tasks in this plan:</div>
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {goalTasks.map(task => (
                                      <div key={task.task_id} className="bg-slate-50 px-3 py-2 rounded border border-slate-200">
                                        <div className="flex items-center justify-between">
                                          <span className="text-sm font-medium text-[var(--color-text)]">Task #{task.task_id}</span>
                                          <span className={cn(
                                            'px-2 py-0.5 rounded text-xs',
                                            task.status === 'completed' ? 'bg-emerald-100 border border-emerald-300 text-emerald-950' :
                                            task.status === 'in_progress' ? 'bg-sky-100 border border-sky-300 text-sky-950' :
                                            task.status === 'failed' ? 'bg-red-100 border border-red-300 text-red-950' :
                                            'bg-slate-100 border border-slate-300 text-slate-800'
                                          )}>
                                            {task.status}
                                          </span>
                                        </div>
                                        <div className="text-xs text-[var(--color-text-secondary)] mt-1 truncate">{task.description}</div>
                                        {task.agent_id && (
                                          <div className="text-xs text-[var(--color-text-muted)] mt-1">Agent: {task.agent_id}</div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Target className="w-8 h-8" />}
                    title="No goals assigned"
                    description="This plan doesn't have any goals assigned to it."
                  />
                )}
              </div>
            )}

            {activeTab === 'prompts' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Wand2 className="w-5 h-5 text-blue-800" />
                    </div>
                    <h3 className="text-xl font-bold text-[var(--color-text)]">Prompts</h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setPromptsView('planning')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        promptsView === 'planning'
                          ? 'bg-blue-100 text-blue-900 border border-blue-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      Planning
                    </button>
                    <button
                      onClick={() => setPromptsView('allocation')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        promptsView === 'allocation'
                          ? 'bg-violet-100 text-purple-900 border border-violet-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      Allocation
                    </button>
                  </div>
                </div>

                {promptsView === 'planning' && (
                  <Card className="p-6 border-slate-200">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <GitBranch className="w-4 h-4 text-blue-800" />
                        </div>
                        <h4 className="text-lg font-bold text-[var(--color-text)]">Planning Prompts</h4>
                      </div>
                      <button
                        onClick={downloadPlanningPrompts}
                        className="px-3 py-1 text-sm rounded transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-slate-200 hover:border-slate-200-strong"
                      >
                        📥 Download (.zip)
                      </button>
                    </div>
                  {plan.planning_prompts ? (
                    <div className="space-y-4">
                      {typeof plan.planning_prompts === 'object' && plan.planning_prompts.system && plan.planning_prompts.user ? (
                        <div className="space-y-4">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                            <div className="flex items-center space-x-2 mb-3">
                              <div className="w-6 h-6 bg-blue-100 rounded border border-blue-300 flex items-center justify-center">
                                <span className="text-xs font-bold text-blue-900">S</span>
                              </div>
                              <h4 className="text-sm font-semibold text-blue-900">System Prompt</h4>
                            </div>
                            <div className="bg-surface/80 p-4 rounded border border-slate-200">
                              <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                                {plan.planning_prompts.system}
                              </pre>
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                            <div className="flex items-center space-x-2 mb-3">
                              <div className="w-6 h-6 bg-emerald-100 rounded border border-emerald-300 flex items-center justify-center">
                                <span className="text-xs font-bold text-green-900">U</span>
                              </div>
                              <h4 className="text-sm font-semibold text-green-900">User Prompt</h4>
                            </div>
                            <div className="bg-surface/80 p-4 rounded border border-slate-200">
                              <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                                {plan.planning_prompts.user}
                              </pre>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                          <div className="bg-surface/80 p-4 rounded border border-slate-200">
                            <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                              {JSON.stringify(plan.planning_prompts, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-slate-50/40 p-4 rounded-lg border border-slate-200/30">
                      <div className="flex items-center space-x-3 text-[var(--color-text-secondary)]">
                        <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center">
                          <GitBranch className="w-4 h-4" />
                        </div>
                        <span>No planning prompts available for this plan.</span>
                      </div>
                    </div>
                  )}
                  </Card>
                )}

                {promptsView === 'allocation' && (
                  <Card className="p-6 border-slate-200">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
                          <Wand2 className="w-4 h-4 text-purple-900" />
                        </div>
                        <h4 className="text-lg font-bold text-[var(--color-text)]">Allocation Prompts</h4>
                      </div>
                      <button
                        onClick={downloadAllocationPrompts}
                        className="px-3 py-1 text-sm rounded transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-slate-200 hover:border-slate-200-strong"
                      >
                        📥 Download (.zip)
                      </button>
                    </div>
                  {plan.allocation_prompts ? (
                    <div className="space-y-4">
                      {typeof plan.allocation_prompts === 'object' && plan.allocation_prompts.system && plan.allocation_prompts.user ? (
                        <div className="space-y-4">
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                            <div className="flex items-center space-x-2 mb-3">
                              <div className="w-6 h-6 bg-violet-100 rounded border border-violet-300 flex items-center justify-center">
                                <span className="text-xs font-bold text-purple-900">S</span>
                              </div>
                              <h4 className="text-sm font-semibold text-purple-900">System Prompt</h4>
                            </div>
                            <div className="bg-surface/80 p-4 rounded border border-slate-200">
                              <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                                {plan.allocation_prompts.system}
                              </pre>
                            </div>
                          </div>
                          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                            <div className="flex items-center space-x-2 mb-3">
                              <div className="w-6 h-6 bg-emerald-100 rounded border border-emerald-300 flex items-center justify-center">
                                <span className="text-xs font-bold text-green-900">U</span>
                              </div>
                              <h4 className="text-sm font-semibold text-green-900">User Prompt</h4>
                            </div>
                            <div className="bg-surface/80 p-4 rounded border border-slate-200">
                              <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                                {plan.allocation_prompts.user}
                              </pre>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                          <div className="bg-surface/80 p-4 rounded border border-slate-200">
                            <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                              {JSON.stringify(plan.allocation_prompts, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-slate-50/40 p-4 rounded-lg border border-slate-200/30">
                      <div className="flex items-center space-x-3 text-[var(--color-text-secondary)]">
                        <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center">
                          <Wand2 className="w-4 h-4" />
                        </div>
                        <span>No allocation prompts available for this plan. Plan may not have been allocated yet.</span>
                      </div>
                    </div>
                  )}
                  </Card>
                )}
              </div>
            )}

            {activeTab === 'artifacts' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Link className="w-5 h-5 text-blue-800" />
                    </div>
                    <h3 className="text-xl font-bold text-[var(--color-text)]">Artifacts</h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setArtifactsView('planning')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        artifactsView === 'planning'
                          ? 'bg-blue-100 text-blue-900 border border-blue-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      Planning
                    </button>
                    <button
                      onClick={() => setArtifactsView('allocation')}
                      className={cn(
                        'px-3 py-1 text-sm rounded transition-colors',
                        artifactsView === 'allocation'
                          ? 'bg-violet-100 text-purple-900 border border-violet-300'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      )}
                    >
                      Allocation
                    </button>
                  </div>
                </div>

                {artifactsView === 'planning' && (
                  <Card className="p-6 border-slate-200">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <Link className="w-4 h-4 text-blue-800" />
                        </div>
                        <h4 className="text-lg font-bold text-[var(--color-text)]">Planning Artifacts</h4>
                      </div>
                      <button
                        onClick={downloadPlanningArtifacts}
                        className="px-3 py-1 text-sm rounded transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-slate-200 hover:border-slate-200-strong"
                      >
                        📥 Download (.json)
                      </button>
                    </div>
                  {plan.planning_artifacts ? (
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                      <div className="bg-surface/80 p-4 rounded border border-slate-200">
                        <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                          {JSON.stringify(plan.planning_artifacts, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-slate-50/40 p-4 rounded-lg border border-slate-200/30">
                      <div className="flex items-center space-x-3 text-[var(--color-text-secondary)]">
                        <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center">
                          <Link className="w-4 h-4" />
                        </div>
                        <span>No planning artifacts available for this plan.</span>
                      </div>
                    </div>
                  )}
                  </Card>
                )}

                {artifactsView === 'allocation' && (
                  <Card className="p-6 border-slate-200">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
                          <Link className="w-4 h-4 text-purple-900" />
                        </div>
                        <h4 className="text-lg font-bold text-[var(--color-text)]">Allocation Artifacts</h4>
                      </div>
                      <button
                        onClick={downloadAllocationArtifacts}
                        className="px-3 py-1 text-sm rounded transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-slate-200 hover:border-slate-200-strong"
                      >
                        📥 Download (.json)
                      </button>
                    </div>
                  {plan.allocation_artifacts ? (
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                      <div className="bg-surface/80 p-4 rounded border border-slate-200">
                        <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
                          {JSON.stringify(plan.allocation_artifacts, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-slate-50/40 p-4 rounded-lg border border-slate-200/30">
                      <div className="flex items-center space-x-3 text-[var(--color-text-secondary)]">
                        <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
                          <Link className="w-4 h-4" />
                        </div>
                        <span>No allocation artifacts available for this plan. Plan may not have been allocated yet.</span>
                      </div>
                    </div>
                  )}
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Method Detail Modal */}
      <MethodDetailModal
        methodId={selectedMethod?.id || null}
        methodType={selectedMethod?.type || undefined}
        isOpen={!!selectedMethod}
        onClose={() => {
          setSelectedMethod(null)
          navigate(`/plans/${planId}`, { replace: true })
        }}
      />

      {/* Allocate Plan Modal */}
      {allocatePlanId && (
        <Modal
          isOpen={!!allocatePlanId}
          onClose={() => setAllocatePlanId(null)}
          title={`Allocate Plan #${allocatePlanId}`}
          size="wide"
        >
          <AllocatePlanForm
            agents={agents || []}
            onSubmit={(allocationStrategy) => {
              allocateMutation.mutate({ planId: allocatePlanId, allocationStrategy })
            }}
            onCancel={() => setAllocatePlanId(null)}
            isLoading={allocateMutation.isPending}
          />
        </Modal>
      )}

      {/* Task Editor Modal */}
      <Modal
        isOpen={isTaskEditorOpen}
        onClose={() => setIsTaskEditorOpen(false)}
        title={taskEditorMode === 'create' ? 'Add Task' : `Edit Task #${editingTaskId ?? ''}`}
        size="wide"
      >
        <form onSubmit={submitTaskEditor} className="space-y-6 max-h-[75vh] overflow-y-auto">
          <div className="space-y-2">
            <div className="text-sm font-medium text-[var(--color-text)]">Description</div>
            <textarea
              value={taskFormDescription}
              onChange={(e) => setTaskFormDescription(e.target.value)}
              className="w-full min-h-[96px] bg-slate-50/60 border border-slate-200 rounded-lg px-3 py-2 text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-cyber-500/40"
              placeholder="Describe what this task should do…"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-medium text-[var(--color-text)]">Goal</div>
              <select
                value={taskFormGoalId === '' ? '' : String(taskFormGoalId)}
                onChange={(e) => setTaskFormGoalId(e.target.value ? Number(e.target.value) : '')}
                className="w-full bg-slate-50/60 border border-slate-200 rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-cyber-500/40"
              >
                <option value="">Select a goal…</option>
                {((plan?.goal_ids && plan.goal_ids.length > 0 ? plan.goal_ids : (goals as any[]).map((g: any) => g.goal_id)) as number[]).map(
                  (goalId) => {
                    const goal = (goals as any[]).find((g: any) => g.goal_id === goalId)
                    return (
                      <option key={goalId} value={goalId}>
                        Goal #{goalId}{goal?.description ? ` — ${goal.description}` : ''}
                      </option>
                    )
                  }
                )}
              </select>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium text-[var(--color-text)]">Agent (optional)</div>
              <select
                value={taskFormAgentId}
                onChange={(e) => setTaskFormAgentId(e.target.value)}
                className="w-full bg-slate-50/60 border border-slate-200 rounded-lg px-3 py-2 text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-cyber-500/40"
              >
                <option value="">Unassigned</option>
                {(agents as any[] | undefined)?.map((r: any) => (
                  <option key={r.agent_id} value={r.agent_id}>
                    {r.agent_id} ({r.agent_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-[var(--color-text)]">Dependencies</div>
              <div className="text-xs text-[var(--color-text-muted)]">Select tasks that must finish before this one</div>
            </div>
            <div className="bg-surface/60 border border-slate-200/50 rounded-lg p-3 max-h-48 overflow-y-auto space-y-2">
              {(plan?.tasks || [])
                .filter((t: any) => t.task_id && t.task_id !== editingTaskId)
                .map((t: any) => {
                  const checked = taskFormDependencyIds.includes(t.task_id)
                  return (
                    <label key={t.task_id} className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => {
                          setTaskFormDependencyIds((prev) =>
                            checked ? prev.filter((id) => id !== t.task_id) : [...prev, t.task_id]
                          )
                        }}
                        className="mt-1"
                      />
                      <div className="min-w-0">
                        <div className="text-sm text-[var(--color-text)] font-medium">Task #{t.task_id}</div>
                        <div className="text-xs text-[var(--color-text-muted)] truncate">{t.description}</div>
                      </div>
                    </label>
                  )
                })}
              {(plan?.tasks || []).filter((t: any) => t.task_id && t.task_id !== editingTaskId).length === 0 && (
                <div className="text-sm text-[var(--color-text-muted)]">No other tasks available.</div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setIsTaskEditorOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createTaskMutation.isPending || updateTaskMutation.isPending}
            >
              {taskEditorMode === 'create' ? 'Create Task' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Task Confirmation */}
      <Modal
        isOpen={deleteTaskId != null}
        onClose={() => setDeleteTaskId(null)}
        title={deleteTaskId != null ? `Delete Task #${deleteTaskId}` : 'Delete Task'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="text-[var(--color-text)]">
            This will delete the task and automatically remove it from any other tasks’ dependency lists (dependents are not deleted).
          </div>
          <div className="flex items-center justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeleteTaskId(null)} disabled={deleteTaskMutation.isPending}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteTaskId != null && canEditPlanTasks && deleteTaskMutation.mutate(deleteTaskId)}
              disabled={deleteTaskMutation.isPending || deleteTaskId == null || !canEditPlanTasks}
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

// =============================================================================
// Allocation Components (copied from Plans.tsx)
// =============================================================================

/**
 * Props for AllocatePlanForm — agents list, submit/cancel, loading flag.
 */
interface AllocatePlanFormProps {
  agents: Agent[]
  onSubmit: (allocationStrategy: string) => void
  onCancel: () => void
  isLoading: boolean
}

/**
 * Compact selectable card for choosing a planner or allocator method.
 *
 * Used during plan creation and allocation so operators can pick which
 * YAML-defined strategy the fleet server should invoke.
 *
 * @param props.method - MethodSummary from methodsApi.
 * @param props.isSelected - Whether this card is the current selection.
 * @param props.onClick - Selection handler.
 */
function MethodSelectionCard({
  method,
  isSelected,
  onClick
}: {
  method: MethodSummary
  isSelected: boolean
  onClick: () => void
}) {
  // Return the React element tree for this fleet UI component.
  return (
    <Card
      className={cn(
        'cursor-pointer hover:border-slate-200 transition-all p-3',
        isSelected && 'ring-2 ring-cyber-500/50 shadow-lg shadow-cyber-500/20 border-cyber-500'
      )}
      onClick={onClick}
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-[var(--color-text)] text-sm">{method.name}</h3>
          <div className="flex items-center gap-2">
            <span className={cn(
              'px-2 py-0.5 rounded text-xs font-medium border',
              method.method_type === 'foundation model' && 'bg-sky-100 border-blue-500/30 text-blue-800',
              method.method_type === 'hybrid' && 'bg-violet-100 border-violet-300 text-violet-950',
              method.method_type === 'algorithmic' && 'bg-orange-100 border-orange-300 text-orange-950',
              method.method_type === 'manual' && 'bg-slate-100/10 border-slate-200 text-[var(--color-text-secondary)]'
            )}>
              {method.method_type}
            </span>
            {isSelected && (
              <CheckCircle className="w-4 h-4 text-cyber-400" />
            )}
          </div>
        </div>
        <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed line-clamp-2">{method.description}</p>
      </div>
    </Card>
  )
}

/**
 * Form that selects an allocation strategy / agents and assigns plan tasks.
 *
 * Runs after planning: maps each task onto a concrete agent_id.
 *
 * @param props.agents - Registered fleet agents eligible for allocation.
 * @param props.onSubmit - Called with allocation payload.
 * @param props.onCancel - Close without allocating.
 * @param props.isLoading - Disable controls while the mutation runs.
 */
function AllocatePlanForm({ agents, onSubmit, onCancel, isLoading }: AllocatePlanFormProps) {
  // Local state/binding `[selectedAllocator, setSelectedAllocator]` for this fleet UI flow.
  const [selectedAllocator, setSelectedAllocator] = useState<string | null>(null)
  // Local state/binding `[allocatorFilter, setAllocatorFilter]` for this fleet UI flow.
  const [allocatorFilter, setAllocatorFilter] = useState<string>('all')

  // Load available allocators dynamically
  const { data: allocators = [], isLoading: allocatorsLoading, error: allocatorsError } = useQuery({
    queryKey: ['allocators'],
    queryFn: () => methodsApi.list().then(methods => methods.filter(m => m.category === 'allocator')),
  })

  // Allocation options (only real allocators, no manual option)
  const allocationOptions = [...allocators]

  // Filter allocators by method type
  const filteredAllocators = allocationOptions.filter(a =>
    allocatorFilter === 'all' || a.method_type === allocatorFilter
  )

  // Get unique method types for filters
  const allocatorMethodTypes = ['all', ...new Set(allocationOptions.map(a => a.method_type))]

  /**
   * Component/helper `handleSubmit` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  // Local state/binding `handleSubmit` for this fleet UI flow.
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!selectedAllocator) return
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    onSubmit(selectedAllocator)
  }

  // If still loading or error, show loading state
  if (allocatorsLoading) {
    return (
      <div className="p-8 text-center text-[var(--color-text-secondary)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-200 mx-auto mb-4"></div>
        Loading allocation methods...
      </div>
    )
  }

  if (allocatorsError) {
    return (
      <div className="p-8 text-center text-red-800">
        Error loading allocation methods: {allocatorsError.message}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-h-[75vh] overflow-y-auto">
      {allocators.length === 0 ? (
        <div className="text-center py-8 text-[var(--color-text-secondary)]">
          No allocation methods available. Please check your configuration.
        </div>
      ) : (
        <>
          {/* Allocation Methods - Same design as CreatePlanForm */}
          <div>
        <h3 className="text-lg font-semibold text-[var(--color-text)] mb-6 flex items-center gap-3">
          <span className="w-3 h-3 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full"></span>
          Choose Allocation Method
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-base font-medium text-[var(--color-text)] flex items-center gap-2">
              <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
              Allocation Methods
            </h4>
            {/* Method Type Filter - Below header */}
            <div className="flex gap-1 flex-wrap">
              {allocatorMethodTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => setAllocatorFilter(type)}
                  className={cn(
                    'px-3 py-1 text-xs rounded-full border transition-all',
                    allocatorFilter === type
                      ? 'bg-emerald-100 border-emerald-400 text-emerald-900'
                      : 'border-slate-200 text-[var(--color-text-secondary)] hover:border-slate-200-strong'
                  )}
                >
                  {type === 'all' ? 'All' : type}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {filteredAllocators.map((allocator) => (
              <MethodSelectionCard
                key={allocator.type}
                method={allocator}
                isSelected={selectedAllocator === allocator.type}
                onClick={() => setSelectedAllocator(allocator.type)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Available Agents */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4 flex items-center gap-3">
          <span className="w-3 h-3 bg-gradient-to-r from-violet-400 to-pink-400 rounded-full"></span>
          Available Agents
        </h3>
        <div className="mb-4">
          <div className="text-sm text-[var(--color-text-secondary)]">
            {agents.filter(r => r.status === 'running' || r.status === 'registered').length} of {agents.length} agents available
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
          {agents.map((agent) => (
            <Card
              key={agent.agent_id}
              className={cn(
                'p-3 transition-all',
                agent.status === 'running' || agent.status === 'registered'
                  ? 'bg-emerald-100 border-emerald-500/30'
                  : 'bg-slate-50 border-slate-200'
              )}
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-3 h-3 rounded-full flex-shrink-0',
                  agent.status === 'running' || agent.status === 'registered'
                    ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50'
                    : 'bg-slate-100'
                )} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-[var(--color-text)] text-sm truncate">
                    {agent.agent_id}
                  </div>
                  <div className="text-xs text-[var(--color-text-secondary)]">
                    {agent.agent_type}
                  </div>
                </div>
                <div className={cn(
                  'text-xs px-2 py-1 rounded-full',
                  agent.status === 'running' || agent.status === 'registered'
                    ? 'bg-emerald-100 text-emerald-900'
                    : 'bg-slate-100 text-[var(--color-text-secondary)]'
                )}>
                  {agent.status === 'running' || agent.status === 'registered' ? 'Available' : 'Offline'}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={!selectedAllocator || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Allocating...
            </>
          ) : (
            <>
              <Users className="w-4 h-4" />
              Allocate Agents
            </>
          )}
        </Button>
      </div>
        </>
      )}
    </div>
  )
}
