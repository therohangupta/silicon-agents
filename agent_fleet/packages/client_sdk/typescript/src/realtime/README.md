# client_sdk/typescript/src/realtime/

Gateway **WebSocket clients** and **browser telemetry viewing** helpers.

## Purpose

REST caches go stale when fleet state changes. The Gateway pushes lightweight
events so the dashboard refetches or patches local state. This directory holds:

- Typed **event unions** (`events.ts`)
- **WebSocket connectors** (`wsClient.ts`)
- **Telemetry stream helper** (`telemetryClient.ts`) for live panels

Agent-side telemetry **publish** uses gRPC/protobuf in `agent_sdk` — not this module.

## File inventory

| File | Exports | Role |
|------|---------|------|
| `events.ts` | `GatewayRealtimeMessage`, per-type interfaces | WS JSON discriminant union |
| `wsClient.ts` | `GatewayRealtimeClient` | `connectGlobalUpdates`, `connectPlanExecution` |
| `telemetryClient.ts` | Telemetry viewer helpers | Dashboard live charts / streams |
| `README.md` | — | you are here |

## events.ts

Discriminated union on **`type`**:

| `type` | Meaning |
|--------|---------|
| `connected` | Handshake after socket open |
| `invalidate` | React Query (or similar) keys to refetch |
| `tasks_update` | Live task array for a plan |

Must stay aligned with **`../../../contract/events.schema.json`** and Python
`realtime/events.py`.

## wsClient.ts

```typescript
const client = new GatewayRealtimeClient({ wsBaseUrl: 'ws://localhost:8000' })

const ws = client.connectGlobalUpdates((msg) => { ... })
const ws2 = client.connectPlanExecution(planId, (msg) => { ... })
```

Returns native **`WebSocket`** — caller owns lifecycle (`close`, reconnect policy).

URLs:

- `{wsBaseUrl}/ws/global-updates`
- `{wsBaseUrl}/ws/execution/{planId}`

Empty `wsBaseUrl` → relative WS URL (same host as dashboard).

Parsing: `JSON.parse` in `onmessage`; malformed payloads ignored.

## telemetryClient.ts

Browser-oriented helper for subscribing to telemetry streams exposed by Gateway
or telemetry HTTP endpoints (see file for current URL patterns and event parsing).

Use for **visualization** — does not replace agent publishers or
`packages/proto/telemetry.proto` ingest path.

## Combined UI flow

```
Mount plan execution page
    ├─ useQuery loads plan/tasks via gatewayClient (http/)
    └─ connectPlanExecution(planId, handler)
            ├─ tasks_update → setState or merge tasks
            └─ invalidate → queryClient.invalidateQueries
```

Global hook on app shell:

```
connectGlobalUpdates → invalidate queries on fleet-wide changes
```

## How Gateway, fleet, and agents relate

| Path | Flow |
|------|------|
| WS events | fleet state change → Gateway broadcaster → browser |
| Telemetry viewer | telemetry service → Gateway/proxy → telemetryClient |
| Agent publish | agent → TelemetryIngestion gRPC → storage |

Agents do not open `GatewayRealtimeClient`.

## Related documentation

- `../../../contract/README.md` — schema reference
- `../../python/src/realtime/README.md` — Python async equivalent
- `../../../../proto/telemetry.proto` — event ordering (`step_index`, `sequence_id`)
- `../../../../agent_sdk/src/telemetry/` — publisher side

## Reading order

1. **`events.ts`** — handler switch cases.
2. **`wsClient.ts`** — URL builders.
3. Dashboard WebSocket hooks — reconnection patterns.
4. **`telemetryClient.ts`** — if building telemetry widgets.
5. Gateway WS route source — auth and message emission points.

## Robustness tips

- Implement exponential backoff reconnect outside `wsClient` (class is minimal).
- On `invalidate`, prefer targeted query keys over global refetch when lists are
  large.
- For `tasks_update`, validate `plan_id` matches mounted plan before applying.
