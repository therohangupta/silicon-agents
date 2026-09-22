# Dashboard pages (`src/pages`)

This directory contains the **Mission Control** React route pages for the agent fleet dashboard (`dashboard-web`). Each file is a top-level screen wired in `App.tsx` via React Router. Together they cover the fleet lifecycle:

**Goals → Plans (planner) → Allocation (allocator + agents) → Execution (tasks + telemetry)**

| Page file | Route | Primary fleet concepts |
| --- | --- | --- |
| `Dashboard.tsx` | `/` | Fleet overview: agent/goal/plan/task counts, recent tasks |
| `Goals.tsx` | `/goals` | High-level objectives that planners decompose |
| `Plans.tsx` | `/plans` | Plan list, create, allocate, launch |
| `PlanDetails.tsx` | `/plans/:planId` | Single-plan deep dive (tasks, DAG, artifacts) |
| `Execution.tsx` | `/plans/:planId/execute` | Live/historical plan run telemetry |
| `Agents.tsx` | `/agents` | Agent registry, health, config, ad-hoc tasks |
| `Planners.tsx` | `/planners` | Planner method catalog + YAML detail modal |
| `Allocators.tsx` | `/allocators` | Allocator method catalog (reuses planner modal) |

Shared building blocks live under `../components`, HTTP/WebSocket helpers under `../lib/api`, and domain types under `../types`.

---

## Fleet vocabulary (used across these pages)

- **Goal** — Operator objective (natural-language description). Planners turn goals into task DAGs.
- **Plan** — Scheduled unit of multi-agent work: bound goals, planning strategy, allocation strategy, task ids, execution status.
- **Task** — DAG node with description, optional `agent_id`, `dependency_task_ids`, and lifecycle status (`pending`, `in_progress`, `completed`, `failed`, …).
- **Agent** — Registered worker with `agent_type`, capabilities, and a task-server `host:port`. Allocators assign tasks to agents.
- **Planner / Allocator (methods)** — YAML-defined strategies (`methodsApi`) that produce plans or assign agents. Surfaced as numeric strategy ids on plans and human names via `getPlanningStrategyName` / `getAllocationStrategyName`.
- **Execution / telemetry** — Runtime view of a plan: WebSocket `tasks_update`, elapsed timers, Event Log, metrics, and optional live video streams.

---

## `Dashboard.tsx` — Mission Control home

**Export:** `Dashboard`  
**Route:** `/`

Landing overview for operators. Subscribes to `useRealtimeUpdates()`, then loads agents, agent health (`/api/agents/health/all`), goals, plans, and tasks via React Query.

**UI regions:**

- **Stat cards** (`StatCard`) — Active (reachable) agents, goal count, plan count, completed-task count. Click-through navigates to `/agents`, `/goals`, or `/plans`.
- **Recent Activity** (`RecentActivity`) — Up to 50 newest tasks with plan id chips, agent assignment (or “Unallocated”), and status badges. Clicking a task opens `/plans/:planId?tab=tasks` when the plan exists.

This page does not create or mutate fleet entities; it is a read-only status board.

---

## `Goals.tsx` — Goal registry

**Exports:** `Goals` (page), plus helpers `GoalDetailsModal`, `CreateGoalModal`  
**Route:** `/goals`

Manages the top of the fleet funnel: create/search/sort/delete goals and inspect how each goal fans out into plans and agents.

**Main page (`Goals`):**

- Lists goals with search and sort controls.
- Shows per-goal derived counts: how many plans include the goal, how many distinct agents appear on those plans’ tasks.
- Opens `CreateGoalModal` for new goals (`goalsApi` mutation + query invalidation).
- Opens `GoalDetailsModal` for deep inspection.

**`GoalDetailsModal` tabs:**

- **Overview** — Goal description and aggregate stats (plans generated, tasks created, agents assigned).
- **Plans** — Cards for plans whose `goal_ids` include this goal, with execution status, strategy tags, and counts; opens plan details in a new tab.
- **Agents** — Agents discovered via plan `allocation_artifacts`, with live health (`useRealtimeUpdates` + health query) and capability chips; deep-links to `/agents?agent=…`.

