/**
 * @file Typed Gateway BFF HTTP client.
 *
 * One method per Gateway REST resource (agents, plans, tasks, goals,
 * agent templates, methods). The dashboard and scripts call this instead of hand-rolling
 * fetch URLs. Realtime updates arrive via `GatewayRealtimeClient`, not here.
 */

import { fetchApi } from './fetchApi'
import type {
  AgentTemplate,
  Goal,
  GoalCreateRequest,
  Plan,
  PlanCreateRequest,
  PlanStatus,
  Agent,
  AgentAllocationsResponse,
  AgentInstanceCreateRequest,
  StrategiesResponse,
  Task,
  ManualPlanCreateRequest,
  MethodSummary,
  MethodDetail,
} from '../models/types'

/** interface `GatewayClientOptions` — Gateway client SDK contract type. */
export interface GatewayClientOptions {
  /** Example: "http://localhost:8000" (no trailing slash). Empty string for same-origin. */
  baseUrl?: string
  /** If provided, sent as Authorization: Bearer <token> */
  bearerToken?: string
}

/** class `GatewayClient` — Gateway client SDK helper; see methods. */
export class GatewayClient {
  private baseUrl: string
  private bearerToken?: string

  constructor(opts?: GatewayClientOptions) {
    this.baseUrl = opts?.baseUrl ?? ''
    this.bearerToken = opts?.bearerToken
  }

  private headers(): Record<string, string> {
    // Return this value to the Gateway client caller.
    return this.bearerToken ? { Authorization: `Bearer ${this.bearerToken}` } : {}
  }

