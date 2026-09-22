# Contract tests

**Offline** (or in-process **`TestClient`**) contracts that agent packages, gateway scanners, codegen runtime, gRPC bridge config, and plan workspace must satisfy **without** a full Docker Compose stack. These tests catch structural drift early — missing Dockerfiles, broken health routes, wrong embodiment lists, invalid env expansion — before operators spend time on **`startup.sh`**.

Run:

```bash
cd agent_fleet
pytest tests/contract/ -q
```

## Design goals

| Goal | How contracts enforce it |
|------|---------------------------|
| Every catalog agent is runnable | Parametrized HTTP health + execute smoke |
| Gateway sees the right agents | Embodiment YAML scan matches silicon tree |
| Config/codegen path stays wired | Env expansion + skill execution |
| Plan artifacts resolve | **`ArtifactRef`** + workspace backend |
| Repo-wide hygiene | E2E audit over agent tree |

Failures should point to a **specific directory or config key**, not a generic integration timeout.

## Module reference

### test_agent_package.py

Parametrized over agent directories under **`agents/`**:

- Import/load agent package layout
- **`/health`** (or equivalent) responds
- **`execute`** / task path accepts SDK-shaped requests where applicable
- Telemetry adapter hooks present when required by platform config

This is the broadest contract — new agents should pass automatically once the catalog layout is correct.

### test_config_and_codegen.py

- Environment variable expansion in agent/platform config
- Codegen **skill** execution path (generated or template skills under SDK)

Guards against broken **`${VAR}`** patterns and stale codegen entrypoints.

### test_embodiment_scan.py

Gateway **embodiment scanner** reads YAML and lists **silicon** agents only (frontend/backend paths per product rules). Prevents dashboard/gateway from advertising removed demo agents or missing catalog entries.

### test_e2e_audit.py

Repo-wide audit:

- Agent tree shape vs validator expectations
- Required files per agent directory
- Cross-checks that complement **`registry.validate_catalog`**

Useful when refactoring directory conventions.

### test_grpc_bridge_config.py

Gateway configuration for **agentfleet/v1** connection and deployment metadata:

- Host/port or service names resolve
- Bridge settings consistent with **`config/platform.yaml`**

Catches gateway mispointing at fleet-server without starting gRPC.

### test_plan_workspace.py

**Plan workspace** stack:

- **`ArtifactRef`** serialization and fleet ref mapping
- **`LocalWorkspaceBackend`** read/write semantics
- **`PlanWorkspace`** higher-level API used by planners or tools

Ensures planning artifacts remain compatible with SDK workspace types.

## Relationship to `test_silicon.py`

| Suite | Focus |
|-------|--------|
| **`tests/test_silicon.py`** | Domain behavior — memory policy, **`EdaAgent`** outcomes |
| **`tests/contract/`** | Package and platform **shape** — files, routes, config, scans |

A change can pass silicon unit tests but fail contract tests if **`Dockerfile`** or **`server.py`** routing breaks.

## Relationship to live mesh tests

**`test_agent_mesh.py`** (parent **`tests/`**) requires Compose and **`SILICON_PLANE_TEST=1`**. Contract tests should fail **first** in CI when an agent cannot even serve health.

## Extending contracts

When adding a new global requirement (e.g. mandatory OpenTelemetry exporter config):

1. Add a focused test module or extend **`test_e2e_audit.py`** with a clear error message.
2. Avoid duplicating full **`EdaAgent`** execution — keep contracts fast.
3. Parametrize over **`all_specs()`** or filesystem globs consistent with **`registry`**.

## Related documentation

| Document | Topic |
|----------|--------|
| [`../README.md`](../README.md) | Full test suite layout |
| [`../../agents/README.md`](../../agents/README.md) | Agent directory contract |
| [`../../docs/GATEWAY_VS_TELEMETRY_SPLIT.md`](../../docs/GATEWAY_VS_TELEMETRY_SPLIT.md) | Gateway embodiment context |
| [`../../scripts/check_agents.py`](../../scripts/check_agents.py) | Catalog validator CLI |