**`CreateGoalModal`:** Simple description form that posts a new goal into the fleet goal store.

---

## `Plans.tsx` — Plan list & lifecycle actions

**Exports:** `Plans`, `CreatePlanForm`, `AllocatePlanForm`, `MethodSelectionCard`  
**Route:** `/plans`

Central operator console for **plans**. Heavily commented for contributors; behavior includes:

- Realtime subscription (`useRealtimeUpdates`) and local `planStatuses` bookkeeping.
- Search, status filter (`unallocated` / `allocated` / `executing` / `completed` / `failed`), and sort.
- **Create plan** modal using planner `MethodSelectionCard`s + goals (`CreatePlanForm`), or **ManualPlanCreation** for hand-authored DAGs.
- **Allocate** modal (`AllocatePlanForm`) to run an allocator method against an unallocated plan.
- Per-plan actions: open details, start/monitor execution, copy, delete, retry patterns.
- URL deep-link `?method=&method_type=` opens `MethodDetailModal` (imported from `Planners.tsx`) for YAML introspection of the planner/allocator used by a plan.

Plans are the bridge between goals and executable tasks: after planning and allocation, operators move to `PlanDetails` or `Execution`.

---

## `PlanDetails.tsx` — Single-plan workspace

**Default export:** `PlanDetails`  
**Also defines:** `normalizeTaskStatus`, `VerticalTaskList`, `MethodSelectionCard`, `AllocatePlanForm`  
**Route:** `/plans/:planId`

Deep inspection and pre-execution editing for one plan.

**Capabilities (by tab / region):**

- **Overview** — Plan metadata (name, description, strategies, goal bindings), edit-in-place when allowed, allocate CTA when unallocated, navigate to Execution Monitor.
- **Tasks** — `VerticalTaskList` (status chips, agent assignment, dependency chips, edit/delete) or `DAGVisualization`. Task mutations gated by `canEdit` (blocked once execution has started).
- **Prompts / Artifacts** — Planning vs allocation prompt text and server-side artifacts for auditability of how the plan was produced/assigned.
- **Goals** — Goals attached to this plan.
- **Exports** — Graphviz / zip-style downloads of plan structure for offline review (`JSZip`, dynamic Graphviz).
- **Allocation modal** — Local `AllocatePlanForm` / `MethodSelectionCard` (inlined to avoid circular imports with `Plans.tsx`).
- **Method modal** — `MethodDetailModal` via search params for strategy YAML.

`normalizeTaskStatus` canonicalizes heterogeneous status strings to fleet snake_case for consistent badges.

---

## `Execution.tsx` — Execution Monitor

**Export:** `Execution`  
**Helpers:** `formatElapsed`, `formatTimestamp`, `parsePersistedEventLog`, `buildEventLogFromMetrics`, `getExpandedEventMessage`  
**Types:** `LogEntry`, `MetricRow`  
**Route:** `/plans/:planId/execute`

Runtime (and historical) telemetry for one plan’s task DAG.

**Modes:**

1. **Preview** — Plan not started; operator reviews the queue and clicks **Start Execution** (`plansApi.start`).
2. **Live** — `GatewayRealtimeClient.connectPlanExecution` streams `tasks_update`; status diffs append to the Event Log; 1s timer updates per-task and wall-clock elapsed times.
3. **Historical** — For completed/failed plans, Event Log is seeded from `metricsApi` rows and/or filtered `plan.server_logs` lifecycle lines.

**UI panels (accordion sections):**

- Progress strip (completed / executing / failed / cancelled segments).
- **Agent Fleet** table — per-agent current task, elapsed, progress, status; row click opens `AgentExecutionModal`.
- **Task Queue** — pending tasks sorted by dependency readiness (`depsReady`).
- **Completed & Failed Tasks** — terminal tasks with expandable `result` payloads.
- **Task Dependencies** — `DAGVisualization`.
- **Event Log** — newest-first lifecycle messages with expand/collapse for long results.
- **Copy & Retry** — on overall failure, copies the plan and navigates to the new plan’s execute route.

