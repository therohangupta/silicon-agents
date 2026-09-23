/**
 * @fileoverview Shared TypeScript domain types for the Mission Control dashboard.
 *
 * These interfaces mirror gateway / protobuf JSON shapes returned by
 * `@agent-fleet/client-sdk` wrappers in `lib/api.ts`. Pages and components import
 * from here instead of re-declaring ad-hoc shapes so status unions stay consistent.
 */

// =============================================================================
// API Types — core fleet entities returned by list/get endpoints
// =============================================================================

/**
 * Lifecycle status of a single task within a plan DAG.
 * `unknown` covers legacy / unset values from older server payloads.
 */
export type TaskStatus = 'unknown' | 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'failed'

/**
 * Deployment / runtime state of a registered agent process or container.
 */
export type AgentState = 'unknown' | 'registered' | 'deploying' | 'running' | 'error' | 'stopped'

/**
 * Network endpoint where an agent's task-execution gRPC/HTTP server listens.
 */
export interface TaskServerInfo {
  /** Hostname or IP reachable from the gateway (often Docker host or localhost). */
  host: string
  /** TCP port of the agent task server. */
  port: number
}

/**
 * Optional Docker / runtime metadata when an agent is containerized.
 */
export interface ContainerInfo {
  /** Docker container id when known. */
  container_id?: string
  /** Image reference used to launch the container. */
  image?: string
  /** Published host for the container network. */
  host?: string
  /** Published host port. */
  port?: number
}

/**
 * Nested status object sometimes returned alongside Agent records.
 * (Distinct from the flatter `Agent.status` AgentState field used in list views.)
 */
export interface AgentStatus {
  /** Coarse agent lifecycle state. */
  state: AgentState
  /** Human-readable status detail from the agent or orchestrator. */
  message?: string
}

/**
 * Registered agent (robot / worker) available for task allocation.
 */
export interface Agent {
  /** Unique agent identifier used in allocations and telemetry keys. */
  agent_id: string
  /** Agent type label from registration (matches a catalog template name). */
  agent_type: string
  /** Optional free-text description from the agent config. */
  description?: string
  /** Capability tags used by allocators for matching. */
  capabilities: string[]
  /** Current lifecycle state when provided by the gateway. */
  status?: AgentState
  /** Where the task server is reachable. */
  task_server_info?: TaskServerInfo
  /** Container metadata when the agent runs in Docker. */
  container?: ContainerInfo
  /** Task ids currently or historically associated with this agent. */
  task_ids: number[]
}

/**
 * High-level objective that planners decompose into tasks.
 */
export interface Goal {
  /** Stable numeric id assigned by the gateway. */
  goal_id: number
  /** Natural-language description of the desired outcome. */
  description: string
  /** Task ids linked to this goal (may be empty until planning runs). */
  task_ids: number[]
}

/**
 * Atomic unit of work in a plan DAG.
 */
export interface Task {
  /** Stable numeric task id. */
  task_id: number
  /** What the assigned agent should do. */
  description: string
  /** Owning goal when set. */
  goal_id?: number
  /** Owning plan when set. */
  plan_id?: number
  /** Allocated agent id; absent means unallocated. */
  agent_id?: string
  /** Required agent type / capability hint for allocation. */
  agent_type?: string
  /** Upstream task ids that must complete before this task can run. */
  dependency_task_ids: number[]
  /** Current execution status. */
  status: TaskStatus
  /** Optional textual / JSON result payload after completion or failure. */
  result?: string
}

/**
 * Planned DAG binding goals, strategies, tasks, and optional artifacts.
 */
export interface Plan {
  /** Stable numeric plan id. */
  plan_id: number
  /** Operator-facing title. */
  name: string
  /** Longer description of intent / scope. */
  description: string
  /** Numeric planning strategy / method id (proto enum or method catalog id). */
  planning_strategy: number
  /** Numeric allocation strategy / method id. */
  allocation_strategy: number
  /** Task ids belonging to this plan. */
  task_ids: number[]
  /** Goal ids this plan was created to satisfy. */
  goal_ids: number[]
  /** Optional embedded task objects (detail endpoints may hydrate these). */
  tasks?: Task[]
  /** Captured planner prompt transcripts keyed by stage name. */
  planning_prompts?: Record<string, string>
  /** Captured allocator prompt transcripts keyed by stage name. */
  allocation_prompts?: Record<string, string>
  /** Opaque planner artifacts (intermediate structures, LLM JSON, etc.). */
  planning_artifacts?: Record<string, any>
  /** Opaque allocator artifacts including final_allocation allocations. */
  allocation_artifacts?: Record<string, any>
  /** Optional aggregated server logs from planning / allocation. */
  server_logs?: string
  /** Optional serialized DAG structure for visualization helpers. */
  dag_structure?: Record<string, any>
  /** ISO timestamp when the plan was created, if provided. */
  created_at?: string
  /** Coarse execution lifecycle: not_executed | executing | completed | … */
  execution_status?: string
}

