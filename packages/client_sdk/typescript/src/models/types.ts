/**
 * @file Shared TypeScript types mirroring Gateway JSON payloads.
 *
 * These interfaces document the HTTP/JSON contract between the BFF and
 * browser/CLI clients. Keep them aligned with Gateway OpenAPI responses.
 */

// Shared types for any TypeScript client (web/mobile/node).

/** type `TaskStatus` — Gateway client SDK contract type. */
export type TaskStatus = 'unknown' | 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'failed'
/** type `AgentState` — Gateway client SDK contract type. */
export type AgentState = 'unknown' | 'registered' | 'deploying' | 'running' | 'error' | 'stopped'

/** interface `TaskServerInfo` — Gateway client SDK contract type. */
export interface TaskServerInfo {
  host: string
  port: number
}

/** interface `ContainerInfo` — Gateway client SDK contract type. */
export interface ContainerInfo {
  container_id?: string
  image?: string
  host?: string
  port?: number
}

/** interface `Agent` — Gateway client SDK contract type. */
export interface Agent {
  agent_id: string
  agent_type: string
  description?: string
  capabilities: string[]
  status?: AgentState
  task_server_info?: TaskServerInfo
  container?: ContainerInfo
  task_ids: number[]
}

/** type `PlanExecutionStatus` — Gateway client SDK contract type. */
export type PlanExecutionStatus = 'not_executed' | 'executing' | 'completed' | 'failed'

/** interface `AgentAllocationsPlanSummary` — Gateway client SDK contract type. */
export interface AgentAllocationsPlanSummary {
  plan_id: number
  goal_ids: number[]
  task_count: number
  status: PlanExecutionStatus
  name: string
  description: string
}

/** interface `AgentAllocationsResponse` — Gateway client SDK contract type. */
export interface AgentAllocationsResponse {
  agent_id: string
  plans_count: number
  goals_count: number
  tasks_count: number
  plans: AgentAllocationsPlanSummary[]
  goals: number[]
}

/** interface `Goal` — Gateway client SDK contract type. */
export interface Goal {
  goal_id: number
  description: string
  task_ids: number[]
}

/** interface `Task` — Gateway client SDK contract type. */
export interface Task {
  task_id: number
  description: string
  goal_id?: number
  plan_id?: number
  agent_id?: string
  agent_type?: string
  dependency_task_ids: number[]
  status: TaskStatus
  result?: string | null
}

/** interface `Plan` — Gateway client SDK contract type. */
export interface Plan {
  plan_id: number
  name: string
  description: string
  planning_strategy: number
  allocation_strategy: number
  task_ids: number[]
  goal_ids: number[]
  tasks?: Task[]
  planning_prompts?: Record<string, string>
  allocation_prompts?: Record<string, string>
  planning_artifacts?: Record<string, any>
  allocation_artifacts?: Record<string, any>
  server_logs?: string
  dag_structure?: Record<string, any>
  created_at?: string
  execution_status?: string
}

/** interface `Embodiment` — Gateway client SDK contract type. */
export interface Embodiment {
  name: string
  description: string
  capabilities: string[]
  default_port: number
  config_path: string
  container_image: string
}

/** interface `Strategy` — Gateway client SDK contract type. */
export interface Strategy {
  value: string
  id: number
  label: string
  description: string
}

/** interface `StrategiesResponse` — Gateway client SDK contract type. */
export interface StrategiesResponse {
  planning: Strategy[]
  allocation: Strategy[]
}

// Methods (planners/allocators) metadata
/** interface `MethodSummary` — Gateway client SDK contract type. */
export interface MethodSummary {
  category: string
  type: string
  id?: number
  name: string
  description: string
  method_type: string
  output_format?: string
  example_output?: string
  example_behavior?: string
  prompts: Array<{
    type: string
    description: string
  }>
}

/** interface `MethodDetail` — Gateway client SDK contract type. */
export interface MethodDetail extends MethodSummary {
  system_prompt: string
  user_prompt: string
  variables: string[]
}

/** interface `AgentInstanceCreateRequest` — Gateway client SDK contract type. */
export interface AgentInstanceCreateRequest {
  config_path: string
  agent_id: string
  host: string
  port: number
}

/** interface `GoalCreateRequest` — Gateway client SDK contract type. */
export interface GoalCreateRequest {
  description: string
}

/** interface `PlanCreateRequest` — Gateway client SDK contract type. */
export interface PlanCreateRequest {
  planning_strategy: number
  allocation_strategy: number
  goal_ids: number[]
  name: string
  description: string
}

/** interface `ManualTaskDefinition` — Gateway client SDK contract type. */
export interface ManualTaskDefinition {
  temp_id: string
  description: string
  agent_id?: string
  agent_type?: string
  depends_on: string[]
  goal_id?: number
}

/** interface `ManualPlanCreateRequest` — Gateway client SDK contract type. */
export interface ManualPlanCreateRequest {
  name: string
  description: string
  tasks: ManualTaskDefinition[]
}

/** type `PlanAllocationStatus` — Gateway client SDK contract type. */
export type PlanAllocationStatus = 'empty' | 'unallocated' | 'partially_allocated' | 'fully_allocated'

/** interface `PlanStatus` — Gateway client SDK contract type. */
export interface PlanStatus {
  plan_id: number
  status: PlanAllocationStatus
  total_tasks: number
  allocated_tasks: number
  unallocated_task_ids: number[]
  is_executable: boolean
}

