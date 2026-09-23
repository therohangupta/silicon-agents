# Legacy physical demo agent Docker helpers

These shell scripts previously built and ran **physical demo** agent containers that lived outside the current EDA registry under **`agents/`**. Those packages were removed during the silicon registry migration.

## Current behavior

Each script now **exits immediately** with a removal notice pointing operators to supported paths:

| Script | Historical role |
|--------|-----------------|
| **`rebuild_examples_docker.sh`** | Rebuild demo agent images |
| **`run_examples_docker.sh`** | Run demo agents in Docker |
| **`run_examples_docker_dev.sh`** | Dev-mode bind mounts for demos |

Do not extend these files for new work — they remain only so old docs/links fail loudly instead of silently doing the wrong thing.

## Supported replacement workflow

Build and run **registered agents** instead:

1. Pick an agent directory, e.g. **`agents/frontend/architecture/requirements/`**
2. Use that directory's **`Dockerfile`**, or the shared **`services/silicon_agent`** image pattern documented under **`agents/`**
3. Select the agent via **fleet YAML** and **`scripts/startup.sh`**, or render a one-off Compose file with **`scripts/fleet_select.py render`**

Registration with the fleet manager (when not using Compose-only dev):

```bash
# From  after editable install
agentctl register agents/frontend/architecture/requirements/config.yaml
```

See [`../../cli/README.md`](../../cli/README.md) and [`../../agents/README.md`](../../agents/README.md).

## Why demos were removed

The fleet now treats **`agents/**/config.yaml`** as the single registry source of truth (**`domains.eda.fleet.registry`**). Parallel “example” trees duplicated validation rules, ports, and memory policy. Consolidating on registered agents keeps **`check_agents.py`**, contract tests, and gateway embodiment scans aligned.

## Related

| Path | Topic |
|------|--------|
| [`../examples/README.md`](../examples/README.md) | Legacy population script (also removed) |
| [`../README.md`](../README.md) | Current maintainer scripts index |
| [`../../fleets/README.md`](../../fleets/README.md) | Fleet YAML format |

## Historical context (for archaeologists)

The removed demo agents predated **`domains.eda.fleet.registry`** as the registry authority. They used ad hoc image tags and registration scripts in this folder, which caused port collisions with **`config/platform.yaml`** reserved ports and split memory policy between “demo” and “registry” trees.

If you find external docs referencing **`run_examples_docker.sh`**, update them to **`startup.sh`** + fleet YAML. Do not restore the old scripts without reintroducing the full demo tree — contract tests will fail on embodiment and package layout.

## Docker build flags today

Use **`startup.sh ... --build`** when Dockerfiles or base images change. Individual agent Dockerfiles live next to each registered agent; the platform image for **`services/silicon_agent`** (when used) is documented under **`agents/`**.

Port publishing respects **`config/platform.yaml`** **`host_port_collision_offset`** — demo scripts did not, which was a common source of “agent up but unreachable on expected localhost port” confusion.

## Mapping old workflows to registry paths

| Old mental model | Current equivalent |
|------------------|-------------------|
| “Rebuild all example images” | **`startup.sh <fleet.yaml> --build`** |
| “Run examples in dev mode” | Mount agent source via Compose working_dir prefix in **`platform.yaml`** |
| “Pick three random agents” | Edit **`fleets/*.yaml`** **`agents:`** list explicitly |

Each registered agent exposes **`connection.port`** in **`config.yaml`**; **`domains.eda.fleet.select_agents`** assigns **`host_port`** after reserved-port shifting. Use **`scripts/fleet_select.py names`** to print the mapping when debugging local curls.

## Contact / ownership

There is no separate “examples team” for this folder anymore. Questions about running agents belong with **`agents/`** maintainers and the runbook in **`docs/RUN.md`**. Leave these stub scripts untouched unless product direction explicitly reintroduces a second agent tree (unlikely).

## Files in this directory

| File | Behavior |
|------|----------|
| **`rebuild_examples_docker.sh`** | Prints removal notice; exit non-zero |
| **`run_examples_docker.sh`** | Prints removal notice; exit non-zero |
| **`run_examples_docker_dev.sh`** | Prints removal notice; exit non-zero |
| **`README.md`** | Migration guide (this document) |

If a script here ever runs Docker again, it should be moved out of **`scripts/agents/`** and documented in **`scripts/README.md`** as a supported maintainer tool — not hidden among legacy stubs.
