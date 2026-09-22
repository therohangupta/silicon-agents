# client_sdk/typescript/

TypeScript package **`@agent-fleet/client-sdk`** consumed by **`dashboard-web`**
and any other frontend tooling in the monorepo.

## Purpose

Provides typed Gateway REST access, WebSocket realtime subscriptions, and browser
telemetry viewing helpers. The dashboard links this package with a **`file:`**
dependency in `package.json` so SDK changes ship atomically with UI changes.

This package does **not** run in agent containers or fleet_server — browsers and
Node-based frontend tooling only.

## File inventory

| Path | Role |
|------|------|
| `package.json` | Name, ESM entry, exports map |
| `README.md` | you are here |
| `src/index.ts` | Public barrel re-exports |
| `src/http/` | REST transport — see `src/http/README.md` |
| `src/models/` | JSON types — see `src/models/README.md` |
| `src/realtime/` | WS + telemetry — see `src/realtime/README.md` |

## package.json summary

| Field | Value |
|-------|--------|
| `name` | `@agent-fleet/client-sdk` |
| `type` | `module` |
| `main` / `exports` | `./src/index.ts` (Vite/tsconfig resolves TS directly) |
| `private` | `true` |

No npm publish step in typical dev — monorepo `file:` link only.

## Public exports (index.ts)

Re-exports:

- `./models/types`
- `./http/gatewayClient` (+ `fetchApi` via gateway module imports)
- `./realtime/events`
- `./realtime/wsClient`
- `./realtime/telemetryClient`

Dashboard code should import from `@agent-fleet/client-sdk` root, not deep paths,
so refactors stay centralized.

## Configuration patterns

```typescript
import { GatewayClient, GatewayRealtimeClient } from '@agent-fleet/client-sdk'

const http = new GatewayClient({
  baseUrl: import.meta.env.VITE_GATEWAY_URL ?? '',
  bearerToken: token,
})

const realtime = new GatewayRealtimeClient({
  wsBaseUrl: import.meta.env.VITE_GATEWAY_WS_URL ?? '',
})
```

Empty `baseUrl` / `wsBaseUrl` use same-origin relative URLs in production builds
behind the Gateway reverse proxy.

## Data flows

### REST (React Query)

```
Component → gatewayClient.plans.list()
    → fetchApi GET /api/plans
    → Gateway → fleet gRPC
    → JSON → cache key ['plans']
```

### Realtime invalidation

```
WebSocket message { type: 'invalidate', queries: [...] }
    → GatewayRealtimeClient handler
    → queryClient.invalidateQueries
```

### Plan execution view

```
connectPlanExecution(planId, handler)
    → /ws/execution/{planId}
    → tasks_update merges into local state or invalidates task queries
```

## How Gateway, fleet, and agents relate

| Layer | Interaction |
|-------|-------------|
| **dashboard-web** | Primary consumer of this package |
| **Gateway** | Implements REST/WS contract |
| **fleet_server** | Backend for mutating routes |
| **Agents** | Visible via Gateway agent/plan/task APIs; no direct SDK call |

Agent telemetry **viewing** may use `telemetryClient`; agent **publishing** uses
Python gRPC in `agent_sdk`.

## Related documentation

- `../README.md` — bilingual SDK overview
- `src/README.md` — module map
- `../contract/README.md` — WebSocket JSON Schema
- `../../proto/README.md` — backend wire types (for debugging only)

## Reading order

1. **`src/index.ts`** — export surface.
2. **`src/http/gatewayClient.ts`** — REST coverage.
3. **`src/realtime/wsClient.ts`** — WS URLs.
4. **`src/models/types.ts`** — DTO shapes used in UI.
5. Dashboard hooks/components — integration patterns.

## Parity with Python SDK

TypeScript client is richer (agents, goals, world, methods). When adding REST
methods here, consider mirroring in `python/src/http/client.py` for operator
scripts — track gaps in Python README.
