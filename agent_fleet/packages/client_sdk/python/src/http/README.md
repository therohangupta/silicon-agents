# client_sdk/python/src/http/

Sync **HTTP client** for the Gateway BFF REST API.

## Purpose

`client.py` exposes `GatewayClient`, a thin httpx wrapper that mirrors a subset
of Gateway routes for automation. It centralizes base URL joining, JSON headers,
Bearer auth, and error translation so scripts do not duplicate fetch logic.

This is **not** the fleet gRPC client (`packages/fleet_sdk`) and **not** the
agent task-server client (`packages/agent_sdk/src/client`).

## File inventory

| File | Symbol | Role |
|------|--------|------|
| `client.py` | `GatewayClient` | Dataclass with `_request` + resource methods |
| `README.md` | — | you are here |

## GatewayClient configuration

| Field | Default | Notes |
|-------|---------|-------|
| `base_url` | `GATEWAY_URL` from platform config | No trailing slash |
| `bearer_token` | `None` | Sent as `Authorization: Bearer …` when set |
| `timeout_seconds` | `30.0` | httpx client timeout |

## Request pipeline

```
_request(method, path, json?)
    │
    ├─ Build URL: f"{base_url}{path}"
    ├─ Headers: Content-Type application/json + optional Bearer
    ├─ httpx.Client.request(...)
    │
    ├─ status >= 400 → RuntimeError(detail from JSON or text)
    └─ else → resp.json() as Any
```

## Implemented REST surface (grep source for authoritative list)

The module grows with Gateway; typical groups today:

| Area | Methods (indicative) | HTTP |
|------|----------------------|------|
| Plans | `list_plans`, `get_plan`, `create_plan`, `allocate_plan`, `start_plan` | GET/POST under `/api/plans` |
| Tasks | `list_tasks`, `update_task` | GET/PATCH under `/api/tasks` |

Compare with **`client_sdk/typescript/src/http/gatewayClient.ts`** for agents,
goals, world, and methods — add matching Python methods when scripts need them.

## Example usage

```python
from packages.client_sdk.python.src.http.client import GatewayClient

client = GatewayClient()  # uses GATEWAY_URL
plans = client.list_plans()
client.start_plan(plans[0]["plan_id"])
```

Adjust import path to match your install / PYTHONPATH layout.

## Error behavior

- HTTP errors become **`RuntimeError`** with Gateway `detail` field when JSON
  body parses.
- Network failures propagate from httpx.

No automatic retries — scripts should wrap transient failures if needed.

## How Gateway, fleet, and agents relate

```
Python script → GatewayClient → Gateway REST → gRPC bridge → fleet_server
Agents ← task dispatch ← fleet_server (not via GatewayClient)
```

Gateway translates REST to proto messages; this module never serializes protobuf.

## Related documentation

- `../README.md` — src tree overview
- `../../README.md` — Python package install
- `../../../typescript/src/http/README.md` — full REST parity reference
- `../../../../config.py` — `GATEWAY_URL`

## Reading order

1. Read **`client.py`** end-to-end for current methods.
2. Open Gateway route definitions for payload shapes.
3. Add types in **`../models/types.py`** when freezing response contracts.
4. Cross-check TS **`gatewayClient.ts`** before implementing new endpoints.

## Extension checklist

1. Confirm Gateway path and JSON body with server source.
2. Add method on `GatewayClient` calling `_request`.
3. Add dataclass types in `models/types.py` if stable.
4. Document in TS and Python READMEs if user-facing.
