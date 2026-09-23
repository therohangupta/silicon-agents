# How to run and test the fleet

Everything runs from the **repository root** (this tree). Install once with `pip install -e .` from here so `packages`, `services`, `domains`, and `cli` import correctly.

**Postgres:** Defaults for bare-metal Python services match `packages/config.py`: host `localhost`, port **5432**, database `agent_fleet`, user `agent_user`, password from `.env`. Override with `DATABASE_URL` or `DB_*` env vars. **Docker Compose** maps the container to the host as **localhost:5433** → container `5432`, so if only the DB runs in Compose and the stack runs on the host, set `DB_PORT=5433` (or a full `DATABASE_URL` using port 5433).

Optional: for Compose, `docker-compose.yml` loads **`.env`** at the repo root for secrets on **fleet-server**.

You need **four terminals** for bare-metal dev (or use Docker Compose). Commands below assume your cwd is the repo root.

---

## 1. Install the repo (one-time)

```bash
pip install -e .
```

This editable install exposes the `packages`, `services`, and `cli` packages (including the `agentctl` entry point).

---

## 2. Terminal 1 – Fleet server (gRPC, port 50051)

```bash
python -m services.fleet_server.src -v
```

Leave it running. It uses the same DB as the gateway.

---

## 3. Terminal 2 – Telemetry service (heartbeat ingest, port 9000)

```bash
python -m services.telemetry.src --port 9000
```

Leave it running. Agents POST heartbeats here; the gateway queries it for health.

---

## 4. Terminal 3 – Gateway (REST + WebSocket, port 8000)

```bash
cd services/gateway
uvicorn src.main:app --reload --port 8000
```

Leave it running. The Vite dev server proxies `/api` and `/ws` to this port (see `services/dashboard-web/vite.config.ts`).

---

## 5. Terminal 4 – Frontend (Vite, port 5173)

```bash
cd services/dashboard-web
npm install   # once per clone
npm run dev
```

Open **http://localhost:5173** in the browser.

---

## Selected agents

From the repo root:

```bash
./scripts/startup.sh fleets/requirements-and-rtl.yaml
```

This starts the macOS-host EDA toolchain before the platform and agent containers.
Agents connect to it through `host.docker.internal:8090`; no separate EDA
terminal is required. The fleet file lists agent directories under `agents:`.
`platform-only.yaml` starts the control plane without agents.

---

## Quick check

- **Gateway**: `curl -s http://localhost:8000/health` → `{"status":"healthy",...}`
- **Telemetry**: `curl -s http://localhost:9000/healthz` → `{"status":"ok"}`
- **Frontend**: http://localhost:5173 loads the dashboard.

---

## Summary

| Component     | Command (from repo root)                                                                 | Port  |
|--------------|-------------------------------------------------------------------------------------------|-------|
| Fleet server  | `pip install -e . && python -m services.fleet_server.src -v`                             | 50051 |
| Telemetry     | `pip install -e . && python -m services.telemetry.src --port 9000`                         | 9000  |
| Gateway       | `cd services/gateway && uvicorn src.main:app --reload --port 8000`                         | 8000  |
| Frontend      | `cd services/dashboard-web && npm run dev`                                                 | 5173  |

Use `pip install -e .` from the repo root first for Python imports and `agentctl`.

---

## Docker (scalable)

Compose files live under **`compose/`** (see [compose/README.md](../compose/README.md)). Startup renders `compose/docker-compose.platform.generated.yml` from `config/platform.yaml`.

```bash
python scripts/render_platform_compose.py --out compose/docker-compose.platform.generated.yml
docker compose -f compose/docker-compose.platform.generated.yml up --build
```

This starts **Postgres**, **fleet-server** (gRPC 50051), **telemetry** (HTTP 9000), and **gateway** (HTTP 8000) in separate containers. They use the Compose network (e.g. `gateway:8000`, `telemetry:9000`, `fleet-server:50051`, `db:5432` inside the network).

- **Gateway**: http://localhost:8000 (e.g. `curl http://localhost:8000/health`)
- **Telemetry**: http://localhost:9000 (e.g. `curl http://localhost:9000/healthz`)
- **Fleet gRPC**: localhost:50051 (for CLI/scripts)
- **DB**: Postgres is reachable from the **host** at **localhost:5433** (maps to `5432` in the container). Data uses the persistent Docker volume `db_data`.

