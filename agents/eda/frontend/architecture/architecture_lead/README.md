# Architecture Lead (`architecture_lead`)

This directory is the deployable microservice package for the **Architecture Lead** in the fleet **architecture** stage (role `lead`).

## EDA responsibility

Architecture Lead — agent class entry point.

Charter from `config.yaml`: Own decomposition and high-level tradeoffs. Select a qualified architecture revision with block budgets, not an informal conclusion.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `architecture_lead` |
| Stage | `architecture` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8203** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read requirements and workload evidence
- Publish an architecture workflow
- Request a human decision when two feasible architectures remain

### May not

- Write RTL or a physical database
- Treat a model projection as a measured result
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `publish_architecture_plan` | `create_workflow` | `publish_architecture_plan` | Emit the workflow that produces one architecture revision. |
| `request_block_decomposition` | `create_workflow` | `request_block_decomposition` | Ask the decomposition work to divide the chip into blocks and interfaces. |
| `request_performance_study` | `create_workflow` | `request_performance_study` | Open a performance-modeling task for one workload. |
| `request_interface_definition` | `create_workflow` | `request_interface_definition` | Open an interface-contract task between two blocks. |
| `compare_architectures` | `read_reports` | `compare_architectures` | Rank architecture candidates against requirements and budgets. |
| `read_block_budgets` | `read_reports` | `read_block_budgets` | Read latency, bandwidth, power, and area budgets per block. |
| `read_requirement_coverage` | `read_reports` | `read_requirement_coverage` | Read which requirements each architecture candidate claims to meet. |
| `list_open_tradeoffs` | `read_reports` | `list_open_tradeoffs` | List architecture choices that are still unresolved. |
| `recommend_architecture_revision` | `publish_finding` | `recommend_architecture_revision` | Record which candidate should become the qualified architecture revision. |
| `publish_block_budget` | `publish_finding` | `publish_block_budget` | Publish a proposed budget for one block. A human still owns the requirement. |
| `flag_infeasible_partition` | `publish_finding` | `flag_infeasible_partition` | Publish evidence that a proposed hierarchy cannot meet a hard budget. |
| `request_architecture_decision` | `request_human_decision` | `request_architecture_decision` | Escalate an unresolved architecture tradeoff. |

## Delegation

This lead may open child workflows/tasks against:

- [`requirements`](../requirements/) — Requirements Agent (port **8202**)
- [`performance_modeling`](../performance_modeling/) — Performance Modeling Agent (port **8204**)
- [`interface`](../interface/) — Interface Agent (port **8205**)
- [`power_area_estimation`](../power_area_estimation/) — Power/Area Estimation Agent (port **8206**)
- [`security_reliability`](../security_reliability/) — Security/Reliability Agent (port **8207**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/architecture_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ArchitectureLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ArchitectureLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`interface`](../interface/) — worker, port **8205**
  - [`performance_modeling`](../performance_modeling/) — worker, port **8204**
  - [`power_area_estimation`](../power_area_estimation/) — worker, port **8206**
  - [`requirements`](../requirements/) — worker, port **8202**
  - [`security_reliability`](../security_reliability/) — worker, port **8207**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ArchitectureLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8203`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ArchitectureLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `publish_architecture_plan` (`tools.publish_architecture_plan`)

**Action:** `create_workflow`. Emit the workflow that produces one architecture revision.

### `request_block_decomposition` (`tools.request_block_decomposition`)

**Action:** `create_workflow`. Ask the decomposition work to divide the chip into blocks and interfaces.

### `request_performance_study` (`tools.request_performance_study`)

**Action:** `create_workflow`. Open a performance-modeling task for one workload.

### `request_interface_definition` (`tools.request_interface_definition`)

**Action:** `create_workflow`. Open an interface-contract task between two blocks.

### `compare_architectures` (`tools.compare_architectures`)

**Action:** `read_reports`. Rank architecture candidates against requirements and budgets.

### `read_block_budgets` (`tools.read_block_budgets`)

**Action:** `read_reports`. Read latency, bandwidth, power, and area budgets per block.

### `read_requirement_coverage` (`tools.read_requirement_coverage`)

**Action:** `read_reports`. Read which requirements each architecture candidate claims to meet.

### `list_open_tradeoffs` (`tools.list_open_tradeoffs`)

**Action:** `read_reports`. List architecture choices that are still unresolved.

### `recommend_architecture_revision` (`tools.recommend_architecture_revision`)

**Action:** `publish_finding`. Record which candidate should become the qualified architecture revision.

### `publish_block_budget` (`tools.publish_block_budget`)

**Action:** `publish_finding`. Publish a proposed budget for one block. A human still owns the requirement.

### `flag_infeasible_partition` (`tools.flag_infeasible_partition`)

**Action:** `publish_finding`. Publish evidence that a proposed hierarchy cannot meet a hard budget.

### `request_architecture_decision` (`tools.request_architecture_decision`)

**Action:** `request_human_decision`. Escalate an unresolved architecture tradeoff.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `human_intent`, `requirements`, `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
- **Context exclude:** `stale_candidates`.
- **Token budget:** 80000.
- **Telemetry:** heartbeat every 5s; streams: skill_calls, artifacts.

## Operational notes

- **Promotion / signoff:** Boundaries forbid treating this agent's summary as independent signoff unless `role: validator` and the workflow explicitly schedules it.
- **Adapters:** Set `EDA_FRAMEWORK` / `backend.type` when wiring OpenROAD, Yosys, OpenSTA, simulators, or licensed signoff tools; until then skills return structured `not_run` observations.
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
