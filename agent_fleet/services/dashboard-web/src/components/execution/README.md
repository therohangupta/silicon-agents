# components/execution/

UI specialized for **plan execution** — the `/plans/:planId/execute` Mission Control view where operators watch tasks move through pending → in progress → completed/failed and drill into per-agent live telemetry.

Parent pages own TanStack Query subscriptions (`tasksApi`, `plansApi`, polling or invalidation from the global WebSocket). This folder renders task-centric affordances and the **agent execution inspector** modal.

## Mission Control context

During execution the operator needs:

- At-a-glance **task identity** (`#42` chips) with dependency context.
- A **single-agent cockpit**: current task, queued tasks blocked on dependencies, completed history, live camera, joint table, rolling action commands.

`AgentExecutionModal` is the main surface; `TaskIdChip` is reused anywhere dense task ids appear (execution tables, dependency rows).

## Files

| File | Export | Purpose |
|------|--------|---------|
| `TaskIdChip.tsx` | `TaskIdChip` | Monospace `#id` with optional hover tooltip |
| `AgentExecutionModal.tsx` | `AgentExecutionModal` | Wide modal: task columns + telemetry column |

## `TaskIdChip`

Props:

| Prop | Type | Default | Meaning |
|------|------|---------|---------|
| `taskId` | `number` | required | Shown as `#${taskId}` |
| `task` | `Task` | optional | Tooltip payload |
| `className` | string | optional | Outer span |
| `colorClass` | string | optional | Override chip colors |
| `showTooltip` | boolean | `true` | Disable hover popup in dense UIs |

Tooltip (when `task` provided and hover enabled):

- Task id + colorized status label
- Full description
- `@agent_id` if assigned, or “Requires: {agent_type}” when typed but unallocated
- Caret pointer anchored above chip

**API / WebSocket:** none — purely presentational.

## `AgentExecutionModal`

Props:

| Prop | Meaning |
|------|---------|
| `isOpen` / `onClose` | Controlled by Execution page |
| `agentId` / `agentType` | Modal title `@id (type)` |
| `tasks` | Subset of plan tasks assigned to this agent |
| `allTasks` | Full plan task list for dependency lookup |
| `elapsedTimes` | `Map<taskId, ms>` for in-progress timer display |
| `taskServerInfo` | Optional `{ host, port }` for telemetry routing |

### Layout (inside `Modal` size `wide`)

Two-column grid on large screens (`lg:grid-cols-[1fr_0.8fr]`), scrollable `max-h-[75vh]`:

**Left — task queue**

- **Current task** — amber bordered card when `status === 'in_progress'`; shows deps as `TaskIdChip` row, elapsed from `elapsedTimes`.
- **Queued** — pending tasks with “Ready” vs “Blocked” from `depsReady()` (all `dependency_task_ids` completed in `taskMap`).
- **Completed / failed** — collapsible result sections (`expandedResults` Set), status icons from Lucide.

**Right — live telemetry**

- Connection badge (`Wifi` / `WifiOff`) from `useTelemetryStream`.
- `LiveVideoCanvas` with telemetry key (see below).
- Joint state table from `telemetry.jointStates`.
- Action log (newest first, capped in hook).
- Optional event log section when events arrive.

### Telemetry key selection

```tsx
const telemetryAgentId = taskServerInfo
  ? `${taskServerInfo.host}:${taskServerInfo.port}`
  : agentId
const telemetry = useTelemetryStream(isOpen ? telemetryAgentId : null)
```

When the gateway exposes a task-server endpoint, telemetry and video subscribe on **`host:port`**; otherwise the registered **agent id** is used. The modal only connects while `isOpen` to avoid idle WebSockets.

### WebSocket patterns (two sockets when open)

| Stream | Module | URL / API |
|--------|--------|-----------|
| Telemetry JSON | `hooks/useTelemetryStream` | SDK `connectAgentTelemetry(id, handlers, wsBaseUrl)` |
| Video binary | `LiveVideoCanvas` | `/ws/video/subscribe/{id}/{cameraName}` |

Both use same-origin `ws://host` or `wss://host`. Vision snapshot URIs inside telemetry may still be proxied via `/api/telemetry/blob?uri=...` in the hook (static frames), while the canvas shows the live video pipe.

### REST

This modal does **not** fetch tasks; the Execution page passes props from existing queries. Starting/stopping plans remains on the page via `plansApi`.

## Integration checklist for pages

1. Keep `tasks` and `allTasks` in sync with query cache; rely on `useRealtimeUpdates` invalidating `tasks` / `plans` keys when the gateway broadcasts changes.
2. Pass `taskServerInfo` when the plan payload includes per-agent task server endpoints.
3. Open modal with `isOpen` true only for one agent at a time if bandwidth is a concern (each open modal = up to 2 WebSockets).

## Status icon map

`AgentExecutionModal` maps task status to Lucide icons:

- `completed` → green CheckCircle
- `in_progress` → amber Clock (pulse)
- `failed` → red AlertCircle
- `pending` → muted Circle

Aligns with `StatusBadge` vocabulary but uses icons for scanability in dense lists.

## Related docs

- `hooks/README.md` — telemetry event types, log caps, blob URI rewriting
- `components/common/README.md` — `LiveVideoCanvas` frame format and codecs
- `pages/README.md` — Execution route orchestration (maintained separately)
