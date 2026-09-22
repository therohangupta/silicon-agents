# client_sdk/python/src/realtime/

**WebSocket client** and **event types** for Gateway live updates.

## Purpose

Dashboard users see plan execution progress via WebSocket pushes. Python
operators running long scripts need the same streams without polling REST.
This directory implements async consumers using **`websockets`** and typed event
dataclasses aligned with **`contract/events.schema.json`**.

## File inventory

| File | Symbols | Role |
|------|---------|------|
| `events.py` | `Connected`, `Invalidate`, `TasksUpdate`, `GatewayRealtimeMessage` | Parsed message shapes |
| `ws_client.py` | `GatewayRealtimeClient` | `watch_global_updates`, `watch_plan_execution` |
| `README.md` | — | you are here |

## GatewayRealtimeClient

Construction:

- **`ws_base_url`** — defaults to `GATEWAY_WS_URL` from `platform_config.setting`
- Trailing slashes stripped on init

Methods (async, blocking until connection closes):

| Method | URL suffix | Typical events |
|--------|------------|----------------|
| `watch_global_updates(on_message)` | `/ws/global-updates` | `connected`, `invalidate` |
| `watch_plan_execution(plan_id, on_message)` | `/ws/execution/{plan_id}` | `tasks_update`, `invalidate` |

Each method opens `websockets.connect`, iterates messages, `json.loads`, and
invokes callback. JSON parse errors are ignored per message.

## Event types (events.py)

| Class | `type` const | Fields |
|-------|--------------|--------|
| `Connected` | `"connected"` | `message: str` |
| `Invalidate` | `"invalidate"` | `queries: list[str]`, `timestamp: float` |
| `TasksUpdate` | `"tasks_update"` | `plan_id: int`, `tasks: list[dict]` |

`GatewayRealtimeMessage = Union[Connected, Invalidate, TasksUpdate, dict[str, Any]]`
allows unknown future variants without crashing handlers.

Handlers should branch on `msg["type"]` or use isinstance when manually
constructing dataclasses from dicts.

## Example pattern

```python
import asyncio
from packages.client_sdk.python.src.realtime.ws_client import GatewayRealtimeClient
from packages.client_sdk.python.src.realtime.events import TasksUpdate

async def main(plan_id: int):
    client = GatewayRealtimeClient()

    def on_msg(raw):
        if isinstance(raw, dict) and raw.get("type") == "tasks_update":
            print("tasks", len(raw.get("tasks", [])))

    await client.watch_plan_execution(plan_id, on_msg)

asyncio.run(main(1))
```

For production, add reconnection backoff — this client is intentionally minimal.

## Flow with Gateway and fleet

```
fleet_server updates task state
        ▼
Gateway execution broadcaster
        ▼
WebSocket JSON tasks_update
        ▼
watch_plan_execution → operator script / test harness
```

Agents do not connect to these WebSocket endpoints; they report status through
fleet/agent HTTP APIs.

## TypeScript counterpart

| Python | TypeScript |
|--------|------------|
| `GatewayRealtimeClient` | `realtime/wsClient.ts` |
| `events.py` | `realtime/events.ts` |
| async `watch_*` | sync `connectGlobalUpdates` returning `WebSocket` |

Browser TS client returns raw WebSocket for React lifecycle control; Python
uses async context manager inside `watch_*`.

## Related documentation

- `../../contract/README.md` — JSON Schema field reference
- `../../../typescript/src/realtime/README.md` — telemetryClient (browser-only)
- `../../../../config.py` — WS URL via platform yaml

## Reading order

1. **`events.py`** — discriminant values.
2. **`ws_client.py`** — URL construction.
3. Gateway WebSocket route handlers — auth and subscription rules.
4. Dashboard React hooks — idiomatic invalidate handling to mirror in scripts.

## Security note

If Gateway adds WS auth, extend `ws_client.py` to pass headers/cookies on
connect — mirror Gateway server requirements when implemented.
