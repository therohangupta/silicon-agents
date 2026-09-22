# Where agent telemetry lives

Every agent package can use two paths. Both are configured under `observability` in `config.yaml`.

## Built into every agent

Code: `packages/agent_sdk/src/telemetry/client.py`

- Heartbeats go to `POST {TELEMETRY_URL}/ingest/heartbeat`.
- Task started, completed, and failed events go to `POST {TELEMETRY_URL}/telemetry/ingest`.
- Skill calls and task artifacts use the same ingest endpoint.

No per-agent file is required for this path.

## Optional high-rate stream

Code: `packages/agent_sdk/src/telemetry/publisher.py`

`AgentServer` loads `telemetry_adapter.py` from an agent directory when that file is present, and calls `stream_idle` / `stream_task` around each `/tasks/execute`.
