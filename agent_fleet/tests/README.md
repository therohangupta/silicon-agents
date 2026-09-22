# agent_fleet/tests

**Pytest** suite for fleet selection, EDA domain agents, engineering memory, context assembly, task lifecycle hooks, and (optionally) live Compose mesh smoke tests. Tests assume **`agent_fleet/`** is on **`PYTHONPATH`** (editable install or **`conftest.py`** path setup).

Run from **`agent_fleet/`**:

```bash
pytest tests/ -q
pytest tests/ -q -k "not memory_plane and not agent_mesh"   # skip live Docker tests
```

## Test modules (root)

| Module | What it locks in |
|--------|------------------|
| **`test_fleet_select.py`** | Fleet YAML parsing, **`select_agents`**, host port shifting, **`render_compose`** output |
| **`test_silicon.py`** | Catalog completeness, memory publish policy, **`EdaAgent`** handle path, **`AgentService`** wiring |
| **`test_task_lifecycle.py`** | SDK **`TaskLifecycle`** hook ordering with EDA overrides |
| **`test_context_assembly.py`** | Generic **`packages.memory.context.assemble`** precedence, conflicts, budgeting (domain-agnostic) |
| **`test_memory_plane.py`** | Live **`EngineeringMemory`** against multi-store plane |
| **`test_agent_mesh.py`** | Running Compose agents invoke each other's HTTP execute paths |

### Live / Docker-gated tests

**`test_memory_plane.py`** and **`test_agent_mesh.py`** require:

- Environment: **`SILICON_PLANE_TEST=1`**
- Platform + agent Compose stacks healthy (see **`docs/RUN.md`**)

Without the flag, these modules skip or no-op so CI and laptop unit runs stay fast.

## Shared fixtures — `conftest.py`

Centralizes path setup, optional async markers, and shared memory backends for silicon tests. Read **`conftest.py`** before adding new fixtures to avoid duplicating **`open_memory`** or catalog load logic.

## Contract subdirectory

Offline (or **`TestClient`**) contracts live under **`tests/contract/`** — package layout, gateway config, embodiment scan, plan workspace, codegen skills. See [`contract/README.md`](contract/README.md).

Contract tests intentionally **do not** require full Compose except where a module spins up an in-process app.

## What unit tests cover vs integration

| Layer | Typical test home |
|-------|-------------------|
| Pydantic schemas, enums | Implicit via domain tests; direct model tests when added |
| **`registry.validate_catalog`** | **`test_silicon.py`**, **`check_agents.py`** in CI |
| **`ContextService` + INCLUDE_TYPES** | **`test_silicon.py`**, **`test_context_assembly.py`** |
| **`fleet_select.py` CLI** | **`test_fleet_select.py`** |
| HTTP agent health/execute | **`contract/test_agent_package.py`** |

## CI recommendations

1. Always run: **`pytest tests/ -q`** with live tests skipped by default.
2. Nightly or manual job: export **`SILICON_PLANE_TEST=1`**, run **`startup.sh`** with a small fleet, then full **`tests/`**.
3. Gate merges on **`python scripts/check_agents.py`** plus contract suite.

## Adding tests

- Prefer injecting **`EngineeringMemory`** / **`ContextService`** into **`EdaAgent`** rather than hitting Docker.
- For new catalog agents, extend parametrized contract tests rather than one-off scripts.
- Mark long-running tests clearly; do not fold plane mesh into default CI without skip guards.

## Related documentation

| Document | Topic |
|----------|--------|
| [`../domains/eda/README.md`](../domains/eda/README.md) | **`EdaAgent`** and memory behavior under test |
| [`../scripts/README.md`](../scripts/README.md) | Scripts mirrored by fleet tests |
| [`../docs/RUN.md`](../docs/RUN.md) | Compose bring-up for live tests |

## Environment variables (quick reference)

| Variable | Effect |
|----------|--------|
| **`SILICON_PLANE_TEST=1`** | Enable live memory plane and agent mesh modules |
| **`MEMORY_BACKEND`** / **`SILICON_MEMORY_BACKEND`** | Override store selection in tests that call **`open_memory()`** |

## Debugging failed silicon tests

1. Run the single failing file with **`pytest -vv`** and no xdist.
2. For catalog failures, run **`python scripts/check_agents.py`** — error messages often match **`test_silicon.py`** assertions.
3. For fleet render diffs, compare **`fleet_select.py render`** output to committed **`docker-compose.agents.yml`** expectations in **`test_fleet_select.py`**.
4. For plane tests, confirm OpenSearch/Postgres/NATS containers are healthy before blaming agent code.
