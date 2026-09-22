# client_sdk/contract/

**Contract snapshots** for Gateway clients. Machine-readable files here cannot
carry inline comments — field semantics and evolution rules live in this README
and in parallel typed sources (`typescript/src/realtime/events.ts`,
`python/src/realtime/events.py`).

## Purpose

The Gateway BFF pushes realtime JSON over WebSocket. Language SDKs and the
dashboard must parse the same discriminated union without drift. This directory
holds the schema snapshot; the live server in `services/gateway/` is the runtime
authority, but CI and reviewers diff against these files.

## File inventory

| File | Format | Role |
|------|--------|------|
| `events.schema.json` | JSON Schema draft 2020-12 | WebSocket message union |
| `README.md` | Documentation | you are here |

REST OpenAPI snapshots may be added later alongside `events.schema.json`; today
REST shapes are implied by Gateway routes and `client_sdk` typed clients.

## events.schema.json — structure

Top level: `oneOf` array of three object variants, discriminated by required
property **`type`** (string const).

### Variant: `connected`

Sent after the WebSocket opens (hello / handshake).

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `type` | `"connected"` | yes | Discriminant |
| `message` | string | yes | Human-readable hello (logging, UI status) |

Additional properties allowed (`additionalProperties: true`) for forward-compatible
server fields — clients should ignore unknown keys.

### Variant: `invalidate`

Tells clients which cached queries to refetch (React Query key list).

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `type` | `"invalidate"` | yes | Discriminant |
| `queries` | string[] | yes | Cache keys to invalidate |
| `timestamp` | number | yes | Server time (ms or s — treat as opaque ordering) |

Typical handler: `queryClient.invalidateQueries({ queryKey: … })` for each
entry in `queries`.

### Variant: `tasks_update`

Live task list snapshot for a plan execution view.

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `type` | `"tasks_update"` | yes | Discriminant |
| `plan_id` | integer | yes | Plan being executed |
| `tasks` | object[] | yes | Task DTOs (Gateway-shaped JSON objects) |

Task object inner schema is intentionally loose (`object`) until a dedicated
`TaskSnapshot.schema.json` is split out — TypeScript `Task` type in
`client_sdk/typescript/src/models/types.ts` is the practical reference for fields.

## Alignment rules (TypeScript / Python)

When changing WebSocket payloads:

1. Update Gateway publisher and consumer handlers.
2. Edit **`events.schema.json`** first or in the same commit.
3. Update **`typescript/src/realtime/events.ts`** union types.
4. Update **`python/src/realtime/events.py`** dataclasses + `GatewayRealtimeMessage`.
5. Add dashboard or script tests that parse sample JSON.

TypeScript uses a typed union; Python uses frozen dataclasses plus
`Union[..., dict[str, Any]]` fallback for forward compatibility.

## WebSocket endpoints (reference)

Implemented in `GatewayRealtimeClient` (both languages):

| Path | Use |
|------|-----|
| `/ws/global-updates` | Fleet-wide invalidate + connected |
| `/ws/execution/{plan_id}` | Plan-scoped tasks_update stream |

Base URL: `GATEWAY_WS_URL` from platform config (Python default) or
`wsBaseUrl` constructor option (TypeScript).

## Flow diagram

```
fleet_server state change
        │
        ▼
Gateway internal event hook
        │
        ▼
WebSocket send JSON { type: "invalidate", queries: [...] }
        │
        ├── dashboard GatewayRealtimeClient → React Query
        └── Python script watch_global_updates → custom handler
```

`tasks_update` follows the same path on `/ws/execution/{plan_id}` during
`StartPlan` execution.

## How Gateway, fleet, and agents relate

| Component | Role |
|-----------|------|
| **Gateway** | Produces messages conforming to this schema |
| **fleet_server** | Source of truth for plan/task state; Gateway translates to WS |
| **Agents** | Do not send these WS messages; they update state via fleet/agent APIs |
| **client_sdk** | Parses and types these messages for external clients |

## Related documentation

- `../README.md` — client_sdk overview
- `../typescript/src/realtime/README.md` — browser client usage
- `../python/src/realtime/README.md` — async websockets usage
- `../../config.py` / `platform.yaml` — Gateway and WS URLs

## Reading order

1. Read this README for field semantics.
2. Open **`events.schema.json`** side-by-side with **`events.ts`**.
3. Trace one **`invalidate`** from Gateway source to dashboard handler.
4. When adding a fourth event type, extend `oneOf` and all language bindings in
   one change set.

## Validation ideas

- JSON Schema validator in CI on sample fixtures checked into `contract/` or tests.
- Golden files: `connected.json`, `invalidate.json`, `tasks_update.json` (optional
  future addition — not required for schema presence today).
