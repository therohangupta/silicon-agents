/**
 * @fileoverview Agents registry page — fleet member health, config, and task dispatch.
 *
 * Route: `/agents`
 *
 * An **Agent** is a registered worker in the fleet (often backed by a task
 * server host:port). Agents advertise an `agent_type` and capabilities that
 * planners/allocators use when building and assigning **Tasks** inside a
 * **Plan**. This page is the operator console for the agent population.
 *
 * Major capabilities:
 * - Grid of AgentCards with live reachability / latency health checks
 * - Detail modal tabs: Overview, Allocations (which plans/goals/tasks),
 *   Capabilities, YAML Configuration, Send Task (ad-hoc dispatch), and
 *   live video / telemetry streaming when supported
 * - Register new agents and delete / refresh health for existing ones
 *
 * Telemetry: `useRealtimeUpdates` plus `useTelemetryStream` and
 * `LiveVideoCanvas` surface runtime signals beyond REST CRUD.
 *
 * Behavior and JSX structure must stay intact; this file is heavily commented
 * for onboarding operators and dashboard contributors.
 */
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, Plus, Trash2, Wifi, WifiOff, RefreshCw, CheckCircle, XCircle, Loader2, FileCode, Download, Settings, Cpu, Network, FileX, Target, Wrench, Info, Send, RotateCcw, Video, Activity, Terminal } from 'lucide-react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/common/Button'
import { Modal } from '../components/common/Modal'
import { EmptyState } from '../components/common/EmptyState'
import { LiveVideoCanvas } from '../components/common/LiveVideoCanvas'
import { useRealtimeUpdates, agentsApi } from '../lib/api'

import { cn } from '../lib/utils'
import { useTelemetryStream } from '../hooks/useTelemetryStream'
import type { Agent } from '../types'

// =============================================================================
// Health Check Types
// =============================================================================

/**
 * Health-check payload: reachability, latency, and optional error for an agent task server.
 */
interface AgentHealth {
  /** Agent identity that was probed. */
  agent_id: string
  /** Task-server host used for the health check. */
  host: string
  /** Task-server port used for the health check. */
  port: number
  /** True when the agent task server responded successfully. */
  reachable: boolean
  /** Round-trip latency in milliseconds when reachable. */
  latency_ms?: number
  /** Error message when the probe failed. */
  error?: string
}

/**
 * Agent plus optional YAML path/content for configuration introspection.
 */
interface AgentYamlDetails {
  /** Registry Agent record. */
  agent: Agent
  /** Filesystem path of the agent YAML, if known. */
  yaml_path: string | null
  /** Parsed YAML object for configuration introspection. */
  yaml_content: Record<string, unknown> | null
}

// =============================================================================
// Agent Allocations API
// =============================================================================

/**
 * Summary of plans/goals/tasks currently allocated to a given agent_id.
 */
interface AgentAllocations {
  /** Agent these allocations belong to. */
  agent_id: string
  /** Number of plans that assign work to this agent. */
  plans_count: number
  /** Number of distinct goals linked through those plans. */
  goals_count: number
  /** Number of tasks allocated to this agent. */
  tasks_count: number
  /** Per-plan allocation summaries (ids, goals, task counts, status). */
  plans: Array<{
    plan_id: number
    goal_ids: number[]
    task_count: number
    status: string
    name: string
    description: string
  }>
  /** Flat list of goal ids associated with this agent via plans. */
  goals: number[]
}


// Info Card Component for technical details
/**
 * Compact info tile for agent technical details (host, latency, status).
 *
 * @param props.title - Field label.
 * @param props.value - Primary value string.
 * @param props.subtitle - Optional secondary line.
 * @param props.icon - Lucide (or other) icon node.
 * @param props.status - Optional reachability boolean for color coding.
 */
function InfoCard({
  title,
  value,
  subtitle,
  icon,
  status
}: {
  title: string
  value: string
  subtitle?: string
  icon: React.ReactNode
  status?: boolean
}) {
  // Return the React element tree for this fleet UI component.
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <div className={cn(
          "p-2 rounded-lg flex-shrink-0",
          status === true ? "bg-emerald-500/10 text-emerald-400" :
          status === false ? "bg-red-500/10 text-red-400" :
          "bg-slate-50 text-[var(--color-text-secondary)]"
        )}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide font-medium">{title}</p>
          <p className="font-medium text-[var(--color-text)] truncate">{value}</p>
          {subtitle && <p className="text-xs text-[var(--color-text-secondary)] truncate">{subtitle}</p>}
        </div>
      </div>
    </Card>
  )
}

// =============================================================================
// Agent Card with Health Status
// =============================================================================

/**
 * Grid card for one registered agent: health, allocation counts, quick actions.
 *
 * @param props.agent - Agent entity from agentsApi.
 * @param props.health - Optional AgentHealth from /api/agents/health.
 * @param props.allocations - Optional plan/goal/task counts for this agent.
 * @param props.onClick - Open the agent detail modal.
 * @param props.onDelete - Unregister / delete the agent.
 * @param props.onCheckHealth - Trigger a fresh reachability probe.
 * @param props.isChecking - True while a health check is in flight.
 */
