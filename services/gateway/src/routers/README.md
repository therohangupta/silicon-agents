# FastAPI routers

HTTP and WebSocket route handlers for the gateway.

## Mounted on `/api` (`api_router`)

| Module | Prefix | Role |
|--------|--------|------|
| `telemetry.py` | `/telemetry` | In-memory agent heartbeats |
| `agents.py` | `/agents` | Register, health, YAML refresh, allocations |
| `goals.py` | `/goals` | Goal CRUD |
| `plans.py` | `/plans` | Plan create/allocate/start/copy/update |
| `tasks.py` | `/tasks` | Task CRUD |
| `agent_templates.py` | `/agent-templates` | Agent type catalog |
| `methods.py` | `/methods` | Planner/allocator details by id |
| `strategies.py` | `/strategies` | UI strategy dropdown data |
| `metrics.py` | `/metrics` | MetricEvent query API |

## Mounted separately in `app.py`

| Module | Paths | Role |
|--------|-------|------|
| `websocket.py` | `/ws/global-updates`, `/ws/execution/{id}`, `POST /internal/events` | Fleet event bus → UI |
| `agent_telemetry.py` | `/ws/telemetry/{id}`, `/api/telemetry/...` | NATS telemetry fan-out + blobs |
| `agent_templates.ports_router` | `/api/ports/*` | Port suggest / used helpers |

## Not mounted

| Module | Notes |
|--------|-------|
| `prompts.py` | Legacy name-based method lookup (same `/methods` prefix as `methods.py`) |