  // Agents
  agents = {
    list: (filter = 'all') => fetchApi<Agent[]>(`/api/agents?filter=${filter}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    get: (agentId: string) => fetchApi<Agent>(`/api/agents/${agentId}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    getAllocations: (agentId: string) =>
      fetchApi<AgentAllocationsResponse>(`/api/agents/${agentId}/allocations`, { baseUrl: this.baseUrl, headers: this.headers() }),
    register: (data: AgentInstanceCreateRequest) =>
      fetchApi<Agent>(`/api/agents/register`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    unregister: (agentId: string) =>
      fetchApi<{ success: boolean }>(`/api/agents/${agentId}`, {
        baseUrl: this.baseUrl,
        method: 'DELETE',
        headers: this.headers(),
      }),
  }

  // Goals
  goals = {
    list: () => fetchApi<Goal[]>(`/api/goals`, { baseUrl: this.baseUrl, headers: this.headers() }),
    get: (goalId: number) => fetchApi<Goal>(`/api/goals/${goalId}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    create: (data: GoalCreateRequest) =>
      fetchApi<Goal>(`/api/goals`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    delete: (goalId: number) =>
      fetchApi<{ success: boolean }>(`/api/goals/${goalId}`, {
        baseUrl: this.baseUrl,
        method: 'DELETE',
        headers: this.headers(),
      }),
  }

  // Plans
  plans = {
    list: () => fetchApi<Plan[]>(`/api/plans`, { baseUrl: this.baseUrl, headers: this.headers() }),
    get: (planId: number) => fetchApi<Plan>(`/api/plans/${planId}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    create: (data: PlanCreateRequest) =>
      fetchApi<Plan>(`/api/plans`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    createManual: (data: ManualPlanCreateRequest) =>
      fetchApi<Plan>(`/api/plans/manual`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    allocate: (planId: number, allocationStrategy: string) =>
      fetchApi<Plan>(`/api/plans/${planId}/allocate`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify({ allocation_strategy: allocationStrategy }),
      }),
    getStatus: (planId: number) => fetchApi<PlanStatus>(`/api/plans/${planId}/status`, { baseUrl: this.baseUrl, headers: this.headers() }),
    start: (planId: number) =>
      fetchApi<{ success: boolean }>(`/api/plans/${planId}/start`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
      }),
    copy: (planId: number, data: { name: string; description: string }) =>
      fetchApi<Plan>(`/api/plans/${planId}/copy`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    update: (planId: number, data: { name: string; description: string }) =>
      fetchApi<Plan>(`/api/plans/${planId}`, {
        baseUrl: this.baseUrl,
        method: 'PUT',
        headers: this.headers(),
        body: JSON.stringify(data),
      }),
    delete: (planId: number) =>
      fetchApi<{ success: boolean }>(`/api/plans/${planId}`, {
        baseUrl: this.baseUrl,
        method: 'DELETE',
        headers: this.headers(),
      }),
  }

  // Tasks
  tasks = {
    list: (params?: { plan_id?: number; goal_id?: number; agent_id?: string }) => {
      /** `searchParams` — Gateway client SDK export. */
      const searchParams = new URLSearchParams()
      // Conditional branch for this Gateway client path.
      if (params?.plan_id) searchParams.set('plan_id', String(params.plan_id))
      // Conditional branch for this Gateway client path.
      if (params?.goal_id) searchParams.set('goal_id', String(params.goal_id))
      // Conditional branch for this Gateway client path.
      if (params?.agent_id) searchParams.set('agent_id', params.agent_id)
      /** `query` — Gateway client SDK export. */
      const query = searchParams.toString()
      // Return this value to the Gateway client caller.
      return fetchApi<Task[]>(`/api/tasks${query ? `?${query}` : ''}`, { baseUrl: this.baseUrl, headers: this.headers() })
    },
    get: (taskId: number) => fetchApi<Task>(`/api/tasks/${taskId}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    create: (data: {
      description: string
      goal_id: number
      plan_id?: number
      agent_id?: string | null
      agent_type?: string | null
      dependency_task_ids?: number[]
    }) =>
      fetchApi<Task>(`/api/tasks`, {
        baseUrl: this.baseUrl,
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify({
          description: data.description,
          goal_id: data.goal_id,
          plan_id: data.plan_id ?? null,
          agent_id: data.agent_id ?? null,
          agent_type: data.agent_type ?? null,
          dependency_task_ids: data.dependency_task_ids ?? [],
        }),
      }),
    update: (
      taskId: number,
      data: {
        description?: string
        goal_id?: number
        agent_id?: string
        update_dependency_task_ids?: boolean
        dependency_task_ids?: number[]
      }
    ) =>
      fetchApi<Task>(`/api/tasks/${taskId}`, {
        baseUrl: this.baseUrl,
        method: 'PATCH',
        headers: this.headers(),
        body: JSON.stringify({
          ...data,
          dependency_task_ids: data.dependency_task_ids ?? [],
          update_dependency_task_ids: data.update_dependency_task_ids ?? false,
        }),
      }),
    delete: (taskId: number) =>
      fetchApi<{ success: boolean; deleted_task_id: number; updated_task_ids: number[] }>(`/api/tasks/${taskId}`, {
        baseUrl: this.baseUrl,
        method: 'DELETE',
        headers: this.headers(),
      }),
  }

  agentTemplates = {
    list: () =>
      fetchApi<AgentTemplate[]>(`/api/agent-templates`, { baseUrl: this.baseUrl, headers: this.headers() }),
    get: (name: string) =>
      fetchApi<AgentTemplate>(`/api/agent-templates/${name}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    suggestPort: (basePort = 8001) =>
      fetchApi<{ suggested_port: number }>(`/api/ports/suggest?base_port=${basePort}`, { baseUrl: this.baseUrl, headers: this.headers() }),
    usedPorts: () => fetchApi<{ used_ports: number[] }>(`/api/ports/used`, { baseUrl: this.baseUrl, headers: this.headers() }),
  }

  strategies = {
    get: () => fetchApi<StrategiesResponse>(`/api/strategies`, { baseUrl: this.baseUrl, headers: this.headers() }),
  }

  methods = {
    list: () => fetchApi<MethodSummary[]>(`/api/methods`, { baseUrl: this.baseUrl, headers: this.headers() }),
    get: (methodId: number, methodType?: 'planner' | 'allocator') => {
      /** `url` — Gateway client SDK export. */
      const url = methodType ? `/api/methods/${methodId}?category=${methodType}` : `/api/methods/${methodId}`
      // Return this value to the Gateway client caller.
      return fetchApi<MethodDetail>(url, { baseUrl: this.baseUrl, headers: this.headers() })
    },
  }
}

