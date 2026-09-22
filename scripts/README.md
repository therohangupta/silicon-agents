# scripts

Operator and maintainer **utilities** — short-lived processes, not fleet services. Run Python entrypoints from **repo root** (repository path to the package root) so **`domains.*`** and **`packages.*`** import without extra **`PYTHONPATH`** hacks. Shell scripts resolve **repo root** relative to their own location.

Skip **`db_backups/`** when browsing source: that tree holds generated SQL dumps, not maintained scripts.

---

## Primary workflows

### Local stack bring-up — `startup.sh`

End-to-end dev startup:

1. **Platform Compose** (`docker-compose.yml`) — Postgres, fleet-server, gateway, telemetry, NATS, memory-plane stores (OpenSearch, etc.)
2. **Agent Compose project** `silicon-agents` (`docker-compose.agents.yml`) — service list **generated** from the fleet YAML you pass
3. **Dashboard** Vite dev server on the host (`http://127.0.0.1:5173`) if not already listening

```bash
# From repo root
./scripts/startup.sh fleets/frontend.yaml
./scripts/startup.sh fleets/architecture.yaml --build
```

Fleet files live under **`fleets/`**; see [`../fleets/README.md`](../fleets/README.md).

### Fleet selection CLI — `fleet_select.py`

Wrapper around **`domains.eda.fleet`**:

| Subcommand | Output |
|------------|--------|
| **`render`** | Write Compose file for selected agents |
| **`count`** | Number of agents in the fleet |
| **`names`** | `agent_id\thost_port` lines |
| **`wait`** | Poll each agent **`/health`** until healthy or timeout |

Used by **`startup.sh`**, tests (**`tests/test_fleet_select.py`**), and manual debugging.

### Catalog validation — `check_agents.py`

Calls **`domains.eda.registry.validate_catalog()`** then prints **`len(all_specs())`**. Use in CI or before rendering Compose to catch incomplete agent directories (missing tools, bad context policy, Dockerfile drift).

### Platform compose render — `render_platform_compose.py`

Renders the platform **`docker-compose.yml`** (or fragments) from **`config/platform.yaml`**. Run when platform ports, images, or service list change in config rather than editing generated YAML by hand.

### gRPC stub generation — `grpc_gen.sh`

Regenerates Python gRPC stubs from **`.proto`** files under **`packages/proto`**. Run after protobuf contract changes before committing generated code.

### Host Postgres backup — `backup_db.sh`

Host-side **`pg_dump`** using connection settings from **`packages.config`**. Prefer **`database_mgmt/`** when Postgres runs inside Compose and host/client version skew is a problem.

---

## Subdirectories

| Path | README | Role |
|------|--------|------|
| [`database_mgmt/`](database_mgmt/README.md) | Backup/restore via **`docker compose exec`** into the **`db`** service |
| [`agents/`](agents/README.md) | Legacy demo-agent Docker helpers (removed; scripts exit with notice) |
| [`examples/`](examples/README.md) | Legacy demo population (removed; use catalog registration) |

---

## Environment and cwd conventions

| Script type | Working directory |
|-------------|-------------------|
| **`startup.sh`**, **`fleet_select.py`**, **`check_agents.py`** | Accept fleet paths relative to **repo root**; scripts normalize to absolute paths |
| Python utilities | Insert **repo root** on **`sys.path`** when run as files |
| **`database_mgmt/*.sh`** | Expect to be run from **repo root** so **`docker compose`** finds the project file |

---

## Testing hooks

Several scripts mirror assertions locked in pytest:

- **`fleet_select.py`** ↔ **`tests/test_fleet_select.py`**
- **`check_agents.py`** ↔ catalog tests in **`tests/test_silicon.py`**
- Live plane scripts require Compose + **`SILICON_PLANE_TEST=1`** (see [`../tests/README.md`](../tests/README.md))

---

## Related documentation

| Document | Topic |
|----------|--------|
| [`../docs/RUN.md`](../docs/RUN.md) | Runbook and failure modes |
| [`../domains/eda/fleet.py`](../domains/eda/fleet.py) | Selection and compose rendering implementation |
| [`../cli/README.md`](../cli/README.md) | **`agentctl`** operator CLI (fleet gRPC) |
