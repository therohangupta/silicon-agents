# components/

Shared React UI for **Mission Control**. Pages in `src/pages/` compose these building blocks instead of duplicating markup, so cards, modals, navigation, and execution-time panels stay visually and behaviorally consistent across Dashboard, Goals, Plans, and Execution.

## Why this layer exists

Mission Control mixes **slow-changing catalog views** (agents, planners) with **high-churn operational views** (plan execution, live video). Components here split that concern:

- **Layout** — persistent chrome (sidebar, page titles) that does not refetch on every route change.
- **Common** — design tokens applied as Tailwind class recipes (buttons, cards, badges, DAG, video).
- **Modals** — multi-step workflows that are larger than a single `Modal` body slot.
- **Execution** — widgets tuned for the `/plans/:planId/execute` experience (task chips, agent inspector).

None of these modules call REST directly except where a feature modal owns its own queries (see `modals/ManualPlanCreation.tsx`). Prefer `lib/api` from pages or modals; keep presentational components free of `fetch`.

## Subdirectories

| Directory | Mission Control role | API / realtime touchpoints |
|-----------|----------------------|----------------------------|
| `layout/` | Fixed sidebar + main margin; “Agent Fleet / Mission Control” brand | None (localStorage for collapse only) |
| `common/` | Primitives and heavy visualizations | `LiveVideoCanvas` → video WebSocket; `DAGVisualization` → local Graphviz WASM only |
| `modals/` | Operator workflows spanning multiple API calls | `ManualPlanCreation` → `goalsApi`, `agentsApi`, `plansApi.createManual` |
| `execution/` | Live run inspection | `AgentExecutionModal` → `useTelemetryStream` + `LiveVideoCanvas` |

## Composition patterns

### Page shell

Typical page structure:

1. `PageHeader` — gradient title, optional meta count, description, primary actions on the right.
2. Body — `Card` sections, `EmptyState` when lists are empty, tables or grids.
3. Feature `Modal` or route-specific dialog opened from actions.

`Layout` (in `layout/Layout.tsx`) wraps all routes from `App`; it does not include `Header.tsx` (sticky path title bar) — that component is available but unused in the current shell.

### Status and lifecycle

Fleet objects share string statuses (`pending`, `in_progress`, `completed`, `failed`, …). Display components should use:

- `StatusBadge` — pill backed by `getStatusBgColor()` from `lib/utils`.
- Raw text labels — `getStatusColor()` when not using a badge.

Do not hard-code new color mappings in pages if a badge already covers the status family.

### Graphs and live media

| Component | When to use | Data source |
|-----------|-------------|-------------|
| `DAGVisualization` | Server-backed tasks with `dependency_task_ids` | Props only; renders DOT via WASM |
| `LiveVideoCanvas` | Agent camera during execution | WebSocket binary stream |
| Inline Graphviz in `ManualPlanCreation` | Preview while authoring temp-id DAG | Client-side DOT from draft tasks |

Execution modals combine **REST-backed task lists** (from parent page queries) with **push telemetry** (hooks + canvas). Parent pages remain responsible for invalidating `tasks` / `plans` when the global WebSocket fires.

## Import paths

```tsx
import { Card, CardHeader } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { AgentExecutionModal } from '../components/execution/AgentExecutionModal'
```

Equivalent alias form:

```tsx
import { Button } from '@/components/common/Button'
```

Use one style per file; the codebase mixes both today.

## WebSocket usage by folder

```
layout/     (none)
common/     LiveVideoCanvas  →  /ws/video/subscribe/:agentId/:cameraName
execution/  AgentExecutionModal  →  useTelemetryStream + LiveVideoCanvas
modals/     (REST only; Graphviz preview is local)
```

Global TanStack invalidation is **not** implemented in components; it lives in `App` via `useRealtimeUpdates()`.

## Adding a new component

1. Place it under the closest folder (`common` for generic UI, `execution` for run-time-only, `modals` for multi-step dialogs).
2. Keep gateway access in the page or modal container; pass data and callbacks as props.
3. If you need a new WebSocket, add a hook under `hooks/` rather than opening sockets inside leaf components.
4. Extend the subdirectory README with exports, props, and any API or WS contract.

## File index (quick reference)

| Path | Exports |
|------|---------|
| `layout/Layout.tsx` | `Layout` |
| `layout/Sidebar.tsx` | `Sidebar` |
| `layout/PageHeader.tsx` | `PageHeader` |
| `layout/Header.tsx` | `Header` |
| `common/Card.tsx` | `Card`, `CardHeader` |
| `common/Button.tsx` | `Button` |
| `common/Modal.tsx` | `Modal` |
| `common/EmptyState.tsx` | `EmptyState` |
| `common/StatusBadge.tsx` | `StatusBadge` |
| `common/DAGVisualization.tsx` | `DAGVisualization` |
| `common/LiveVideoCanvas.tsx` | `LiveVideoCanvas` |
| `modals/ManualPlanCreation.tsx` | `ManualPlanCreation` |
| `execution/TaskIdChip.tsx` | `TaskIdChip` |
| `execution/AgentExecutionModal.tsx` | `AgentExecutionModal` |

See each subdirectory README for behavior, keyboard shortcuts, and edge cases.
