# src/

Application source for **Agent Fleet Mission Control** — the operator-facing React SPA that monitors agents, goals, plans, and live execution. The UI never talks to the gateway by hostname; it uses same-origin `/api` and `/ws` paths that Vite proxies to `127.0.0.1:8000` in development (see `vite.config.ts` at the package root).

## Mission Control in one pass

Mission Control is the control room for a multi-agent chip-design fleet:

- **Inventory** — register agents, browse embodiments, see allocation summaries.
- **Intent** — create and delete goals that planners turn into task DAGs.
- **Planning** — automated plans (planner + allocator strategies) or operator-authored manual DAGs.
- **Execution** — start allocated plans, watch task progress, open per-agent telemetry (joints, actions, video).
- **Catalog** — read planner and allocator YAML methods (prompts, types, variables).

The visual language is a light “mission shell” (`mission-shell-bg`, frosted cards, cyan/violet accents) with a fixed dark sidebar labeled **Agent Fleet / Mission Control**.

## Bootstrap and shell

| File | Role |
|------|------|
| `main.tsx` | Creates `QueryClient` (`staleTime: 2000`), mounts `QueryClientProvider` + `BrowserRouter`, renders `App`, imports `index.css` |
| `App.tsx` | `useRealtimeUpdates()`, Methods API preload gate, `Layout` + React Router routes |
| `index.css` | Tailwind layers, CSS variables (`--color-bg`, `--color-text`, …), tonal chips, scrollbar, React Flow overrides |
| `types.ts` | Shared domain types: `Agent`, `Goal`, `Plan`, `Task`, create/update request bodies, `PlanStatus` |

Until `methodsApi.list()` finishes (success or failure), `App` shows a full-screen spinner (“Loading method configurations…”). That preload seeds `setMethodData()` so plan and goal screens can resolve numeric strategy ids to human names.

## Directory map

| Directory | Role |
|-----------|------|
| `components/` | Reusable UI: layout chrome, primitives, modals, execution widgets |
| `hooks/` | WebSocket-heavy React hooks (per-agent telemetry) |
| `lib/` | Gateway REST facades, realtime singleton, Tailwind/status helpers |
| `pages/` | Route screens (see `pages/README.md` — owned separately; do not duplicate here) |

## Routing (`App.tsx`)

| Path | Page | Typical data sources |
|------|------|----------------------|
| `/` | Dashboard | Aggregated queries (agents, plans, tasks) |
| `/agents` | Agents | `agentsApi`, `agentTemplatesApi` |
| `/goals` | Goals | `goalsApi`, method name helpers |
| `/plans` | Plans | `plansApi`, `strategiesApi`, manual modal |
| `/plans/:planId` | PlanDetails | `plansApi.get`, `tasksApi`, DAG components |
| `/plans/:planId/execute` | Execution | `plansApi`, live task polling + execution modals |
| `/planners` | Planners | `methodsApi.get(..., 'planner')` |
| `/allocators` | Allocators | `methodsApi.get(..., 'allocator')` |
| `*` | Redirect to `/` | — |

Nested routes (plan id, execute) are not listed in `Header.tsx`’s static title map; those pages use `PageHeader` with their own titles.

## Data flow: REST + cache + push invalidation

```
Browser                    Vite proxy (dev)              Gateway
   |  GET /api/...    -->  :8000/api/...        -->     REST handlers
   |  useQuery cache  <--  JSON bodies          <--
   |
   |  WS /ws/...      -->  ws://:8000/ws/...    -->     global updates + telemetry + video
   |  invalidateQueries on { type: 'invalidate', queries: [...] }
```

1. **Reads and writes** — Pages call TanStack Query with `queryFn` / `mutationFn` pointing at `lib/api` facades (`agentsApi`, `plansApi`, etc.). Each facade wraps a shared `GatewayClient({ baseUrl: '' })` from `@agent-fleet/client-sdk`.

2. **Freshness** — Default `staleTime: 2000` in `main.tsx` limits refetch churn on remounts. Realtime invalidation is the primary “something changed” signal.

3. **Realtime** — `useRealtimeUpdates()` in `App` connects `realtimeManager` (singleton). On `{ type: 'invalidate', queries: ['agents', 'plans', …] }`, it runs `queryClient.invalidateQueries({ queryKey: [key] })` for each string. Ping and connected messages are logged only.

4. **Execution telemetry** — Separate from global invalidation: `useTelemetryStream(agentId)` opens an agent telemetry WebSocket via `connectAgentTelemetry`. `LiveVideoCanvas` opens `/ws/video/subscribe/:agentId/:cameraName` for binary JPEG/H.264 frames.

5. **Blob proxy** — Relative vision URIs and `s3://` refs from telemetry are rewritten to `/api/telemetry/blob?uri=...` so the browser can load images without direct object-store access.

## WebSocket patterns (three channels)

| Channel | Where | Purpose |
|---------|--------|---------|
| Global updates | `lib/api.ts` → `RealtimeManager` | Fleet-wide cache invalidation; one socket per tab |
| Agent telemetry | `hooks/useTelemetryStream.ts` | Joints, vision metadata, action log, discrete events |
| Live video | `components/common/LiveVideoCanvas.tsx` | Binary frames + JSON `config` (codec) |

All three derive `wsBaseUrl` or path from `window.location` (`ws:` / `wss:` + host) so production can sit behind TLS-terminated reverse proxies without code changes.

## Import conventions

- Path alias `@/*` → `src/*` (Vite + TypeScript).
- Pages import components with relative paths (`../components/...`) or `@/components/...`.
- Gateway types for methods can be imported from `lib/api` (`MethodSummary`, `MethodDetail`) to avoid reaching into the SDK from pages.

## Related documentation

| README | Contents |
|--------|----------|
| `components/README.md` | Component tree and when to use each folder |
| `hooks/README.md` | Telemetry hook contract and caps |
| `lib/README.md` | REST surface area and `RealtimeManager` lifecycle |
| `../README.md` | Package scripts, dependencies, proxy table |
| `pages/README.md` | Per-route screen behavior (long-form; maintained separately) |

## Out of scope here

Source comments and deep page walkthroughs for `Agents`, `Plans`, `PlanDetails`, and `Execution` are maintained in the page modules and `pages/README.md` per the package root README.
