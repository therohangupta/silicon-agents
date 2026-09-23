# Agent SDK — HTTP client (`packages/agent_sdk/src/client/`)

This directory provides **`AgentClient`**, a minimal async HTTP client for calling **another agent’s task server** on the fleet internal network. It speaks the same JSON contract as `AgentServer` (`AgentTaskRequest` in, `AgentTaskResult` out).

This is **not** the Gateway **`client_sdk/`**, which targets the BFF and user-facing APIs. Use `AgentClient` when one agent (or a test harness) must invoke a peer’s `/tasks/execute` directly by host and port from YAML.

---

## Purpose in the fleet

During multi-agent plans, a lead agent may delegate work by HTTP rather than waiting for the central executor to schedule the next task. Examples:

- Prototype orchestration in integration tests
- Experimental “call specialist agent” flows from `tools.py`
- Health checks before submitting dependent tasks

The fleet’s primary path remains **executor → agent POST**; this client is a **building block** for agent-initiated calls.

---

## Placement in architecture

```text
Agent A (caller)                          Agent B (callee)
    │                                         │
    │  AgentClient(host, port)                │  AgentServer / AgentService
    │       POST /tasks/execute               │       execute route
    │       GET  /health                      │       health route
    └────────────────────────────────────────►│
              AgentTaskRequest                  AgentTaskResult
```

Models are shared via [`../contracts/`](../contracts/) and [`../config/`](../config/) — no duplicate schema.

---

## Files in this directory

| File | Role |
|------|------|
| [`agent_client.py`](agent_client.py) | `AgentClient` class — httpx async client, health + execute |
| [`__init__.py`](__init__.py) | Package marker; import from `agent_client` |
| [`README.md`](README.md) | This document |

---

## `AgentClient` API

Construction:

```python
client = AgentClient(host="placement-lead", port=8243, execute_path="/tasks/execute")
```

- **`host`** / **`port`** — Required; must match callee `connection` in its `config.yaml`.
- **`execute_path`** — Override only if callee customizes `connection.endpoints.execute`.

Methods:

| Method | HTTP | Returns |
|--------|------|---------|
| `health()` | GET `{base_url}/health` | `AgentHealth` |
| `execute_task(request)` | POST `{base_url}{execute_path}` | `AgentTaskResult` |
| `close()` | — | Closes httpx client |

**Timeouts** — The underlying `httpx.AsyncClient` uses `timeout=None` for execute (long-running tasks). Callers should wrap with `asyncio.wait_for` if they need bounded waits.

**Errors** — Non-2xx responses raise via `raise_for_status()`; callers map to replan or retry using [`ReliabilityConfig`](../config/) on the callee side.

---

## Data and control flow

1. Caller builds `AgentTaskRequest` (task_id, description, optional `workspace_uri`, `context`, `inputs`, `required_capabilities`).
2. `execute_task` serializes with `model_dump(mode="json")` and POSTs JSON.
3. Response JSON parsed into `AgentTaskResult` (success, artifacts, traces, replan flags).
4. Caller should `await client.close()` on shutdown to release connections.

Health flow: optional preflight before execute in tests or circuit-breaker patterns.

---


---

## Related paths

| Path | Relationship |
|------|----------------|
| [`../server/README.md`](../server/README.md) | Server routes this client calls |
| [`../contracts/`](../contracts/) and [`../config/`](../config/) | Request/result types |
| [`../../../../client_sdk/`](../../../../client_sdk/) | Gateway client (different API) |

---

## Newcomer reading order

1. [`../server/README.md`](../server/README.md) — understand server endpoints
2. [`../contracts/`](../contracts/) and [`../config/`](../config/) — `AgentTaskRequest` / `AgentTaskResult`
3. This README — construct client and call patterns
4. Agent’s `config.yaml` — callee port and endpoints

---

## Operational notes

- **TLS** — Client uses plain `http://`; mTLS or TLS termination happens at mesh/ingress if enabled.
- **Busy callee** — Health may report `status: busy`; retry or backoff is caller responsibility.
- **Idempotency** — Use stable `task_id` when retries matter; server does not dedupe by default.
- **Docker DNS** — Use service names from compose, not `localhost`, when calling from another container.
- **Testing** — Spin up `AgentServer.from_yaml` in pytest and point `AgentClient` at `127.0.0.1` ephemeral port.

No subdirectories exist under `client/`; all behavior is in `agent_client.py`.