Run the **frontend** on the host for dev: `cd services/dashboard-web && npm install && npm run dev`, then open http://localhost:5173 (proxies to the gateway on port 8000).

---

## Importing existing data into the Docker Postgres (one-time)

The containerized Postgres uses a **persistent Docker volume** (`db_data`). Data survives container restarts. It starts empty until you migrate or import.

To import from a Postgres instance on your **host** (typical bare-metal port **5432**) into the **Compose** database (**5433** on the host):

```bash
# 1. Make sure the db container is running
docker compose up db -d

# 2. Export from your HOST Postgres (adjust user/db to match your local instance)
pg_dump -h localhost -p 5432 -U YOUR_HOST_USER -d agent_fleet > /tmp/agent_fleet_dump.sql

# 3. Import into the CONTAINER Postgres (agent_user @ host port 5433)
psql -h localhost -p 5433 -U agent_user -d agent_fleet < /tmp/agent_fleet_dump.sql
#    Password: from .env (AGENT_FLEET_POSTGRES_PASSWORD)

# 4. Verify
psql -h localhost -p 5433 -U agent_user -d agent_fleet -c "SELECT COUNT(*) FROM goals;"
```

After this, the container DB holds the imported data, and changes persist in the `db_data` volume.

**To completely reset the container DB** (start fresh):

```bash
docker compose down -v   # -v removes volumes
docker compose up --build
```

---

## What to test end-to-end

- **DB**: Compose starts Postgres; fleet-server and gateway connect to it. No extra setup if you use the built-in `db` service.
- **Fleet server**: gRPC on 50051. From the host you can use the CLI: `agentctl world list`, `agentctl agents list`, etc. (requires `pip install -e .`; point at `localhost:50051` or use gateway-backed flows as appropriate.)
- **Telemetry service**: HTTP on 9000. Agents (or scripts) POST heartbeats here; the gateway queries for health.
- **Gateway**: HTTP on 8000. Try:
  - `curl -s http://localhost:8000/health`
  - `curl -s http://localhost:8000/api/agents`
  - `curl -s http://localhost:8000/api/agents/health/all`
  - `curl -s http://localhost:8000/api/goals`
- **Event-driven updates**: Create/update a goal or plan via API or CLI; the fleet server notifies the gateway, which pushes over WebSocket. With the frontend open on the host, you should see updates without polling.
- **Heartbeat flow (agents → telemetry → gateway → UI)**:
  1. Send a heartbeat to Telemetry:

     ```bash
     curl -X POST http://localhost:9000/ingest/heartbeat \
       -H "Content-Type: application/json" \
       -d '{"agent_id":"fake1","reachable":true}'
     ```

  2. Verify Telemetry stored it:

     ```bash
     curl http://localhost:9000/health/summary
     ```

  3. Verify Gateway reads from Telemetry:

     ```bash
     curl http://localhost:8000/api/agents/health/all
     ```

  4. If effective reachable changes (e.g. first heartbeat or timeout), Telemetry pushes `telemetry.health_changed` to the gateway, which pushes over WebSocket. The frontend reacts without polling.

---

## Live reload with Docker

- **Frontend**: Run it on the host (`npm run dev`). UI edits live-reload. The frontend does **not** need to be in Docker for dev.
- **Gateway / fleet-server / telemetry in Docker**: By default, code is baked into the image. A code change requires `docker compose up --build` (rebuild + restart).

To keep **gateway** and **telemetry** live reload while still using Compose for Postgres and all services:

```bash
docker compose -f compose/docker-compose.platform.generated.yml -f compose/docker-compose.dev.yml up --build
```

- **Gateway**: `./services/gateway/src` and `./packages` are mounted read-only; the container runs `uvicorn ... --reload`, so edits there apply without rebuilding the image.
- **Telemetry**: `./services/telemetry/src` is mounted read-only; the container runs `uvicorn services.telemetry.src.main:app ... --reload` for the same behavior.
- **Fleet-server**: `./services/fleet_server/src` and `./packages` are mounted read-only; **restart** the `fleet-server` container to pick up Python changes (no image rebuild needed).
- **Frontend**: Still run on the host; the app talks to `http://localhost:8000` via the Vite proxy. No container needed for local UI dev.

**Does the frontend need to be Dockerized?** For local dev, no—running `npm run dev` on the host keeps UI live reload and is simplest. For production you can serve the built static bundle from a container or a CDN later if you want.
