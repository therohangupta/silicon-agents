# client_sdk/python/src/

Python **implementation root** for the Gateway client SDK.

## Purpose

Organizes sync HTTP and async WebSocket clients plus shared typed event models.
This tree is imported by installed package `agent-fleet-client-sdk` and by
in-repo scripts when `PYTHONPATH` includes the parent directories.

## Directory layout

```
src/
├── README.md           ← you are here
├── http/
│   ├── README.md
│   └── client.py       ← GatewayClient (httpx)
├── models/
│   ├── README.md
│   └── types.py        ← typed payload helpers
└── realtime/
    ├── README.md
    ├── events.py       ← WS event dataclasses
    └── ws_client.py    ← GatewayRealtimeClient
```

No `__init__.py` re-export barrel is required for all layouts; consumers import
submodules explicitly depending on packaging config.

## Cross-module flow

### REST call path

```
Script constructs GatewayClient(base_url=..., bearer_token=...)
        │
        ▼
client._request(method, path, json=...)
        │
        ▼
httpx.Client → {base_url}{path}
        │
        ▼
JSON dict (untyped Any today; refine via models/types.py)
```

Default `base_url` loads `GATEWAY_URL` from `packages.platform_config.setting`
when omitted in `__post_init__`.

### Realtime path

```
GatewayRealtimeClient(ws_base_url=...)
        │
        ▼
websockets.connect({ws}/ws/global-updates | .../execution/{plan_id})
        │
        ▼
json.loads(message) → passed to on_message callback
        │
        ▼
Optional: isinstance checks against events.Connected / Invalidate / TasksUpdate
```

Parse failures in `ws_client.py` are swallowed per message to keep the stream alive.

## Module responsibilities

| Submodule | Sync/async | Depends on |
|-----------|------------|------------|
| `http` | Sync | httpx, platform_config (defaults) |
| `models` | N/A | stdlib dataclasses |
| `realtime` | Async | websockets, events |

## Contract alignment

WebSocket payloads must match:

- `../../contract/events.schema.json`
- `realtime/events.py` dataclass fields

REST paths must match Gateway routes and TypeScript `gatewayClient.ts` methods.

## How Gateway, fleet, and agents use this code

| Actor | Usage |
|-------|--------|
| **Operators / CI** | Primary audience — run scripts against Gateway |
| **Gateway** | Server counterpart — not an importer |
| **fleet_server** | Indirect via Gateway REST |
| **Agents** | No |

## Related documentation

- `../README.md` — packaging and install
- `http/README.md` — REST method inventory
- `models/README.md` — typing strategy
- `realtime/README.md` — WebSocket URLs and handlers
- `../../typescript/src/` — feature parity reference

## Reading order

1. **`http/client.py`** — what REST operations exist today.
2. **`realtime/events.py`** — event shapes.
3. **`realtime/ws_client.py`** — subscription loops.
4. **`models/types.py`** — extend typing as contract stabilizes.
5. Gateway service — confirm paths and auth headers.

## Development notes

- Prefer adding typed return models in `models/types.py` when stabilizing REST
  responses instead of leaving `Any` on `GatewayClient` methods.
- Bearer token: set `GatewayClient.bearer_token` when Gateway auth is enabled.
- Timeouts: `timeout_seconds` on dataclass (default 30s).
