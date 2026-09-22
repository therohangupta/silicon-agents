# components/common/

Design-system-style **primitives and visualizations** reused across Mission Control pages and modals. These components implement the frosted-card aesthetic (white/90, soft borders, cyan focus rings) defined in `index.css` and Tailwind theme extensions.

They are mostly presentational: props in, JSX out. The exceptions are **`DAGVisualization`** (async WASM load) and **`LiveVideoCanvas`** (video WebSocket + WebCodecs/JPEG decode).

## Mission Control role

| Primitive | Typical surfaces |
|-----------|------------------|
| `Card` / `CardHeader` | Dashboard stat grids, goal tiles, planner cards, modal sections |
| `Button` | Primary CTAs (create goal, start plan), secondary cancel, danger delete |
| `Modal` | Confirm dialogs, agent registration, nested validation in manual plan flow |
| `EmptyState` | Zero agents, zero goals, empty plan list |
| `StatusBadge` | Task/plan/agent status on tables and execution panels |
| `DAGVisualization` | Plan detail task dependency graph |
| `LiveVideoCanvas` | Agent execution modal camera feed |

## File reference

| File | Export(s) | Key props / behavior |
|------|-----------|----------------------|
| `Card.tsx` | `Card`, `CardHeader` | `hover`, `onClick`, optional `label` eyebrow on header |
| `Button.tsx` | `Button` | `variant`: primary \| secondary \| danger \| ghost; `size`: sm \| md \| lg |
| `Modal.tsx` | `Modal` | `isOpen`, `onClose`, `title`, `size` through `wide`; Escape + backdrop close |
| `EmptyState.tsx` | `EmptyState` | `icon`, `title`, `description`, optional `action` |
| `StatusBadge.tsx` | `StatusBadge` | `status` string → `getStatusBgColor()` |
| `DAGVisualization.tsx` | `DAGVisualization` | `tasks[]`, optional `height` (default 600px) |
| `LiveVideoCanvas.tsx` | `LiveVideoCanvas` | `agentId`, `cameraName` (default `front_camera`) |

### `Card` and `CardHeader`

- `Card` applies multi-layer shadow, rounded-xl, optional `card-hover` lift when `hover` is true.
- Clickable cards set pointer cursor; hover border brightens even without `hover` when `onClick` is set.
- `CardHeader` supports uppercase mono `label`, title, subtitle, and right `action` slot.

### `Button`

- Primary: cyan gradient with shadow lift on hover.
- Focus: `focus-visible:ring-2 focus-visible:ring-cyan-500/40`.
- Disabled: opacity 40%, `pointer-events-none`.
- Forwards native `button` attributes (type, onClick, aria-*).

### `Modal`

- When open: `document.body.style.overflow = 'hidden'`, Escape listener on document.
- Backdrop click calls `onClose`; panel click does not propagate (relative panel above absolute backdrop).
- Sizes map to Tailwind max-width utilities; `wide` = `max-w-7xl` for execution inspectors.

### `EmptyState`

- Centered column, icon well on `bg-slate-50`, max-width description for readability.
- `action` is usually a `Button` passed from the parent page.

### `StatusBadge`

- Displays status with underscores replaced by spaces.
- Colors align with fleet lifecycle vocabulary in `lib/utils.getStatusBgColor` (completed emerald, running amber, pending cyan, failed red, cancelled slate).

## `DAGVisualization` — Graphviz WASM

**No REST.** Input is an in-memory `tasks` array (same shape as gateway `Task`: `task_id`, `description`, `status`, `agent_type`, `agent_id`, `dependency_task_ids`).

Pipeline:

1. Lazy `import('@hpcc-js/wasm-graphviz')` — module-level cache so multiple mounts share one WASM instance.
2. `generateDot(tasks)` builds a left-to-right digraph with HTML-like table nodes colored by `task.status`.
3. Renders SVG into a pan/zoom viewport (mouse drag, wheel zoom, touch, keyboard `r` reset, `+`/`-` zoom).
4. On failure, falls back to a textual task list.

Used on plan detail views; manual plan creation embeds its own Graphviz preview logic separately (similar DOT ideas, not this component).

## `LiveVideoCanvas` — video WebSocket

**Separate from telemetry JSON socket.** Opens:

```
/ws/video/subscribe/{agentId}/{cameraName}
```

(on same host as the SPA, `ws` or `wss` from `window.location.protocol`).

| Message type | Handling |
|--------------|----------|
| JSON string | `StreamConfig` with `type: 'config'`, optional `codec` (`h264`, `jpeg`/`jpg`) |
| Binary `ArrayBuffer` | Byte 0 = flags (bit 0 = keyframe); remainder = payload |

Decode paths:

- **JPEG** — Blob → object URL → `Image` → `canvas.drawImage`.
- **H.264** — WebCodecs `VideoDecoder` (`avc1.42E01E`, `optimizeForLatency: true`) when available.

UI shows a small connected/disconnected hint from `ws.onopen` / `onclose` / `onerror`. Cleanup on unmount closes socket and decoder.

Parent components (`AgentExecutionModal`) pass `agentId` as the same telemetry key used elsewhere (`host:port` or agent id).

## API usage

| Component | HTTP |
|-----------|------|
| All except LiveVideoCanvas | None |
| LiveVideoCanvas | None (WS only) |

Vision **images** referenced from telemetry hooks use `/api/telemetry/blob?uri=...` in `useTelemetryStream`, not in `LiveVideoCanvas` (canvas path is streaming video).

## Dependencies

- `cn` from `lib/utils` for class merging.
- Lucide icons only in `Modal` (X close).
- `@hpcc-js/wasm-graphviz` — dynamic import from `DAGVisualization` only.

## Accessibility and UX notes

- Modals trap scroll and support Escape; focus management is minimal (no focus trap library).
- DAG viewer keyboard shortcuts apply when the viewport is focused; may conflict with form fields if focus is not scoped — pages typically embed DAG in dedicated panels.
- Live video requires browser support for WebCodecs for H.264; JPEG path works without WebCodecs.

## Adding a common component

1. Prefer stateless presentation; accept `className` overrides via `cn`.
2. Map statuses through `lib/utils` helpers instead of duplicating switch statements.
3. If networking is required, document the WS/HTTP contract in this README and consider a dedicated hook.
