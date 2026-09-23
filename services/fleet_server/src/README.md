# Fleet Server (`src`)

gRPC **FleetManager** service (default port **50051** via `__main__.py`).

## Layout

| Module | Purpose |
|--------|---------|
| `__main__.py` | CLI: port, `--reset-db`, logging, graceful shutdown |
| `service.py` | `FleetManagerService` servicer + `serve()` |
| `events.py` | Re-exports SDK gateway `emit_*` helpers |

Planning, allocation, formats, execution, and execution context live in
`packages/fleet_sdk/src/` (`planners/`, `allocators/`, `formats/`, `executor/`,
`execution_context.py`).
