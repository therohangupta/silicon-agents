# Synthesis Lead (`synthesis_lead`)

This directory is the deployable microservice package for the **Synthesis Lead** in the fleet **synthesis** stage (role `lead`).

## EDA responsibility

Emit the synthesis and equivalence workflow.

Charter from `config.yaml`: Own the RTL-to-netlist workflow. Define synthesis experiments and acceptance criteria, and recommend candidates that satisfy functional and PPA requirements.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `synthesis_lead` |
| Stage | `synthesis` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8232** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a synthesis workflow
- Read RTL, constraints, and QoR reports
- Request a human decision when two netlists remain feasible

### May not

- Accept a netlist that failed equivalence
- Relax a constraint to improve WNS
- Promote a netlist onto the baseline
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_synthesis_experiments` | `create_workflow` | `plan_synthesis_experiments` | Emit the synthesis and equivalence workflow. |
| `request_constraint_audit` | `create_workflow` | `request_constraint_audit` | Open constraint generation and audit before experiments run. |
| `request_synthesis_experiment` | `create_workflow` | `request_synthesis_experiment` | Open one isolated synthesis experiment with a named hypothesis. |
| `request_retiming_study` | `create_workflow` | `request_retiming_study` | Open a state-preserving retiming or mapping study. |
| `request_equivalence_check` | `create_workflow` | `request_equivalence_check` | Open equivalence between the RTL and a netlist candidate. |
| `request_netlist_quality_audit` | `create_workflow` | `request_netlist_quality_audit` | Open a structural quality audit of one netlist. |
| `read_synthesis_acceptance` | `read_reports` | `read_synthesis_acceptance` | Read the PPA and equivalence criteria for this block. |
| `read_experiment_qor` | `read_reports` | `read_experiment_qor` | Read QoR for every experiment against the same baseline. |
| `read_equivalence_status` | `read_reports` | `read_equivalence_status` | Read whether each netlist passed equivalence. |
| `compare_synthesis_candidates` | `read_reports` | `compare_synthesis_candidates` | Rank candidates on timing, area, power, and runtime. A failed equivalence check stays ineligible. |
| `recommend_netlist_candidate` | `publish_finding` | `recommend_netlist_candidate` | Record which experiment should advance, with its QoR and equivalence status. This does not promote it. |
| `flag_ineligible_netlist` | `publish_finding` | `flag_ineligible_netlist` | Publish a netlist that improved QoR and failed equivalence or a hard constraint. |
| `record_synthesis_strategy` | `publish_finding` | `record_synthesis_strategy` | Record which knobs the next experiment batch will change. |
| `request_netlist_decision` | `request_human_decision` | `request_netlist_decision` | Ask a human to choose among feasible netlists. |

## Delegation

This lead may open child workflows/tasks against:

- [`constraint_generation`](../constraint_generation/) — Constraint Generation and Validation Agent (port **8233**)
- [`synthesis_experiment`](../synthesis_experiment/) — Synthesis Experiment Worker (port **8234**)
- [`retiming_mapping`](../retiming_mapping/) — Retiming and Mapping Agent (port **8235**)
- [`equivalence`](../equivalence/) — Equivalence Agent (port **8236**)
- [`netlist_quality`](../netlist_quality/) — Netlist Quality Agent (port **8237**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/synthesis_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `SynthesisLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, SynthesisLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (synthesis specialists under `synthesis/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`constraint_generation`](../constraint_generation/) — worker, port **8233**
  - [`equivalence`](../equivalence/) — worker, port **8236**
  - [`netlist_quality`](../netlist_quality/) — worker, port **8237**
  - [`retiming_mapping`](../retiming_mapping/) — worker, port **8235**
  - [`synthesis_experiment`](../synthesis_experiment/) — worker, port **8234**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `SynthesisLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8232`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `SynthesisLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_synthesis_experiments` (`tools.plan_synthesis_experiments`)

**Action:** `create_workflow`. Emit the synthesis and equivalence workflow.

### `request_constraint_audit` (`tools.request_constraint_audit`)

**Action:** `create_workflow`. Open constraint generation and audit before experiments run.

### `request_synthesis_experiment` (`tools.request_synthesis_experiment`)

**Action:** `create_workflow`. Open one isolated synthesis experiment with a named hypothesis.

### `request_retiming_study` (`tools.request_retiming_study`)

**Action:** `create_workflow`. Open a state-preserving retiming or mapping study.

### `request_equivalence_check` (`tools.request_equivalence_check`)

**Action:** `create_workflow`. Open equivalence between the RTL and a netlist candidate.

### `request_netlist_quality_audit` (`tools.request_netlist_quality_audit`)

**Action:** `create_workflow`. Open a structural quality audit of one netlist.

### `read_synthesis_acceptance` (`tools.read_synthesis_acceptance`)

**Action:** `read_reports`. Read the PPA and equivalence criteria for this block.

### `read_experiment_qor` (`tools.read_experiment_qor`)

**Action:** `read_reports`. Read QoR for every experiment against the same baseline.

### `read_equivalence_status` (`tools.read_equivalence_status`)

**Action:** `read_reports`. Read whether each netlist passed equivalence.

### `compare_synthesis_candidates` (`tools.compare_synthesis_candidates`)

**Action:** `read_reports`. Rank candidates on timing, area, power, and runtime. A failed equivalence check stays ineligible.

### `recommend_netlist_candidate` (`tools.recommend_netlist_candidate`)

**Action:** `publish_finding`. Record which experiment should advance, with its QoR and equivalence status. This does not promote it.

### `flag_ineligible_netlist` (`tools.flag_ineligible_netlist`)

**Action:** `publish_finding`. Publish a netlist that improved QoR and failed equivalence or a hard constraint.

### `record_synthesis_strategy` (`tools.record_synthesis_strategy`)

**Action:** `publish_finding`. Record which knobs the next experiment batch will change.

### `request_netlist_decision` (`tools.request_netlist_decision`)

**Action:** `request_human_decision`. Ask a human to choose among feasible netlists.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
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
