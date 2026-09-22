# Cross-Partition Boundary Coordinator (`boundary_coordinator`)

This directory is the deployable microservice package for the **Cross-Partition Boundary Coordinator** in the fleet **placement** stage (role `worker`).

## EDA responsibility

Tools for the Cross-Partition Boundary Coordinator.

Charter from `config.yaml`: Check timing budgets, interface pins, feedthroughs, routing channels, power continuity, clock interactions, and constraint consistency across partitions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `boundary_coordinator` |
| Stage | `placement` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8246** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read both partitions' boundaries
- Write a proposed budget or feedthrough change as a proposal
- Publish a boundary finding

### May not

- Edit either partition's placement
- Change a timing budget on the canonical constraint set
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_partition_boundaries` | `read_reports` | `read_partition_boundaries` | Read pins, channels, and abstracts for the partitions in scope. |
| `check_timing_budgets` | `read_reports` | `check_timing_budgets` | Compare interface timing budgets across partitions. |
| `check_feedthroughs` | `read_reports` | `check_feedthroughs` | Check feedthroughs, channels, and reserved routing tracks. |
| `check_power_continuity` | `read_reports` | `check_power_continuity` | Check that supplies continue across the partition boundary. |
| `check_clock_boundary` | `read_reports` | `check_clock_boundary` | Check clock handoff, skew budget, and generated clocks at the boundary. |
| `check_constraint_consistency` | `read_reports` | `check_constraint_consistency` | Check that both partitions use the same interface exceptions. |
| `check_pin_agreement` | `read_reports` | `check_pin_agreement` | Check that mating pins share layer, order, and location. |
| `write_budget_proposal` | `write_candidate` | `write_budget_proposal` | Write a proposed timing-budget change. This does not edit the canonical constraints. |
| `write_feedthrough_proposal` | `write_candidate` | `write_feedthrough_proposal` | Write a proposed feedthrough. This does not edit either placement. |
| `flag_budget_mismatch` | `publish_finding` | `flag_budget_mismatch` | Publish interface budgets that do not add up. |
| `flag_feedthrough_conflict` | `publish_finding` | `flag_feedthrough_conflict` | Publish a feedthrough that collides with a channel or pin. |
| `flag_power_discontinuity` | `publish_finding` | `flag_power_discontinuity` | Publish a supply that stops at the boundary. |
| `record_boundary_evidence` | `publish_finding` | `record_boundary_evidence` | Record both partition refs and the reports compared. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/boundary_coordinator:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `BoundaryCoordinatorAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, BoundaryCoordinatorAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (placement specialists under `placement/`).
- Stage lead(s) that delegate here:
  - [`placement_lead`](../placement_lead/) (port **8243**)
- Sibling agents in this folder:
  - [`placement_evaluator`](../placement_evaluator/) — validator, port **8245**
  - [`placement_experiment`](../placement_experiment/) — worker, port **8244**
  - [`placement_lead`](../placement_lead/) — lead, port **8243**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `BoundaryCoordinatorAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8246`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `BoundaryCoordinatorAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_partition_boundaries` (`tools.read_partition_boundaries`)

**Action:** `read_reports`. Read pins, channels, and abstracts for the partitions in scope.

Read pins, channels, and abstracts for partitions in scope.

### `check_timing_budgets` (`tools.check_timing_budgets`)

**Action:** `read_reports`. Compare interface timing budgets across partitions.

Compare interface timing budgets so partitions do not oversubscribe slack.

### `check_feedthroughs` (`tools.check_feedthroughs`)

**Action:** `read_reports`. Check feedthroughs, channels, and reserved routing tracks.

Check feedthrough nets, channels, and reserved routing tracks.

### `check_power_continuity` (`tools.check_power_continuity`)

**Action:** `read_reports`. Check that supplies continue across the partition boundary.

Check that power/ground straps continue across the partition cut.

### `check_clock_boundary` (`tools.check_clock_boundary`)

**Action:** `read_reports`. Check clock handoff, skew budget, and generated clocks at the boundary.

### `check_constraint_consistency` (`tools.check_constraint_consistency`)

**Action:** `read_reports`. Check that both partitions use the same interface exceptions.

Check both partitions share the same interface exceptions.

### `check_pin_agreement` (`tools.check_pin_agreement`)

**Action:** `read_reports`. Check that mating pins share layer, order, and location.

Check mating pins share layer, order, and location.

### `write_budget_proposal` (`tools.write_budget_proposal`)

**Action:** `write_candidate`. Write a proposed timing-budget change. This does not edit the canonical constraints.

Write a proposed timing-budget change (does not edit canonical SDC).

### `write_feedthrough_proposal` (`tools.write_feedthrough_proposal`)

**Action:** `write_candidate`. Write a proposed feedthrough. This does not edit either placement.

Write a proposed feedthrough (does not edit either placement).

### `flag_budget_mismatch` (`tools.flag_budget_mismatch`)

**Action:** `publish_finding`. Publish interface budgets that do not add up.

Finding: interface budgets do not add up across partitions.

### `flag_feedthrough_conflict` (`tools.flag_feedthrough_conflict`)

**Action:** `publish_finding`. Publish a feedthrough that collides with a channel or pin.

Finding: a feedthrough collides with a channel or pin.

### `flag_power_discontinuity` (`tools.flag_power_discontinuity`)

**Action:** `publish_finding`. Publish a supply that stops at the boundary.

Finding: a supply stops at the partition boundary.

### `record_boundary_evidence` (`tools.record_boundary_evidence`)

**Action:** `publish_finding`. Record both partition refs and the reports compared.

Record both partition refs and compared reports.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `canonical_source`, `open_findings`, `experiments`, `gates`, `decisions`.
- **Context exclude:** `stale_candidates`.
- **Token budget:** 80000.
- **Telemetry:** heartbeat every 5s; streams: skill_calls, artifacts.

## Operational notes

- **Promotion / signoff:** Boundaries forbid treating this agent's summary as independent signoff unless `role: validator` and the workflow explicitly schedules it.
- **Adapters:** Set `EDA_FRAMEWORK` / `backend.type` when wiring OpenROAD, Yosys, OpenSTA, simulators, or licensed signoff tools; until then skills return structured `not_run` observations.
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