/**
 * Agent type template used when registering new agent instances.
 */
export interface AgentTemplate {
  /** Template name / key. */
  name: string
  /** Human description of the template. */
  description: string
  /** Default capability list for agents spawned from this template. */
  capabilities: string[]
  /** Suggested starting port for the task server. */
  default_port: number
  /** Path to the agent config on the server filesystem. */
  config_path: string
  /** Docker image used when launching containerized agents. */
  container_image: string
}

/**
 * UI option for a planning or allocation strategy dropdown.
 */
export interface Strategy {
  /** Machine value sent to the API. */
  value: string
  /** Short label shown in selects. */
  label: string
  /** Longer help text for operators. */
  description: string
}

/**
 * Combined strategies payload from the Strategies API.
 */
export interface StrategiesResponse {
  /** Available planning strategies. */
  planning: Strategy[]
  /** Available allocation strategies. */
  allocation: Strategy[]
}

// =============================================================================
// Request Types — bodies posted/patched to the gateway
// =============================================================================

/**
 * Payload to register a concrete agent instance from a template config.
 */
export interface AgentInstanceCreateRequest {
  /** Server-side path to the agent config file. */
  config_path: string
  /** Desired unique agent id. */
  agent_id: string
  /** Host where the agent task server will listen. */
  host: string
  /** Port where the agent task server will listen. */
  port: number
}

/**
 * Payload to create a new goal.
 */
export interface GoalCreateRequest {
  /** Natural-language goal description. */
  description: string
}

/**
 * Payload to create a plan via automated planning + allocation strategies.
 */
export interface PlanCreateRequest {
  /** Planning method / strategy id. */
  planning_strategy: number
  /** Allocation method / strategy id. */
  allocation_strategy: number
  /** Goals to plan for. */
  goal_ids: number[]
  /** Plan display name. */
  name: string
  /** Plan description. */
  description: string
}

// Manual plan creation — operator-authored DAG without invoking a planner.

/**
 * Client-side task draft used by ManualPlanCreation before ids are persisted.
 */
export interface ManualTaskDefinition {
  /** Temporary ID for referencing (e.g., "t1", "t2") among depends_on edges. */
  temp_id: string
  /** Task description text. */
  description: string
  /** Assigned agent (optional) before server allocation. */
  agent_id?: string
  /** Required capability type (optional). */
  agent_type?: string
  /** List of temp_ids this task depends on. */
  depends_on: string[]
  /** Link to a goal (optional but enforced by the manual-create UI). */
  goal_id?: number
}

/**
 * Payload for `plansApi.createManual`.
 */
export interface ManualPlanCreateRequest {
  /** Plan display name. */
  name: string
  /** Plan description. */
  description: string
  /** Manually authored tasks with temp ids and dependency edges. */
  tasks: ManualTaskDefinition[]
  // goal_ids: number[]  // historically commented — goals inferred from task.goal_id
}

// Plan allocation status — whether tasks have agents before Execute is safe.

/**
 * Discrete allocation completeness for a plan.
 */
export type PlanAllocationStatus = 'empty' | 'unallocated' | 'partially_allocated' | 'fully_allocated'

/**
 * Snapshot returned by `plansApi.getStatus` to gate execution readiness.
 */
export interface PlanStatus {
  /** Plan being queried. */
  plan_id: number
  /** Allocation completeness enum. */
  status: PlanAllocationStatus
  /** Total tasks in the plan. */
  total_tasks: number
  /** How many tasks already have an agent_id. */
  allocated_tasks: number
  /** Task ids still missing an agent. */
  unallocated_task_ids: number[]
  /** True when the gateway considers the plan safe to start. */
  is_executable: boolean
}