---

## `Agents.tsx` — Agent registry & ops

**Export:** `Agents`  
**Supporting UI:** `InfoCard`, `AgentCard`, `ConfigSection`, `ConfigurationViewer`, `TabNavigation`, `OverviewTab`, `AllocationsTab`, `CapabilitiesTab`, `ConfigurationTab`, `AgentDetailModal`, `SendTaskTab`, `RegisterAgentModal`  
**Types:** `AgentHealth`, `AgentYamlDetails`, `AgentAllocations`  
**Route:** `/agents`

Operator console for the fleet’s workers.

**Main grid:** `AgentCard`s showing online/offline health (latency), allocation count pills (plans/goals/tasks), task-server endpoint, refresh-health and delete actions.

**Detail modal tabs:**

- **Overview** — Identity and reachability tiles (`InfoCard`).
- **Allocations** — Which plans/goals/tasks currently assign work to this agent.
- **Capabilities** — Capability tags used during allocation matching.
- **Configuration** — YAML loaded from the fleet server, sectioned by `ConfigurationViewer`.
- **Send Task** — Ad-hoc task dispatch to the agent’s task server (bypasses full plan flow; useful for debugging).
- Live **video / telemetry** via `useTelemetryStream` + `LiveVideoCanvas` when the agent exposes a stream.

**RegisterAgentModal** adds a new agent (id, type, host/port) to the registry. Deep-link `?agent=` can open a specific agent’s modal.

---

## `Planners.tsx` — Planner method catalog

**Exports:** `Planners`, **`MethodDetailModal`** (shared), `MethodCard`, `getPlannerColors`  
**Route:** `/planners`

Catalog of **planner** methods (`methodsApi.list` filtered to `category === 'planner'`).

- Search, method-type filter chips (foundation model / hybrid / algorithmic / …), and sort.
- Grid of `MethodCard`s; click navigates to `/planners?method=:id` and opens **`MethodDetailModal`**.
- **`MethodDetailModal`** (also imported by Plans, PlanDetails, Allocators) loads one method’s YAML-backed fields: description, system/user prompts, output format / examples, example behavior, and template variables.

Planners answer: *how should goals become an ordered task DAG?*

---

## `Allocators.tsx` — Allocator method catalog

**Export:** `Allocators`  
**Route:** `/allocators`

Same UX pattern as Planners, but filtered to `category === 'allocator'`. Reuses `MethodDetailModal` from `Planners.tsx` with `methodType="allocator"`.

Allocators answer: *which agent should run each task?* (LLM reasoning, hybrid, or mathematical optimization — explained in the page info banner).

---

## Navigation map

```
/ (Dashboard)
├── /goals                  → GoalDetailsModal / CreateGoalModal
├── /plans                  → create / allocate modals → MethodDetailModal
│   ├── /plans/:planId      → PlanDetails (tasks, DAG, artifacts, allocate)
│   └── /plans/:planId/execute → Execution Monitor (live telemetry)
├── /agents                 → AgentDetailModal (health, config, send task, video)
├── /planners               → MethodDetailModal (planner YAML)
└── /allocators             → MethodDetailModal (allocator YAML)
```

---

## Documentation notes

- `Plans.tsx`, `PlanDetails.tsx`, `Agents.tsx`, and `Execution.tsx` carry file-level `@fileoverview` JSDoc, per-symbol JSDoc, statement-level `//` comments, and `{/* */}` region comments explaining fleet concepts for onboarding.
- `Dashboard.tsx`, `Goals.tsx`, `Planners.tsx`, and `Allocators.tsx` are described here for completeness but were not part of that inline-comment pass.
- Do not edit `node_modules` or build `dist` output when documenting these pages.
