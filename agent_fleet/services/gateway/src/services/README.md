# Gateway services

Reusable business logic called from routers (and lifespan shutdown).

## Modules

| File | Role |
|------|------|
| `__init__.py` | Re-exports health, YAML scan, port, telemetry client helpers |
| `agent_health.py` | Direct HTTP probes to agent `/health` (legacy `source=direct`) |
| `telemetry_client.py` | httpx client to Telemetry service health APIs |
| `yaml_scanner.py` | Embodiment + planner/allocator `summary.yaml` discovery |
| `port_manager.py` | Localhost port occupancy and next-port suggestion |

## Preferred health path

Routers default to Telemetry heartbeats (`telemetry_client`). Use
`agent_health` only for debugging or when Telemetry has no data yet.
