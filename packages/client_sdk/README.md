# client_sdk

Multi-language SDKs for the **Gateway BFF** — the only supported client-facing
API for dashboards, CLIs, automation scripts, and mobile clients.

## Purpose

External callers must not open gRPC channels to `fleet_server` or scrape agent
HTTP task servers directly. The Gateway translates REST and WebSocket contracts
into control-plane operations and fans out realtime updates. This folder holds:

- A **contract snapshot** (JSON Schema for WebSocket events)
- **TypeScript** package `@agent-fleet/client-sdk` for `dashboard-web`
- **Python** package `agent-fleet-client-sdk` for scripts and operator tools

Both language SDKs mirror the same routes and event shapes. When the Gateway
changes, update the server, the contract file, then both SDKs.

## What this is not

| Need | Use instead |
|------|-------------|
| Fleet control-plane gRPC | `packages/fleet_sdk` |
| Agent task-server HTTP | `packages/agent_sdk/src/client` |
| Telemetry gRPC publish from agents | `packages/agent_sdk/src/telemetry` |
| Gateway server implementation | `services/gateway/` (or equivalent) |

## Directory layout

```
client_sdk/
├── README.md                 ← you are here
├── contract/                 ← JSON Schema (no inline comments)
├── typescript/               ← @agent-fleet/client-sdk
├── python/                   ← agent-fleet-client-sdk (pyproject.toml)
└── src/                      ← legacy placeholder (see src/README.md)
```

## End-to-end flows

### REST read/write (plans, tasks, agents)

```
UI or script
    │  GatewayClient.* / gatewayClient.*
    ▼
GET/POST/PATCH /api/...
    ▼
Gateway BFF ──gRPC──► fleet_server
    ▼
Postgres registry
```

Typical dashboard flow: React hook calls `gatewayClient.plans.list()` → Gateway
proxies to `ListPlans` → JSON array returned → React Query caches by key.

### Realtime invalidation and live task lists

```
Gateway publishes JSON on /ws/global-updates or /ws/execution/{plan_id}
    ▼
GatewayRealtimeClient (TS WebSocket or Python websockets)
    ▼
Handler: invalidate React Query keys OR merge tasks_update payload
```

Event discriminant is always `type`: `connected`, `invalidate`, or
`tasks_update`. See `contract/events.schema.json`.

### Live telemetry panels (browser only)

TypeScript `telemetryClient` consumes Gateway/telemetry HTTP or SSE-style
streams for dashboard widgets. This is **viewer** traffic — not the agent-side
gRPC publisher in `agent_sdk`.

## TypeScript SDK

- **Package:** `@agent-fleet/client-sdk` (`typescript/package.json`)
- **Entry:** `typescript/src/index.ts` re-exports models, HTTP, realtime
- **Consumer:** `dashboard-web` via `"@agent-fleet/client-sdk": "file:…"`

Key exports:

| Export | Module | Role |
|--------|--------|------|
| `GatewayClient` | `http/gatewayClient.ts` | Typed REST for agents, plans, tasks, goals, world, methods |
| `fetchApi` | `http/fetchApi.ts` | Low-level fetch + JSON error shaping |
| `GatewayRealtimeClient` | `realtime/wsClient.ts` | WebSocket subscriptions |
| Event types | `realtime/events.ts` | Discriminated union aligned with JSON Schema |
| Telemetry helpers | `realtime/telemetryClient.ts` | Browser live telemetry |

Configure with `baseUrl` / `wsBaseUrl` (empty string = same-origin in the
browser). Optional `bearerToken` on HTTP client.

## Python SDK

- **Package:** `agent-fleet-client-sdk` (`python/pyproject.toml`)
- **Deps:** `httpx`, `websockets`
- **Default base URL:** `GATEWAY_URL` from `packages.platform_config.setting`
- **Default WS URL:** `GATEWAY_WS_URL`

Modules:

| Path | Role |
|------|------|
| `python/src/http/client.py` | Sync REST client (plans, tasks, agents subset) |
| `python/src/models/types.py` | Typed payload helpers (grows with contract) |
| `python/src/realtime/ws_client.py` | Async global/plan WebSocket watchers |
| `python/src/realtime/events.py` | Dataclasses for WS events |

Install editable from repo root for scripts:

```bash
pip install -e packages/client_sdk/python
```

## Contract maintenance

`contract/events.schema.json` is the authoritative WebSocket union. JSON cannot
hold comments — document field semantics in `contract/README.md`. When adding an
event type:

1. Extend Gateway publisher and handler.
2. Update `events.schema.json`.
3. Update `typescript/src/realtime/events.ts` and `python/src/realtime/events.py`.
4. Add dashboard handling + tests.

OpenAPI for REST may live in Gateway service docs; this repo snapshot focuses
on realtime events today.

## How Gateway, fleet, and agents relate

| Component | Talks to client_sdk? |
|-----------|---------------------|
| **Gateway** | Implements the HTTP/WS contract these clients call |
| **fleet_server** | Indirect — only via Gateway (or internal gRPC) |
| **Agents** | No — agents use agent_sdk + fleet registration, not client_sdk |

Operators scripting against the fleet should prefer Python `GatewayClient` for
parity with the UI, or `fleet_sdk` gRPC when Gateway routes do not exist yet.

## Related documentation

- `packages/README.md` — platform layer index
- `packages/fleet_sdk/README.md` — gRPC alternative for internal tools
- `packages/proto/README.md` — wire contracts behind Gateway bridge
- `contract/README.md` — WebSocket schema field reference

## Reading order

1. **`contract/README.md`** — event types and alignment rules.
2. **`typescript/README.md`** or **`python/README.md`** — pick your language.
3. **`typescript/src/http/README.md`** / **`python/src/http/README.md`** — REST
   method inventory.
4. **`…/realtime/README.md`** — WebSocket URLs and handler patterns.
5. Gateway service source — route list must match `gatewayClient` methods.

## File inventory (documentation map)

| README | Scope |
|--------|--------|
| `contract/README.md` | JSON Schema |
| `typescript/README.md` | NPM package layout |
| `typescript/src/README.md` | TS source barrel |
| `typescript/src/http/README.md` | fetchApi + gatewayClient |
| `typescript/src/models/README.md` | Gateway JSON types |
| `typescript/src/realtime/README.md` | WS + telemetry viewer |
| `python/README.md` | Packaging |
| `python/src/README.md` | Python layout |
| `python/src/http/README.md` | httpx client |
| `python/src/models/README.md` | types.py |
| `python/src/realtime/README.md` | websockets client |
| `src/README.md` | Legacy empty dir note |
