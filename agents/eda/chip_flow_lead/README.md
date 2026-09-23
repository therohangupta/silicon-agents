# Chip Flow Lead (`chip_flow_lead`)

This directory is the deployable microservice package for the **Chip Flow Lead** in the fleet **program** stage (role `lead`).

## EDA responsibility

Chip Flow Lead agent class (chip_flow_lead).

Charter from `config.yaml`: Own the program plan from design intent through release. Keep milestone gates, route cross-stage findings backward, and revise the task graph when a stage reports that its strategy is invalid.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `chip_flow_lead` |
| Stage | `program` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8201** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read design intent and every stage's gate status
- Publish a program workflow that names stage leads and milestone order
- Request a human decision when a tradeoff exceeds delegated authority

### May not

- Edit RTL, constraints, or a physical database
- Mark a milestone passed without the stage's independent gate
- Drop a hard requirement to keep a schedule
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `revise_program_plan` | `create_workflow` | `revise_program_plan` | Publish a revised program workflow from current gate status and open findings. |
| `request_stage_replan` | `create_workflow` | `request_stage_replan` | Open a new workflow for one stage whose strategy has stalled. |
| `narrow_program_scope` | `create_workflow` | `narrow_program_scope` | Replace a broad objective with a smaller workflow the stage can finish. |
| `read_program_status` | `read_reports` | `read_program_status` | Read milestone status for every active stage. |
| `read_milestone_gates` | `read_reports` | `read_milestone_gates` | Read the latest gate decision for each milestone. |
| `list_open_findings` | `read_reports` | `list_open_findings` | List findings that no stage has closed. |
| `list_blocked_tasks` | `read_reports` | `list_blocked_tasks` | List tasks waiting on a dependency, license, or human decision. |
| `compare_experiment_history` | `read_reports` | `compare_experiment_history` | Compare prior experiments so the program does not repeat a dead end. |
| `check_program_budget` | `read_reports` | `check_program_budget` | Read remaining compute, license, and schedule budget. |
| `route_upstream_finding` | `publish_finding` | `route_upstream_finding` | Attach a downstream finding to the earliest stage that can change the cause. |
| `record_milestone_evidence` | `publish_finding` | `record_milestone_evidence` | Record the evidence bundle currently attached to a milestone. |
| `record_strategy_change` | `publish_finding` | `record_strategy_change` | Record an outer-loop change to how the program searches, without relaxing a hard requirement. |
| `request_program_decision` | `request_human_decision` | `request_program_decision` | Package a tradeoff that needs a human owner, with options and evidence. |
| `request_baseline_promotion` | `request_human_decision` | `request_baseline_promotion` | Ask a human to promote a candidate after the required gates have passed. |
| `request_waiver_decision` | `request_human_decision` | `request_waiver_decision` | Ask a named human to approve or reject a waiver. This agent cannot approve it. |

## Delegation

This lead may open child workflows/tasks against:

- [`requirements`](../frontend/architecture/requirements/) — Requirements Agent (port **8202**)
- [`architecture_lead`](../frontend/architecture/architecture_lead/) — Architecture Lead (port **8203**)
- [`rtl_lead`](../frontend/rtl/rtl_lead/) — RTL Lead (port **8208**)
- [`verification_lead`](../frontend/verification/verification_lead/) — Verification Lead (port **8215**)
- [`dft_lead`](../dft/dft_lead/) — DFT Lead (port **8225**)
- [`synthesis_lead`](../backend/synthesis/synthesis_lead/) — Synthesis Lead (port **8232**)
- [`floorplanning_lead`](../backend/floorplan/floorplanning_lead/) — Floorplanning Lead (port **8238**)
- [`placement_lead`](../backend/placement/placement_lead/) — Placement Lead (port **8243**)
- [`cts`](../backend/clock/cts/) — CTS Agent (port **8247**)
- [`clock_validation`](../backend/clock/clock_validation/) — Clock Validation Agent (port **8248**)
- [`routing_lead`](../backend/routing/routing_lead/) — Routing Lead (port **8249**)
- [`extraction`](../backend/signoff/extraction/) — Extraction Agent (port **8254**)
- [`sta_lead`](../backend/signoff/sta_lead/) — STA Lead (port **8255**)
- [`signoff_validator`](../backend/signoff/signoff_validator/) — Independent Signoff Validator (port **8262**)
- [`bringup_lead`](../validation/bringup_lead/) — Bring-Up Lead (port **8263**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

Independent validators configured for this agent:

- [`signoff_validator`](../backend/signoff/signoff_validator/) (port **8262**)

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/chip_flow_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ChipFlowLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ChipFlowLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (program specialists under `agents/`).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ChipFlowLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8201`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ChipFlowLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `revise_program_plan` (`tools.revise_program_plan`)

**Action:** `create_workflow`. Publish a revised program workflow from current gate status and open findings.

### `request_stage_replan` (`tools.request_stage_replan`)

**Action:** `create_workflow`. Open a new workflow for one stage whose strategy has stalled.

### `narrow_program_scope` (`tools.narrow_program_scope`)

**Action:** `create_workflow`. Replace a broad objective with a smaller workflow the stage can finish.

### `read_program_status` (`tools.read_program_status`)

**Action:** `read_reports`. Read milestone status for every active stage.

### `read_milestone_gates` (`tools.read_milestone_gates`)

**Action:** `read_reports`. Read the latest gate decision for each milestone.

### `list_open_findings` (`tools.list_open_findings`)

**Action:** `read_reports`. List findings that no stage has closed.

### `list_blocked_tasks` (`tools.list_blocked_tasks`)

**Action:** `read_reports`. List tasks waiting on a dependency, license, or human decision.

### `compare_experiment_history` (`tools.compare_experiment_history`)

**Action:** `read_reports`. Compare prior experiments so the program does not repeat a dead end.

### `check_program_budget` (`tools.check_program_budget`)

**Action:** `read_reports`. Read remaining compute, license, and schedule budget.

### `route_upstream_finding` (`tools.route_upstream_finding`)

**Action:** `publish_finding`. Attach a downstream finding to the earliest stage that can change the cause.

### `record_milestone_evidence` (`tools.record_milestone_evidence`)

**Action:** `publish_finding`. Record the evidence bundle currently attached to a milestone.

### `record_strategy_change` (`tools.record_strategy_change`)

**Action:** `publish_finding`. Record an outer-loop change to how the program searches, without relaxing a hard requirement.

### `request_program_decision` (`tools.request_program_decision`)

**Action:** `request_human_decision`. Package a tradeoff that needs a human owner, with options and evidence.

### `request_baseline_promotion` (`tools.request_baseline_promotion`)

**Action:** `request_human_decision`. Ask a human to promote a candidate after the required gates have passed.

### `request_waiver_decision` (`tools.request_waiver_decision`)

**Action:** `request_human_decision`. Ask a named human to approve or reject a waiver. This agent cannot approve it.

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
