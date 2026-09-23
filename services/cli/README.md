# `services/cli` — future service-packaged CLI image

This directory is a **placeholder** for a deployable CLI container. It does not
contain Python source, Dockerfile, or Compose service definitions yet — only
documentation describing how it relates to the live operator CLI elsewhere in
the repo.

## What exists today

| Location | What it is |
|----------|------------|
| **`cli/`** | Production **Click CLI** (`agentctl`): register agents, goals, tasks, plans via `FleetManagerClient` gRPC |
| **`services/cli/` (here)** | Reserved name for a future **image** that would run the same commands inside Docker/CI |

Operators install the fleet editable (`pip install -e .` from ``) and
invoke the console script:

```bash
agentctl register agents/frontend/architecture/requirements/config.yaml
agentctl list -v
agentctl plan create dag llm 1
```

Implementation modules:

- `cli/agentctl.py` — command tree, YAML validation via `load_agent_config_dict`, gRPC calls
- `cli/printer.py` — stdout formatting and planning/allocation strategy maps
- `cli/__init__.py` — package marker

See [`../../cli/README.md`](../../cli/README.md) for command coverage and examples.

## Why a separate `services/cli` folder?

Fleet services follow a convention: **`services/<name>/`** is something Compose
can `build:` and run as a named container (`gateway`, `telemetry`,
`storage-writer`, …). The Python package path `agent_fleet.cli` must remain
importable from the monorepo root — it should not be moved under `services/`.

A future **`services/cli/Dockerfile`** could:

- Start from a slim Python base (similar to telemetry/gateway images).
- `pip install -e .` or install a wheel with only CLI + fleet_sdk dependencies.
- Set entrypoint `agentctl` with default `GRPC_SERVER_ADDRESS` / `GATEWAY_URL`
  pointing at in-network hostnames (`fleet-server:50051`, `gateway:8000`).
- Ship in CI pipelines that register agents or submit plans without a host Python.

That image would **not** replace the gateway HTTP API — it is for operators who
want a pinned, reproducible CLI environment (Kubernetes Job, GitHub Action, bastion).

## Gateway vs CLI (conceptual)

| Tool | Protocol | Typical use |
|------|----------|-------------|
| **Gateway** | HTTP/WebSocket REST under `/api` | Dashboard, browser clients, SDKs |
| **agentctl** | gRPC to **fleet-server** | Scripting, bulk register, plan creation from terminal |

Neither agentctl nor this future container talks to **telemetry** directly for
fleet control — telemetry is agent ingest and health. Operators see agent health
in the dashboard because the **gateway proxies** telemetry’s `/health/*` routes.

A containerized CLI would still use gRPC to fleet-server unless extended with
HTTP subcommands that call gateway REST (not implemented today).

## Planned contents (when implemented)

When this placeholder graduates to a real service, expect:

```text
services/cli/
  Dockerfile          # non-root user, agentctl entrypoint
  README.md           # (this file, updated)
  compose snippet     # optional profile in docker-compose.yml
```

Non-goals for the CLI image:

- Running agent task servers (`server.py`) — those use `silicon_agent`.
- Writing Parquet — that is `storage_writer`.
- Serving the dashboard — that is `dashboard-web` + gateway.

## Environment alignment

When adding a Dockerfile, mirror variables from platform Compose so in-container
commands match host behaviour:

| Variable | Purpose for CLI |
|----------|-----------------|
| `GRPC_SERVER_ADDRESS` | Target fleet-server gRPC host:port |
| `DATABASE_URL` | Only if future commands query DB directly (today unused by agentctl) |
| Repository `.env` | Secrets for generated compose; mount or inject in CI |

Host-side `agentctl` reads defaults from `FleetManagerClient` / shared config —
document any drift between host and container in the service README when the
image lands.

## Migration checklist (for implementers)

1. Add `services/cli/Dockerfile` with editable or wheel install from repo root context.
2. Wire a Compose service (optional profile) on the `agent_fleet` network.
3. Document example: `docker compose run --rm cli agentctl list`.
4. Keep **`cli/`** as the single source of Click command definitions —
   the image should call the same module, not fork commands.
5. Update [`../README.md`](../README.md) services table if ports or dependencies change.

Until those steps land, treat this directory as documentation-only namespace
reservation — no build required.