function AgentCard({
  agent,
  health,
  allocations,
  onClick,
  onDelete,
  onCheckHealth,
  isChecking
}: {
  agent: Agent
  health?: AgentHealth
  allocations?: { plans_count: number; goals_count: number; tasks_count: number }
  onClick: () => void
  onDelete: (id: string) => void
  onCheckHealth: (id: string) => void
  isChecking: boolean
}) {
  // Reachability/latency map for agent task servers (online/offline telemetry).
  const isReachable = health?.reachable === true

  // Return the React element tree for this fleet UI component.
  return (
    <Card hover className="group relative overflow-hidden p-0 cursor-pointer" onClick={onClick}>
      {/* Top accent */}
      <div className={cn(
        'h-1',
        isChecking ? 'bg-gradient-to-r from-yellow-400 to-amber-400' :
        isReachable ? 'bg-gradient-to-r from-emerald-400 to-cyan-400' :
        'bg-gradient-to-r from-red-400 to-rose-400'
      )} />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center',
              isReachable ? 'bg-emerald-50 ring-1 ring-emerald-200/60' : 'bg-slate-50 ring-1 ring-slate-200/60'
            )}>
              <Bot className={cn('w-5 h-5', isReachable ? 'text-emerald-600' : 'text-slate-400')} />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">{agent.agent_id}</h3>
              <p className="text-xs text-slate-500">{agent.agent_type}</p>
            </div>
          </div>

          <span className={cn(
            'inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full',
            isChecking ? 'bg-yellow-50 text-yellow-700 ring-1 ring-yellow-200/80' :
            isReachable ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/80' :
            'bg-red-50 text-red-700 ring-1 ring-red-200/80'
          )}>
            {isChecking ? <Loader2 className="w-3 h-3 animate-spin" /> :
             isReachable ? <CheckCircle className="w-3 h-3" /> :
             <XCircle className="w-3 h-3" />}
            {isChecking ? 'Checking' : isReachable ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Allocation pills */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className="tonal-sky">{allocations?.plans_count || 0} plans</span>
          <span className="tonal-emerald">{allocations?.goals_count || 0} goals</span>
          <span className="tonal-violet">{allocations?.tasks_count || 0} tasks</span>
        </div>

        {/* Connection footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            {isReachable ? <Wifi className="w-3.5 h-3.5 text-emerald-500" /> : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
            <span className="font-mono">{agent.task_server_info?.host}:{agent.task_server_info?.port}</span>
            {health?.latency_ms && <span className="text-emerald-600">({Math.round(health.latency_ms)}ms)</span>}
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="sm" onClick={() => onCheckHealth(agent.agent_id)} className="text-slate-400 hover:text-slate-700 p-1.5 h-7 w-7">
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onDelete(agent.agent_id)} className="text-red-400 hover:text-red-600 hover:bg-red-50 p-1.5 h-7 w-7">
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {health?.error && <p className="text-xs text-red-600 mt-2">{health.error}</p>}
      </div>
    </Card>
  )
}

// Config Section Component
/**
 * Collapsible key/value section inside an agent's YAML configuration viewer.
 *
 * @param props.title - Section heading (e.g. Agent Identity).
 * @param props.items - Array of {key, value} config entries.
 * @param props.icon - Optional section icon.
 */
function ConfigSection({
  title,
  items,
  icon
}: {
  title: string
  items: Array<{key: string, value: any}>
  icon?: React.ReactNode
}) {
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isExpanded, setIsExpanded] = useState(true)

  // Return the React element tree for this fleet UI component.
  return (
    <Card className="p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left mb-3"
      >
        <div className="flex items-center gap-2">
          {icon && <div className="text-[var(--color-text-secondary)]">{icon}</div>}
          <h5 className="font-medium text-[var(--color-text)]">{title}</h5>
          <span className="text-xs text-[var(--color-text-muted)] bg-slate-50 px-2 py-0.5 rounded-full">
            {items.length}
          </span>
        </div>
        <div className="text-[var(--color-text-secondary)]">
          {isExpanded ? '−' : '+'}
        </div>
      </button>

      {isExpanded && (
        <div className="space-y-2">
          {items.map(({key, value}) => (
            <div key={key} className="flex justify-between items-start py-1 border-b border-slate-200/50">
              <span className="text-sm text-[var(--color-text-secondary)] font-mono flex-shrink-0 mr-4">{key}:</span>
              <span className="text-sm text-[var(--color-text)] font-mono break-all text-right">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

// Configuration Viewer Component
/**
 * Parses agent YAML into logical sections (identity, networking, capabilities).
 *
 * @param props.config - Parsed YAML object from the fleet server.
 * @param props.filePath - Source path shown to operators for traceability.
 */
function ConfigurationViewer({
  config,
  filePath
}: {
  config: Record<string, unknown>
  filePath: string
}) {
  // Parse configuration into logical sections
  /**
   * Component/helper `parseConfigSections` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const parseConfigSections = (config: Record<string, unknown>) => {
    // Local state/binding `sections` for this fleet UI flow.
    const sections = []

    // Agent metadata
    const robotSection = []
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.agent_id) robotSection.push({key: 'agent_id', value: config.agent_id})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.agent_type) robotSection.push({key: 'agent_type', value: config.agent_type})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.description) robotSection.push({key: 'description', value: config.description})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (robotSection.length > 0) {
      sections.push({
        title: 'Agent Identity',
        items: robotSection,
        icon: <Bot className="w-4 h-4" />
      })
    }

    // Connection settings
    const connectionSection = []
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.host) connectionSection.push({key: 'host', value: config.host})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.port) connectionSection.push({key: 'port', value: config.port})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (connectionSection.length > 0) {
      sections.push({
        title: 'Network Configuration',
        items: connectionSection,
        icon: <Network className="w-4 h-4" />
      })
    }

    // Local state/binding `capabilitySection` for this fleet UI flow.
    const capabilitySection = []
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.capabilities) capabilitySection.push({key: 'capabilities', value: config.capabilities})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (capabilitySection.length > 0) {
      sections.push({
        title: 'Capabilities',
        items: capabilitySection,
        icon: <Cpu className="w-4 h-4" />
      })
    }

    // Software settings
    const softwareSection = []
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.software) softwareSection.push({key: 'software', value: config.software})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.parameters) softwareSection.push({key: 'parameters', value: config.parameters})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (config.calibration) softwareSection.push({key: 'calibration', value: config.calibration})
    // Conditional branch controlling fleet UI flow or data filtering.
    if (softwareSection.length > 0) {
      sections.push({
        title: 'Software Configuration',
        items: softwareSection,
        icon: <Settings className="w-4 h-4" />
      })
    }

    // Everything else
    const otherItems = Object.entries(config).filter(([key]) =>
      !['agent_id', 'agent_type', 'description', 'host', 'port', 'hardware', 'capabilities', 'sensors', 'software', 'parameters', 'calibration'].includes(key)
    ).map(([key, value]) => ({key, value}))

    // Conditional branch controlling fleet UI flow or data filtering.
    if (otherItems.length > 0) {
      sections.push({
        title: 'Additional Settings',
        items: otherItems,
        icon: <FileCode className="w-4 h-4" />
      })
    }

    // Return a computed value or early-exit for this fleet helper.
    return sections
  }

  const sections = parseConfigSections(config)

  return (
    <div className="space-y-4">
      <div className="text-xs text-[var(--color-text-secondary)] font-mono p-2 bg-surface/60 rounded border border-slate-200">
        📁 {filePath}
      </div>

      {sections.map(section => (
        <ConfigSection
          key={section.title}
          title={section.title}
          items={section.items}
          icon={section.icon}
        />
      ))}

      {/* Raw JSON fallback */}
      <Card className="p-4">
        <h5 className="font-medium text-[var(--color-text)] mb-3 flex items-center gap-2">
          <FileCode className="w-4 h-4" />
          Raw Configuration
        </h5>
        <pre className="p-3 bg-surface rounded text-xs text-[var(--color-text)] overflow-auto max-h-48 font-mono">
          {JSON.stringify(config, null, 2)}
        </pre>
      </Card>
    </div>
  )
}

// =============================================================================
// Agent Detail Modal
// =============================================================================

// =============================================================================
// Tab Components
// =============================================================================

/**
 * Tab strip for the agent detail modal (overview, allocations, config, send task, …).
 *
 * @param props.tabs - Tab descriptors with id/label/icon.
 * @param props.activeTab - Currently selected tab id.
 * @param props.onChange - Tab change handler.
 */
function TabNavigation({
  tabs,
  activeTab,
  onTabChange
}: {
  tabs: Array<{id: string, label: string, icon: React.ReactNode}>
  activeTab: string
  onTabChange: (tabId: string) => void
}) {
  // Return the React element tree for this fleet UI component.
  return (
    <div className="flex border-b border-slate-200 mb-6">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === tab.id
              ? 'border-cyber-500 text-cyber-400'
              : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
          )}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  )
}

/**
 * Agent overview tab: identity, reachability, and high-level connection stats.
 *
 * @param props.agent - Agent under inspection.
 * @param props.health - Optional live health payload.
 */
function OverviewTab({ agent, health }: { agent: Agent, health?: AgentHealth }) {
  // Reachability/latency map for agent task servers (online/offline telemetry).
  const isReachable = health?.reachable ?? false

  // Return the React element tree for this fleet UI component.
  return (
    <div className="space-y-6">
      {/* Technical Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InfoCard
          title="Embodiment"
          value={agent.agent_type}
          icon={<Bot className="w-5 h-5" />}
        />
        <InfoCard
          title="Connection"
          value={health?.reachable ? "Online" : "Offline"}
          subtitle={`${agent.task_server_info?.host || 'Unknown'}:${agent.task_server_info?.port || 'Unknown'}`}
          icon={<Network className="w-5 h-5" />}
          status={health?.reachable}
        />
        <InfoCard
          title="Capabilities"
          value={`${agent.capabilities.length} Skills`}
          subtitle="Available Actions"
          icon={<Settings className="w-5 h-5" />}
        />
      </div>

      {/* Description */}
      {agent.description && (
        <Card className="p-4">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] mb-2 uppercase tracking-wide">Description</h4>
          <p className="text-[var(--color-text)] leading-relaxed">{agent.description}</p>
        </Card>
      )}

      {/* Connection Details */}
      <Card className="p-4">
        <h4 className="text-sm font-medium text-[var(--color-text-secondary)] mb-3 uppercase tracking-wide">Connection Details</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-[var(--color-text-muted)]">Host:</span>
            <span className="text-[var(--color-text)] ml-2 font-mono">{agent.task_server_info?.host || 'Unknown'}</span>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Port:</span>
            <span className="text-[var(--color-text)] ml-2 font-mono">{agent.task_server_info?.port || 'Unknown'}</span>
          </div>
          <div>
            <span className="text-[var(--color-text-muted)]">Status:</span>
            <span className={cn("ml-2", isReachable ? "text-emerald-400" : "text-red-400")}>
              {isReachable ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {health?.latency_ms && (
            <div>
              <span className="text-[var(--color-text-muted)]">Latency:</span>
              <span className="text-emerald-400 ml-2">{Math.round(health.latency_ms)}ms</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

/**
 * Shows which plans, goals, and tasks currently allocate work to this agent.
 *
 * @param props.agentId - Agent id used to fetch allocation summary.
 */
function AllocationsTab({ agentId }: { agentId: string }) {
  // React Router navigate helper for Plans ↔ PlanDetails ↔ Execution transitions.
  const navigate = useNavigate()
  // List-page filter/sort state for browsing fleet entities.
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: allocations, isLoading } = useQuery({
    queryKey: ['agent-allocations', agentId],
    queryFn: () => agentsApi.getAllocations(agentId),
  })

  // Fleet plans — each binds goals, strategies, tasks, and execution state.
  const filteredPlans = allocations?.plans.filter(plan => {
    if (statusFilter === 'all') return true
    return plan.status === statusFilter
  }) || []

  // Conditional branch controlling fleet UI flow or data filtering.
  if (isLoading) {
    // Return the React element tree for this fleet UI component.
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--color-text-secondary)]" />
        <span className="ml-3 text-[var(--color-text-secondary)]">Loading allocations...</span>
      </div>
    )
  }

  // Which plans/goals/tasks currently assign work to an agent.
  if (!allocations) {
    // Return the React element tree for this fleet UI component.
    return (
      <div className="text-center py-12 text-[var(--color-text-muted)]">
        <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Failed to load allocation data</p>
      </div>
    )
  }

  // Return the React element tree for this fleet UI component.
  return (
    <div className="space-y-6">
      {/* Allocation Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-[var(--color-text)]">{allocations.plans_count}</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Active Plans</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-[var(--color-text)]">{allocations.goals_count}</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Goals Assigned</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-[var(--color-text)]">{allocations.tasks_count}</div>
          <div className="text-sm text-[var(--color-text-secondary)]">Tasks Assigned</div>
        </Card>
      </div>

      {/* Plans Section */}
      {allocations.plans.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-[var(--color-text)] flex items-center gap-2">
              <Target className="w-4 h-4" />
              Allocated Plans ({allocations.plans.length})
            </h4>
          </div>

          {/* Status Filters */}
          <div className="flex gap-2">
            {[
              { key: 'all', label: 'All Plans', count: allocations.plans.length },
              { key: 'not_executed', label: 'Pending', count: allocations.plans.filter(p => p.status === 'not_executed').length },
              { key: 'executing', label: 'Executing', count: allocations.plans.filter(p => p.status === 'executing').length },
              { key: 'completed', label: 'Completed', count: allocations.plans.filter(p => p.status === 'completed').length },
            ].map(({ key, label, count }) => (
              <Button
                key={key}
                variant={statusFilter === key ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setStatusFilter(key)}
                className="text-xs"
              >
                {label} ({count})
              </Button>
            ))}
          </div>

          {/* Plans Grid */}
          <div className="max-h-96 overflow-y-auto">
            {filteredPlans.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredPlans.map((plan) => (
                  <Card
                    key={plan.plan_id}
                    className="p-4 cursor-pointer hover:bg-slate-50 transition-all duration-200 hover:shadow-md"
                    onClick={() => navigate(`/plans/${plan.plan_id}?from=agent-${agentId}`)}
                  >
                    <div className="flex justify-between items-start gap-2 mb-2">
                      <div className="font-semibold text-slate-900 text-sm min-w-0 leading-snug">
                        #{plan.plan_id}: {plan.name}
                      </div>
                      <div className={cn(
                        'shrink-0 px-2 py-0.5 rounded-full text-xs font-semibold',
                        plan.status === 'completed' ? 'tonal-emerald' :
                        plan.status === 'executing' ? 'tonal-amber' :
                        plan.status === 'failed' ? 'tonal-red' :
                        'tonal-amber'
                      )}>
                        {plan.status === 'not_executed' ? 'Pending' :
                         plan.status === 'executing' ? 'Running' :
                         plan.status.charAt(0).toUpperCase() + plan.status.slice(1)}
                      </div>
                    </div>

                    {/* Plan Name and Description */}
                    <div className="mb-3">
                      {plan.description && (
                        <p className="text-xs text-slate-600 line-clamp-2">
                          {plan.description}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col items-center justify-center text-center gap-1 rounded-lg bg-cyan-50 ring-1 ring-cyan-200/70 px-3 py-3 min-h-[5.5rem]">
                        <span className="text-2xl font-bold tabular-nums text-cyan-950 leading-none">
                          {plan.task_count}
                        </span>
                        <span className="text-[11px] font-semibold text-cyan-900 leading-snug">
                          Tasks on this agent
                        </span>
                      </div>
                      <div className="flex flex-col items-center justify-center text-center gap-1 rounded-lg bg-emerald-50 ring-1 ring-emerald-200/70 px-3 py-3 min-h-[5.5rem]">
                        <span className="text-2xl font-bold tabular-nums text-emerald-950 leading-none">
                          {plan.goal_ids.length}
                        </span>
                        <span className="text-[11px] font-semibold text-emerald-900 leading-snug">
                          Plan goals
                        </span>
                      </div>
                    </div>

                    {plan.goal_ids.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-200">
                        <div className="flex flex-wrap gap-0.5">
                          {plan.goal_ids.slice(0, 4).map((goalId) => (
                            <span
                              key={goalId}
                              className="px-1.5 py-0.5 bg-cyan-100 text-cyan-950 border border-cyan-300 rounded text-xs font-medium"
                            >
                              G{goalId}
                            </span>
                          ))}
                          {plan.goal_ids.length > 4 && (
                            <span className="px-1.5 py-0.5 bg-slate-100 text-[var(--color-text-secondary)] rounded text-xs">
                              +{plan.goal_ids.length - 4}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[var(--color-text-muted)]">
                <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No plans match the selected filter</p>
              </div>
            )}
          </div>
        </div>
      )}

      {allocations.plans.length === 0 && (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>This agent has no active plan allocations</p>
        </div>
      )}
    </div>
  )
}

/**
 * Lists capability strings the allocator may match when assigning tasks.
 *
 * @param props.capabilities - Capability tags from the agent registry.
 */
function CapabilitiesTab({ capabilities }: { capabilities: string[] }) {
  // Return the React element tree for this fleet UI component.
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wrench className="w-5 h-5 text-[var(--color-text-secondary)]" />
          <h4 className="text-lg font-semibold text-[var(--color-text)]">Agent Capabilities</h4>
        </div>
        <span className="text-sm text-[var(--color-text-muted)] bg-slate-50 px-3 py-1 rounded-full">
          {capabilities.length} skills
        </span>
      </div>

      <Card className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {capabilities.map((capability, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200"
            >
              <div className="w-2 h-2 bg-cyber-400 rounded-full flex-shrink-0"></div>
              <span className="text-sm text-[var(--color-text)] font-mono">
                {capability}
              </span>
            </div>
          ))}
        </div>
        {capabilities.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)]">
            <Wrench className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No capabilities configured</p>
          </div>
        )}
      </Card>
    </div>
  )
}

/**
 * Loads and displays the agent's YAML configuration from the fleet server.
 *
 * @param props.agent - Agent whose YAML should be fetched/rendered.
 */
function ConfigurationTab({ agent }: { agent: Agent }) {
  // Local state/binding `[yamlDetails, setYamlDetails]` for this fleet UI flow.
  const [yamlDetails, setYamlDetails] = useState<AgentYamlDetails | null>(null)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isLoadingYaml, setIsLoadingYaml] = useState(false)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isRefreshing, setIsRefreshing] = useState(false)
  // Local state/binding `[refreshMessage, setRefreshMessage]` for this fleet UI flow.
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null)
  // TanStack Query client used to invalidate fleet entity caches after mutations.
  const queryClient = useQueryClient()

  // Fetch YAML details
  useEffect(() => {
    if (agent) {
      setIsLoadingYaml(true)
      fetch(`/api/agents/${agent.agent_id}/yaml`)
        .then(res => res.json())
        .then(data => {
          setYamlDetails(data)
          setIsLoadingYaml(false)
        })
        .catch(() => setIsLoadingYaml(false))
    }
  }, [agent])

  /**
   * Component/helper `handleRefreshFromYaml` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  // Local state/binding `handleRefreshFromYaml` for this fleet UI flow.
  const handleRefreshFromYaml = async () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!agent) return
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsRefreshing(true)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setRefreshMessage(null)

    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Registered fleet agents available for allocation and health display.
      const response = await fetch(`/api/agents/${agent.agent_id}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_path: yamlDetails?.yaml_path })
      })

      // Conditional branch controlling fleet UI flow or data filtering.
      if (response.ok) {
        // Local state/binding `data` for this fleet UI flow.
        const data = await response.json()
        // Invoke a setter/helper that advances fleet UI or telemetry state.
        setRefreshMessage('✓ Agent refreshed from YAML successfully!')
        queryClient.invalidateQueries({ queryKey: ['agents'] })
        // Re-fetch YAML details
        const yamlRes = await fetch(`/api/agents/${agent.agent_id}/yaml`)
        // Local state/binding `yamlData` for this fleet UI flow.
        const yamlData = await yamlRes.json()
        // Invoke a setter/helper that advances fleet UI or telemetry state.
        setYamlDetails(yamlData)
      } else {
        // Local state/binding `error` for this fleet UI flow.
        const error = await response.json()
        // Invoke a setter/helper that advances fleet UI or telemetry state.
        setRefreshMessage(`✗ ${error.detail || 'Failed to refresh'}`)
      }
    } catch (error) {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setRefreshMessage('✗ Failed to refresh from YAML')
    }
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsRefreshing(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCode className="w-5 h-5 text-[var(--color-text-secondary)]" />
          <h4 className="text-lg font-semibold text-[var(--color-text)]">Configuration Details</h4>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={handleRefreshFromYaml}
          disabled={isRefreshing || !yamlDetails?.yaml_path}
        >
          <Download className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
          {isRefreshing ? 'Refreshing...' : 'Refresh from YAML'}
        </Button>
      </div>

      {isLoadingYaml ? (
        <Card className="p-8">
          <div className="flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--color-text-secondary)]" />
            <span className="text-[var(--color-text-secondary)]">Loading configuration details...</span>
          </div>
        </Card>
      ) : yamlDetails?.yaml_content ? (
        <ConfigurationViewer
          config={yamlDetails.yaml_content}
          filePath={yamlDetails.yaml_path || 'Unknown path'}
        />
      ) : (
        <Card className="p-8">
          <div className="flex flex-col items-center justify-center gap-3">
            <FileX className="w-8 h-8 text-[var(--color-text-muted)]" />
            <div className="text-center">
              <h5 className="font-medium text-[var(--color-text-secondary)] mb-1">Configuration Not Found</h5>
              <p className="text-sm text-[var(--color-text-muted)]">YAML source file not available for this agent</p>
            </div>
          </div>
        </Card>
      )}

      {refreshMessage && (
        <div className={cn(
          'p-3 rounded-lg border text-sm font-medium',
          refreshMessage.startsWith('✓')
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-red-500/10 border-red-500/20 text-red-400'
        )}>
          {refreshMessage}
        </div>
      )}
    </div>
  )
}

/**
 * Modal shell hosting agent detail tabs plus live telemetry panels.
 *
 * @param props.agent - Selected agent or null when closed.
 * @param props.health - Optional health for overview coloring.
 * @param props.isOpen - Modal visibility.
 * @param props.onClose - Close handler (also clears URL deep-link).
 */
function AgentDetailModal({
  agent,
  health,
  isOpen,
  onClose,
  onRefresh,
  activeTab,
  onTabChange
}: {
  agent: Agent | null
  health?: AgentHealth
  isOpen: boolean
  onClose: () => void
  onRefresh: () => void
  activeTab: string
  onTabChange: (tab: string) => void
}) {

  // Local state/binding `tabs` for this fleet UI flow.
  const tabs = [
    { id: 'overview', label: 'Overview', icon: <Info className="w-4 h-4" /> },
    { id: 'allocations', label: 'Allocations', icon: <Target className="w-4 h-4" /> },
    { id: 'capabilities', label: 'Capabilities', icon: <Wrench className="w-4 h-4" /> },
    { id: 'config', label: 'Configuration', icon: <FileCode className="w-4 h-4" /> },
    { id: 'send-task', label: 'Send Task', icon: <Send className="w-4 h-4" /> }
  ]

  // Conditional branch controlling fleet UI flow or data filtering.
  if (!agent) return null

  // Return the React element tree for this fleet UI component.
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`${agent.agent_id}`} size="wide" className="max-h-[90vh]">
      <div className="space-y-6 max-h-[75vh] overflow-y-auto">
        {/* Tab Navigation */}
        <TabNavigation tabs={tabs} activeTab={activeTab} onTabChange={onTabChange} />

        {/* Tab Content */}
        {activeTab === 'overview' && <OverviewTab agent={agent} health={health} />}
        {activeTab === 'allocations' && <AllocationsTab agentId={agent.agent_id} />}
        {activeTab === 'capabilities' && <CapabilitiesTab capabilities={agent.capabilities} />}
        {activeTab === 'config' && <ConfigurationTab agent={agent} />}
        {activeTab === 'send-task' && <SendTaskTab agent={agent} health={health} />}

      </div>
    </Modal>
  )
}

// =============================================================================
// Send Task Tab Component
// =============================================================================

/**
 * Ad-hoc task dispatch UI — send a one-off task to this agent's task server.
 *
 * Bypasses full plan planning/allocation for operator debugging and tests.
 *
 * @param props.agent - Target agent.
 * @param props.health - Reachability gate for send actions.
 */
function SendTaskTab({ agent, health }: { agent: Agent, health?: AgentHealth }) {
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [taskDescription, setTaskDescription] = useState('')
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isSending, setIsSending] = useState(false)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [recordEpisode, setRecordEpisode] = useState(false)
  // Local state/binding `[response, setResponse]` for this fleet UI flow.
  const [response, setResponse] = useState<{
    success: boolean
    message: string
    replan?: boolean
    timestamp: Date
  } | null>(null)
  // Local state/binding `[error, setError]` for this fleet UI flow.
  const [error, setError] = useState<string | null>(null)
  // Local state/binding `telemetryAgentId` for this fleet UI flow.
  const telemetryAgentId = agent.task_server_info
    ? `${agent.task_server_info.host}:${agent.task_server_info.port}`
    : null
  // Hook into live agent telemetry stream (beyond REST CRUD).
  const telemetry = useTelemetryStream(telemetryAgentId)

  /**
   * Component/helper `handleSendTask` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  // Local state/binding `handleSendTask` for this fleet UI flow.
  const handleSendTask = async () => {
    // Conditional branch controlling fleet UI flow or data filtering.
    if (!taskDescription.trim()) {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setError('Please enter a task description')
      return
    }

    // Conditional branch controlling fleet UI flow or data filtering.
    if (!agent.task_server_info?.host || !agent.task_server_info?.port) {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setError('Agent server information not available')
      return
    }

    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsSending(true)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setError(null)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setResponse(null)

    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Local state/binding `host` for this fleet UI flow.
      const host = agent.task_server_info.host === 'host.docker.internal' ? 'localhost' : agent.task_server_info.host
      // Local state/binding `agentUrl` for this fleet UI flow.
      const agentUrl = `http://${host}:${agent.task_server_info.port}/tasks/execute`

      // Local state/binding `taskId` for this fleet UI flow.
      const taskId = crypto.randomUUID()
      // Local state/binding `fullDescription` for this fleet UI flow.
      const fullDescription = taskDescription

      // Local state/binding `res` for this fleet UI flow.
      const res = await fetch(agentUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          description: fullDescription,
          record_episode: recordEpisode,
        }),
      })

      // Conditional branch controlling fleet UI flow or data filtering.
      if (!res.ok) {
        // Abort this path — invalid fleet state or missing required identity.
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }

      // Local state/binding `result` for this fleet UI flow.
      const result = await res.json()

      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setResponse({
        success: result.success,
        message: result.message,
        replan: result.replan,
        timestamp: new Date()
      })

    } catch (err) {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setError(err instanceof Error ? err.message : 'Failed to send task')
    } finally {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setIsSending(false)
    }
  }

  // Reachability/latency map for agent task servers (online/offline telemetry).
  const isReachable = health?.reachable === true

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.8fr] gap-6">
      {/* Left column: task form + response */}
      <div className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center gap-2 px-1">
          {isReachable ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className={cn(
            'text-sm font-medium',
            isReachable ? 'text-emerald-400' : 'text-red-400'
          )}>
            {isReachable ? 'Connected' : 'Disconnected'}
          </span>
          <span className="text-xs text-[var(--color-text-muted)] font-mono ml-auto">
            {agent.task_server_info?.host}:{agent.task_server_info?.port}
          </span>
        </div>

        {/* Task Input */}
        <div>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder="Enter a natural language task description (e.g., 'navigate to the kitchen and pick up the red cup')"
            className="w-full h-28 px-3 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 resize-none text-sm"
            disabled={!isReachable || isSending}
          />

          {error && (
            <div className="mt-2 p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <div className="flex items-center justify-between mt-3">
            <label className="flex items-center gap-2 cursor-pointer select-none group">
              <input
                type="checkbox"
                checked={recordEpisode}
                onChange={(e) => setRecordEpisode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer peer-checked:bg-cyan-500 transition-colors relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-transform peer-checked:after:translate-x-4 after:shadow-sm" />
              <span className="text-sm font-medium text-slate-600 group-hover:text-slate-800">
                Record Episode
              </span>
              <span className="text-xs text-slate-400">(save telemetry to Parquet + blobs)</span>
            </label>
            <Button
              onClick={handleSendTask}
              disabled={!isReachable || isSending || !taskDescription.trim()}
              className="flex items-center gap-2"
            >
              {isSending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              {isSending ? 'Executing...' : 'Send Task'}
            </Button>
          </div>
        </div>

        {/* Execution Status */}
        {isSending && (
          <div className="p-4 rounded-lg border-2 border-amber-500/40 bg-amber-500/5">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
              <span className="text-sm font-medium text-amber-300">Executing Task</span>
            </div>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{taskDescription}</p>
          </div>
        )}

        {/* Response Display */}
        {response && (
          <div className={cn(
            'p-4 rounded-lg border',
            response.success
              ? 'border-emerald-500/30 bg-emerald-500/5'
              : 'border-red-500/30 bg-red-500/5'
          )}>
            <div className="flex items-center gap-2 mb-2">
              {response.success ? (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400" />
              )}
              <span className={cn(
                'text-sm font-medium',
                response.success ? 'text-emerald-300' : 'text-red-300'
              )}>
                {response.success ? 'Task Completed' : 'Task Failed'}
              </span>
              <span className="text-xs text-[var(--color-text-muted)] ml-auto">
                {response.timestamp.toLocaleTimeString()}
              </span>
            </div>
            <pre className={cn(
              'whitespace-pre-wrap font-mono text-xs leading-relaxed mt-2',
              response.success ? 'text-emerald-300/80' : 'text-red-300/80'
            )}>
              {response.message}
            </pre>
            {response.replan && (
              <div className="mt-3 flex items-center gap-2">
                <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-xs font-medium text-amber-300">Replan required</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right column: live telemetry */}
      <div className="space-y-4">
        {/* Telemetry connection indicator */}
        <div className="flex items-center gap-2 text-xs">
          {telemetry.connected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700 font-medium">Telemetry connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400">Telemetry disconnected</span>
            </>
          )}
        </div>

        {/* Video feed — MJPEG stream from telemetry server media plane */}
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
            <Video className="w-4 h-4 text-[var(--color-text-muted)]" />
            <span className="text-sm font-medium text-[var(--color-text-secondary)]">Live Video Feed</span>
            <span className="text-xs text-[var(--color-text-muted)] ml-auto font-mono">MJPEG</span>
          </div>
          {telemetryAgentId ? (
            <div className="aspect-video bg-black flex items-center justify-center">
              <LiveVideoCanvas agentId={telemetryAgentId} className="w-full h-full" />
            </div>
          ) : (
            <div className="aspect-video flex flex-col items-center justify-center text-[var(--color-text-muted)] bg-surface/50">
              <Video className="w-10 h-10 mb-3 opacity-40" />
              <p className="text-sm">No video feed available</p>
            </div>
          )}
        </div>

        {/* Joint states */}
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
            <Activity className="w-4 h-4 text-[var(--color-text-muted)]" />
            <span className="text-sm font-medium text-[var(--color-text-secondary)]">Joint States</span>
          </div>
          <div className="p-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[var(--color-text-muted)] border-b border-slate-200">
                  <th className="text-left pb-2 font-medium">Joint</th>
                  <th className="text-right pb-2 font-medium">Position</th>
                  <th className="text-right pb-2 font-medium">Velocity</th>
                  <th className="text-right pb-2 font-medium">Effort</th>
                </tr>
              </thead>
              <tbody className="text-[var(--color-text)]">
                {telemetry.jointStates.length > 0 ? (
                  telemetry.jointStates.map((joint) => (
                    <tr key={joint.name} className="border-b border-slate-200">
                      <td className="py-1.5 font-mono text-slate-700">{joint.name}</td>
                      <td className="py-1.5 text-right font-mono">{joint.position.toFixed(4)}</td>
                      <td className="py-1.5 text-right font-mono">{joint.velocity.toFixed(4)}</td>
                      <td className="py-1.5 text-right font-mono">{joint.effort.toFixed(4)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-[var(--color-text-muted)]">
                      No joint data received
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Action command log */}
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
            <Terminal className="w-4 h-4 text-[var(--color-text-muted)]" />
            <span className="text-sm font-medium text-[var(--color-text-secondary)]">Action Commands</span>
            {telemetry.actionLog.length > 0 && (
              <span className="text-xs text-[var(--color-text-muted)] ml-auto">{telemetry.actionLog.length} entries</span>
            )}
          </div>
          <div className="max-h-40 overflow-y-auto">
            {telemetry.actionLog.length > 0 ? (
              <div className="divide-y divide-slate-200">
                {telemetry.actionLog.slice(0, 20).map((entry, i) => (
                  <div key={i} className="px-4 py-2 text-xs">
                    <div className="flex items-center gap-2">
                      {entry.attributes?.cmd_type && (
                        <span className="font-mono text-cyan-700 bg-cyan-50 px-1.5 py-0.5 rounded">
                          {entry.attributes.cmd_type}
                        </span>
                      )}
                      <span className="text-[var(--color-text-muted)] font-mono">
                        {entry.signals.map(s => `${s.name}: ${s.values[0]?.toFixed(3)}`).join(', ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-24 flex flex-col items-center justify-center text-[var(--color-text-muted)]">
                <Terminal className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-xs">No commands received</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Register Agent Modal (Simplified)
// =============================================================================

/**
 * Form modal to register a new agent (id, type, task server host/port) into the fleet.
 *
 * @param props.isOpen - Modal visibility.
 * @param props.onClose - Close handler.
 * @param props.onSuccess - Called after successful registration.
 */
function RegisterAgentModal({ 
  isOpen, 
  onClose 
}: { 
  isOpen: boolean
  onClose: () => void
}) {
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [configPath, setConfigPath] = useState('')
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [agentId, setAgentId] = useState('')
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [host, setHost] = useState('localhost')
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [port, setPort] = useState('')
  // TanStack Query client used to invalidate fleet entity caches after mutations.
  const queryClient = useQueryClient()

  // Mutation wrapping a fleet API write (create / allocate / start / delete / copy).
  const mutation = useMutation({
    mutationFn: agentsApi.register,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      queryClient.invalidateQueries({ queryKey: ['agentsHealth'] })
      onClose()
      setConfigPath('')
      setAgentId('')
      setHost('localhost')
      setPort('')
    },
  })

  /**
   * Component/helper `handleSubmit` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  // Local state/binding `handleSubmit` for this fleet UI flow.
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      config_path: configPath,
      agent_id: agentId,
      host: host,
      port: parseInt(port, 10),
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Register Agent">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
            YAML Config Path
          </label>
          <input
            type="text"
            value={configPath}
            onChange={(e) => setConfigPath(e.target.value)}
            placeholder="agents/frontend/rtl/rtl_implementation/config.yaml"
            className="w-full px-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono text-sm"
            required
          />
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Path to the embodiment YAML (relative to project root)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
            Agent ID
          </label>
          <input
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="rtl-dma"
            className="w-full px-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono text-sm"
            required
          />
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Unique identifier for this agent instance
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Host / IP
            </label>
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="localhost"
              className="w-full px-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono text-sm"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Port
            </label>
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="8001"
              min={1}
              max={65535}
              className="w-full px-4 py-2 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono text-sm"
              required
            />
          </div>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] -mt-2">
          For Docker: localhost + exposed port. For real agents: IP + server port.
        </p>

        {mutation.error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{(mutation.error as Error).message}</p>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Registering...' : 'Register Agent'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// =============================================================================
// Main Agents Page
// =============================================================================

/**
 * Main Agents registry page — health grid, detail modal, register/delete agents.
 *
 * Coordinates agentsApi queries, health checks, allocations summary, and
 * telemetry hooks (`useRealtimeUpdates`, `useTelemetryStream`).
 */
export function Agents() {
  // URL search params for deep-linking method modals, tabs, and filters.
  const [searchParams, setSearchParams] = useSearchParams()
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false)
  // Agent id opened in AgentExecutionModal for drill-down telemetry.
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [activeTab, setActiveTab] = useState('overview')
  // Local state/binding `[checkingAgents, setCheckingAgents]` for this fleet UI flow.
  const [checkingAgents, setCheckingAgents] = useState<Set<string>>(new Set())
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isCheckingAll, setIsCheckingAll] = useState(false)
  // Local React UI state for modals, filters, selections, and ephemeral telemetry views.
  const [isRefreshingAll, setIsRefreshingAll] = useState(false)
  // Local state/binding `[refreshMessage, setRefreshMessage]` for this fleet UI flow.
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null)
  // TanStack Query client used to invalidate fleet entity caches after mutations.
  const queryClient = useQueryClient()

  // Enable real-time updates for agent allocations and health
  useRealtimeUpdates()

  // Query fetching fleet entities (plans, tasks, agents, methods, metrics, health).
  const { data: agents = [], isLoading, error } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list()
  })

  // Agent health: event-driven only. Fetched on mount and when WebSocket sends invalidate for 'agent-health'
  // (triggered by telemetry.health_changed from Telemetry when heartbeat changes effective reachable status).
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
    // No refetchInterval — updates only via WebSocket invalidation from Telemetry events
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  })

  // Restore modal state from URL params
  useEffect(() => {
    const robotParam = searchParams.get('agent')
    const tabParam = searchParams.get('tab')

    if (robotParam && agents.length > 0) {
      const agent = agents.find(r => r.agent_id === robotParam)
      if (agent) {
        setSelectedAgent(agent)
        setActiveTab(tabParam || 'overview')
      }
    }
  }, [agents, searchParams])

  // Update URL when modal state changes (but don't clear params that should restore modal)
  useEffect(() => {
    const currentAgentParam = searchParams.get('agent')
    const currentTabParam = searchParams.get('tab')

    if (selectedAgent) {
      // Update URL to match current modal state
      if (currentAgentParam !== selectedAgent.agent_id || currentTabParam !== activeTab) {
        setSearchParams({
          agent: selectedAgent.agent_id,
          tab: activeTab
        })
      }
    }
    // Don't clear URL params here - let them persist for direct links
  }, [selectedAgent, activeTab, searchParams, setSearchParams])

  // Fetch allocations for all agents (don't let this block agents display)
  const { data: robotAllocations = {} } = useQuery({
    queryKey: ['agent-allocations'],
    queryFn: async () => {
      if (agents.length === 0) return {}
      const allocations: Record<string, AgentAllocations> = {}
      for (const agent of agents) {
        try {
          const alloc = await agentsApi.getAllocations(agent.agent_id)
          allocations[agent.agent_id] = alloc
        } catch (error) {
          console.error(`Failed to fetch allocations for ${agent.agent_id}:`, error)
          // If allocation fetch fails, provide default empty allocation
          allocations[agent.agent_id] = {
            agent_id: agent.agent_id,
            plans_count: 0,
            goals_count: 0,
            tasks_count: 0,
            plans: [],
            goals: []
          }
        }
      }
      return allocations
    },
    enabled: agents.length > 0,
    // Don't retry on failure to prevent blocking
    retry: false,
    // Don't refetch on window focus to avoid spam
    refetchOnWindowFocus: false,
  })

  // Debug logging (after both queries are declared)
  console.log('Agents data:', { agents, isLoading, error, robotAllocations })

  // Mutation wrapping a fleet API write (create / allocate / start / delete / copy).
  const deleteMutation = useMutation({
    mutationFn: agentsApi.unregister,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })

  // Check health of a single agent
  /**
   * Component/helper `checkSingleHealth` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const checkSingleHealth = async (agentId: string) => {
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setCheckingAgents(prev => new Set(prev).add(agentId))
    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Optimistic update: assume agent is reachable while checking
      queryClient.setQueryData(['agent-health'], (oldData: any) => ({
        ...oldData,
        [agentId]: { ...oldData?.[agentId], reachable: true, checking: true }
      }))

      // Trigger immediate refetch
      await queryClient.invalidateQueries({ queryKey: ['agent-health'] })
    } catch (error) {
      console.error('Failed to refresh health:', error)
    } finally {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setCheckingAgents(prev => {
        const newSet = new Set(prev)
        newSet.delete(agentId)
        return newSet
      })
    }
  }

  /**
   * Component/helper `checkAllHealth` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const checkAllHealth = async () => {
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsCheckingAll(true)
    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Trigger immediate refetch for all agents
      await queryClient.invalidateQueries({ queryKey: ['agent-health'] })
    } catch (error) {
      console.error('Failed to refresh health:', error)
    } finally {
      // Invoke a setter/helper that advances fleet UI or telemetry state.
      setIsCheckingAll(false)
    }
  }


  // Refresh all agents from YAML
  /**
   * Component/helper `refreshAllFromYaml` used by this fleet dashboard page.
   *
   * @remarks Part of Mission Control for the agent fleet.
   */
  const refreshAllFromYaml = async () => {
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsRefreshingAll(true)
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setRefreshMessage(null)
    // Guard a fleet API / parse operation that may fail at runtime.
    try {
      // Registered fleet agents available for allocation and health display.
      const response = await fetch('/api/agents/refresh/all', { method: 'POST' })
      // Local state/binding `data` for this fleet UI flow.
      const data = await response.json()
      
      // Conditional branch controlling fleet UI flow or data filtering.
      if (response.ok) {
        queryClient.invalidateQueries({ queryKey: ['agents'] })
        // Registered fleet agents available for allocation and health display.
        setRefreshMessage(`✓ Refreshed ${data.success_count}/${data.total} agents from YAML`)
        // Also refresh health after YAML refresh
        setTimeout(checkAllHealth, 500)
      } else {
        // Invoke a setter/helper that advances fleet UI or telemetry state.
        setRefreshMessage(`✗ ${data.detail || 'Failed to refresh'}`)
      }
    } catch (error) {
      // Registered fleet agents available for allocation and health display.
      setRefreshMessage('✗ Failed to refresh agents from YAML')
    }
    // Invoke a setter/helper that advances fleet UI or telemetry state.
    setIsRefreshingAll(false)
    // Clear message after 5 seconds
    setTimeout(() => setRefreshMessage(null), 5000)
  }

  if (isLoading) {
    return <div className="text-[var(--color-text-secondary)]">Loading...</div>
  }

  // Reachability/latency map for agent task servers (online/offline telemetry).
  const connectedCount = Object.values(robotHealth).filter(h => h.reachable).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent Fleet"
        meta={
          <>
            {agents.length} registered · {connectedCount} connected
          </>
        }
        actions={
          <>
            <Button
              variant="secondary"
              onClick={refreshAllFromYaml}
              disabled={isRefreshingAll || agents.length === 0}
              title="Re-read all YAML files and update agent capabilities"
            >
              <Download className={cn('w-4 h-4', isRefreshingAll && 'animate-spin')} />
              {isRefreshingAll ? 'Syncing...' : 'Sync YAMLs'}
            </Button>
            <Button
              variant="secondary"
              onClick={checkAllHealth}
              disabled={isCheckingAll || agents.length === 0}
            >
              <RefreshCw className={cn('w-4 h-4', isCheckingAll && 'animate-spin')} />
              {isCheckingAll ? 'Checking...' : 'Check All'}
            </Button>
            <Button onClick={() => setIsRegisterModalOpen(true)}>
              <Plus className="w-4 h-4" />
              Register Agent
            </Button>
          </>
        }
      />

      {/* Refresh Message */}
      {refreshMessage && (
        <div className={cn(
          'p-3 rounded-xl text-sm ring-1',
          refreshMessage.startsWith('✓') 
            ? 'bg-emerald-50 ring-emerald-200/70 text-emerald-800'
            : 'bg-red-50 ring-red-200/70 text-red-800'
        )}>
          {refreshMessage}
        </div>
      )}

      {/* Agents Grid */}
      {agents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              health={robotHealth[agent.agent_id]}
              allocations={robotAllocations[agent.agent_id]}
              onClick={() => setSelectedAgent(agent)}
              onDelete={(id) => deleteMutation.mutate(id)}
              onCheckHealth={checkSingleHealth}
              isChecking={checkingAgents.has(agent.agent_id)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Bot className="w-8 h-8" />}
          title="No agents registered"
          description="Register your first agent to start building your fleet. You'll need the YAML config path, host/IP, and port."
          action={
            <Button onClick={() => setIsRegisterModalOpen(true)}>
              <Plus className="w-4 h-4" />
              Register Agent
            </Button>
          }
        />
      )}

      {/* Modals */}
      <RegisterAgentModal 
        isOpen={isRegisterModalOpen} 
        onClose={() => setIsRegisterModalOpen(false)} 
      />
      
      <AgentDetailModal
        agent={selectedAgent}
        health={selectedAgent ? robotHealth[selectedAgent.agent_id] : undefined}
        isOpen={!!selectedAgent}
        onClose={() => {
          setSelectedAgent(null)
          setActiveTab('overview')
          // Clear URL params when modal is closed
          setSearchParams({})
        }}
        onRefresh={checkAllHealth}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
    </div>
  )
}
