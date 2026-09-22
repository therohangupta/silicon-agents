# client_sdk/typescript/src/http/

Gateway BFF **REST transport** for the TypeScript client SDK.

## Purpose

Centralizes `fetch` usage so every Gateway resource shares base URL joining, JSON
headers, Bearer auth injection, and error parsing. Resource-specific methods live
in **`gatewayClient.ts`**; low-level plumbing in **`fetchApi.ts`**.

Not used for fleet gRPC or agent task HTTP.

## File inventory

| File | Exports | Role |
|------|---------|------|
| `fetchApi.ts` | `fetchApi`, `GatewayFetchOptions` | Generic JSON GET/POST/PATCH/DELETE |
| `gatewayClient.ts` | `GatewayClient`, `GatewayClientOptions` | Namespaced REST API (`agents`, `plans`, …) |
| `README.md` | — | you are here |

## fetchApi behavior

```
fetchApi<T>(endpoint, { baseUrl, method, body, headers })
    │
    ├─ URL = baseUrl + endpoint (endpoint starts with /api/...)
    ├─ Default Content-Type: application/json
    ├─ Merge caller headers (Authorization from GatewayClient)
    │
    ├─ !response.ok → throw Error(detail || HTTP status)
    └─ return response.json() as T
```

`GatewayFetchOptions` extends `RequestInit` with optional `baseUrl`.

## GatewayClient structure

Instantiated with `{ baseUrl?, bearerToken? }`. Private `headers()` adds Bearer
when token present.

Resource groups (grep `gatewayClient.ts` for full list):

| Property | REST areas |
|----------|------------|
| `agents` | list, get, allocations, register, unregister |
| `goals` | list, get, create, delete |
| `plans` | list, get, create, manual create, delete, allocate, start, status |
| `tasks` | list, get, create, update, delete |
| `world` / embodiment | world model queries |
| `methods` | method catalog for UI |

Each method is a thin `fetchApi` call with typed generic from `../models/types`.

## Typical dashboard flow

```
useQuery(['plans'], () => gatewayClient.plans.list())
        │
        ▼
GET /api/plans → Gateway → ListPlans gRPC
        │
        ▼
Plan[] typed response → render + cache
```

Mutations use `gatewayClient.plans.start(id)` etc., then rely on WebSocket
`invalidate` or manual `queryClient.invalidateQueries`.

## Error handling in UI

`fetchApi` throws `Error` with Gateway `detail` string — catch in mutation hooks
and surface toast notifications.

## How Gateway, fleet, and agents relate

```
Browser GatewayClient → Gateway REST → FleetManagerClient (bridge) → fleet_server
Runnable tasks → agent task_server HTTP (agent_sdk), not fetchApi
```

REST paths are BFF-specific; they may not 1:1 match gRPC message names.

## Related documentation

- `../models/README.md` — TypeScript DTO interfaces
- `../realtime/README.md` — push updates complement REST cache
- `../../contract/README.md` — WebSocket only
- `../../../../config.py` — `GATEWAY_URL` for local dev env vars

## Reading order

1. **`fetchApi.ts`** — error and header rules.
2. **`gatewayClient.ts`** — find resource group for your feature.
3. Gateway service router — confirm path and payload.
4. **`../models/types.ts`** — add fields when API evolves.

## Extension checklist

1. Add Gateway route + server handler.
2. Add interface(s) in `models/types.ts`.
3. Add method under appropriate `gatewayClient` namespace.
4. Wire dashboard hook + optional Python mirror in `python/src/http/client.py`.
