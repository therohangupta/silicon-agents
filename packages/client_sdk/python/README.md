# client_sdk/python/

Python packaging for the **Gateway client SDK** (`agent-fleet-client-sdk`).

## Purpose

Scripts, operator CLIs, and integration tests need the same REST and WebSocket
behavior as `dashboard-web` without importing TypeScript. This directory is the
installable Python project; implementation modules live under **`src/`**.

## File inventory

| Path | Role |
|------|------|
| `pyproject.toml` | Hatchling build, project metadata, dependencies |
| `README.md` | you are here |
| `src/` | Source tree — see `src/README.md` |

## pyproject.toml summary

| Key | Value |
|-----|--------|
| Project name | `agent-fleet-client-sdk` |
| Version | `0.0.0` (monorepo dev) |
| Python | `>=3.11` |
| Dependencies | `httpx`, `websockets` |
| Build | `hatchling` |

The package is not necessarily published to PyPI; editable installs from the
repo are the common path.

## Installation

From repository root (adjust path if your cwd differs):

```bash
pip install -e packages/client_sdk/python
```

Ensure `agent_fleet` is on `PYTHONPATH` when using defaults that call
`packages.platform_config.setting("GATEWAY_URL")` inside `GatewayClient`.

## Public modules (under src/)

| Module | Entry types | Transport |
|--------|-------------|-----------|
| `http.client` | `GatewayClient` | Sync REST via httpx |
| `models.types` | Dataclasses / helpers | N/A |
| `realtime.ws_client` | `GatewayRealtimeClient` | Async WebSocket |
| `realtime.events` | `Connected`, `Invalidate`, `TasksUpdate` | Parsed WS JSON |

Import style in monorepo scripts:

```python
from client_sdk.python.src.http.client import GatewayClient  # if path wired
# OR copy src layout into installed package name per pyproject packages config
```

Check `pyproject.toml` `[tool.hatch.build.targets.wheel]` packages table if
imports fail — monorepo scripts often add `src` to path directly.

## Default configuration

`GatewayClient` and `GatewayRealtimeClient` resolve empty base URLs from
platform settings:

- **`GATEWAY_URL`** — HTTP REST base (no trailing slash)
- **`GATEWAY_WS_URL`** — WebSocket origin for realtime clients

These keys are produced by `packages.platform_config.host_settings()` from
`config/platform.yaml`, overridable via environment variables.

## Typical script flows

### List plans and start execution

```
GatewayClient().list_plans()
    → GET /api/plans
GatewayClient().start_plan(plan_id)
    → POST /api/plans/{id}/start
```

Errors raise `RuntimeError` with Gateway `detail` JSON when present.

### Watch live task updates

```
asyncio.run(watch_plan(plan_id))
    → GatewayRealtimeClient.watch_plan_execution
    → on_message(TasksUpdate) handler
```

See `src/realtime/README.md` for async patterns.

## How Gateway, fleet, and agents relate

| Component | Relationship |
|-----------|--------------|
| **Gateway** | Sole HTTP/WS peer for this SDK |
| **fleet_server** | Reached only through Gateway REST mapping |
| **Agents** | Not addressed by this package |

For direct gRPC automation use `packages/fleet_sdk` instead.

## Related documentation

- `../README.md` — dual-language SDK overview
- `src/README.md` — layout of http / models / realtime
- `../contract/README.md` — WebSocket JSON Schema
- `../../config.py` — `GATEWAY_URL` derivation

## Reading order

1. **`pyproject.toml`** — dependencies and package name.
2. **`src/http/client.py`** — available REST methods.
3. **`src/realtime/ws_client.py`** — WebSocket entry points.
4. **`../typescript/src/http/gatewayClient.ts`** — parity reference for missing
   Python methods (TS client is often ahead).

## Parity with TypeScript

The TypeScript `GatewayClient` exposes more resource groups (agents, goals,
world, methods). Python `client.py` currently focuses on plans/tasks subset —
extend Python when scripts need feature parity; mirror URL paths from TS.
