# Silicon agent base image

Shared **Docker image** for silicon and EDA agent task servers. One build
produces `agentfleet/silicon-agent:dev`; Compose reuses that image for every
entry in `docker-compose.agents.yml` by changing `working_dir` and `command`
only.

## Design goals

- **Single filesystem copy** of the monorepo inside the container (`/app`).
- **Editable install** so `packages.*`, `domains.*`, and `agents.*` imports match
  developer laptops.
- **No default process** in the Dockerfile — each agent package supplies
  `python server.py` (or equivalent) via Compose.
- **Same Python version** as platform services (`python:3.11-slim`) to avoid
  wheel and typing drift.

Agents are not micro-images per role unless a package adds its own Dockerfile
for extra OS packages (EDA tools, licensed binaries, GPU drivers).

## Dockerfile walkthrough

File: `services/silicon_agent/Dockerfile`

| Step | Effect |
|------|--------|
| `FROM python:3.11-slim` | Small glibc-based runtime |
| `WORKDIR /app` | Expected repo root inside container |
| `COPY . .` | Full build context (repo root when built from Compose) |
| `RUN pip install -e .` | Installs `agent_fleet` distribution and dependencies from `pyproject.toml` |
| `ENV PYTHONUNBUFFERED=1` | Line-buffered logs for Docker |
| `ENV PYTHONPATH=/app` | Imports resolve before site-packages links settle |

There is **no `CMD` or `ENTRYPOINT`**. Compose sets both per service.

Build from repo root:

```bash
docker build -f services/silicon_agent/Dockerfile -t agentfleet/silicon-agent:dev .
```

## Compose pattern (`docker-compose.agents.yml`)

Generated agent services share:

```yaml
image: agentfleet/silicon-agent:dev
build:
  context: .
  dockerfile: services/silicon_agent/Dockerfile
working_dir: /app/agents/<track>/.../<agent_name>
command: ["python", "server.py"]
ports:
  - "<host>:<container>"   # task server port from agent config
networks:
  - agent_fleet            # external platform network
```

Example: `requirements` agent uses
`working_dir: /app/agents/frontend/architecture/requirements` and publishes
port **8202**.

The **host:port** pair is what agents report to telemetry heartbeats — the
gateway correlates registered agents with telemetry keys via endpoint metadata.

## Runtime environment (typical)

Agent containers receive memory-plane and observability variables from the
generated Compose file, including:

| Variable | Role |
|----------|------|
| `DATABASE_URL` / `MEMORY_*` | Memory plane backends (Postgres, Cassandra, MinIO, ClickHouse, OpenSearch, Vault, git, NATS) |
| `NATS_URL` | Event bus for agent SDK publishers |
| `TELEMETRY_URL` | HTTP telemetry base (heartbeats, optional HTTP ingest) |
| `TELEMETRY_GRPC_PORT` / `TELEMETRY_GRPC_TARGET` | gRPC ingest target inside the cluster |

Exact keys depend on the agent’s `config.yaml` and fleet startup script — treat
the generated YAML as source of truth after `scripts/startup.sh <fleet.yaml>`.

Agents **do not** embed gateway URLs for fleet control unless configured in SDK
code; task servers focus on telemetry and memory while fleet-server orchestrates
plans via gRPC from the platform stack.

## Relationship to platform services

```text
silicon_agent container (server.py)
    │ heartbeats / StreamTelemetry
    ▼
telemetry → NATS → storage-writer (persist=true)
    │
    ▼
gateway ← fleet-server (plans/tasks assigned to agent endpoints)
```

The silicon image is **not** telemetry, gateway, or fleet-server — it is the
**workload runtime** those services coordinate.

## When to override with a per-agent Dockerfile

Stay on `silicon_agent` when the agent is pure Python with dependencies already
in `pyproject.toml`.

Add `agents/.../Dockerfile` when you need:

- Apt packages (compilers, EDA CLIs, headless tools).
- Multi-stage copies that shrink runtime layers.
- Non-root users or capability drops specific to a tool chain.

Override pattern in Compose: point `build.dockerfile` at the agent file but keep
`context: .` at repo root so shared packages remain importable.

## Local development without Docker

Developers often run `python server.py` directly from an agent directory on the
host with the same editable install. Docker reproduces that layout under `/app`
with identical `PYTHONPATH` semantics.

## Image naming and rebuild

Changing **shared** dependencies (`pyproject.toml`, `packages/*`) requires
rebuilding the silicon image so all agent containers pick up the change:

```bash
docker compose -f docker-compose.agents.yml build
```

Changing **one agent’s** Python code bind-mounts are not used by default — rebuild
or use dev compose overrides if hot reload inside containers is required.

## Security and secrets

Compose injects secrets from the repository `.env` (Postgres, MinIO, ClickHouse,
Vault dev token, etc.). The base image does not bake secrets; it only provides
the Python stack.

For production, pin image digests, run agents as non-root, and restrict the
`agent_fleet` network to required services only.

## Related docs

- [`../README.md`](../README.md) — platform vs silicon-agents Compose projects
- [`../telemetry/README.md`](../telemetry/README.md) — heartbeat and ingest APIs
- [`../../docker-compose.agents.yml`](../../docker-compose.agents.yml) — generated agent list
- [`../../agents/README.md`](../../agents/README.md) — agent package layout (if present)
