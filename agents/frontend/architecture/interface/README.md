# Interface Agent (`interface`)

This directory is the deployable microservice package for the **Interface Agent** in the fleet **architecture** stage (role `worker`).

## EDA responsibility

Interface Agent — agent class entry point.

Charter from `config.yaml`: Define inter-block protocols and contracts, including the assertions those contracts imply.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `interface` |
| Stage | `architecture` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8205** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read block boundaries and requirements
- Write an interface contract into an isolated candidate

### May not

- Change block ownership
- Weaken a protocol to hide a failed assertion
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `define_interface_contract` | `write_candidate` | `define_interface_contract` | Write the signals, ordering, and error behavior for one interface. |
| `define_signal_list` | `write_candidate` | `define_signal_list` | Write names, widths, directions, and reset values for one interface. |
| `define_ordering_rules` | `write_candidate` | `define_ordering_rules` | Write legal transaction ordering and outstanding-count rules. |
| `define_error_behavior` | `write_candidate` | `define_error_behavior` | Write how the interface reports and recovers from an error. |
| `define_performance_contract` | `write_candidate` | `define_performance_contract` | Write bandwidth, latency, and backpressure obligations. |
| `generate_interface_assertions` | `write_candidate` | `generate_interface_assertions` | Draft assertions that check this interface contract, not general block properties. |
| `generate_interface_coverpoints` | `write_candidate` | `generate_interface_coverpoints` | Draft coverpoints for the legal and illegal transactions of this interface. |
| `revise_interface_draft` | `write_candidate` | `revise_interface_draft` | Edit a draft contract that has not been qualified. |
| `read_interface_contract` | `read_reports` | `read_interface_contract` | Read the current contract for one interface. |
| `diff_interface_revisions` | `read_reports` | `diff_interface_revisions` | Show what changed between two contract revisions. |
| `check_contract_against_ports` | `read_reports` | `check_contract_against_ports` | Compare the contract signal list with the RTL or netlist ports. |
| `flag_protocol_conflict` | `publish_finding` | `flag_protocol_conflict` | Publish a contract clause that contradicts a requirement or another interface. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/interface:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `InterfaceAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, InterfaceAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Stage lead(s) that delegate here:
  - [`architecture_lead`](../architecture_lead/) (port **8203**)
- Sibling agents in this folder:
  - [`architecture_lead`](../architecture_lead/) — lead, port **8203**
  - [`performance_modeling`](../performance_modeling/) — worker, port **8204**
  - [`power_area_estimation`](../power_area_estimation/) — worker, port **8206**
  - [`requirements`](../requirements/) — worker, port **8202**
  - [`security_reliability`](../security_reliability/) — worker, port **8207**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `InterfaceAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8205`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `InterfaceAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `define_interface_contract` (`tools.define_interface_contract`)

**Action:** `write_candidate`. Write the signals, ordering, and error behavior for one interface.

### `define_signal_list` (`tools.define_signal_list`)

**Action:** `write_candidate`. Write names, widths, directions, and reset values for one interface.

### `define_ordering_rules` (`tools.define_ordering_rules`)

**Action:** `write_candidate`. Write legal transaction ordering and outstanding-count rules.

### `define_error_behavior` (`tools.define_error_behavior`)

**Action:** `write_candidate`. Write how the interface reports and recovers from an error.

### `define_performance_contract` (`tools.define_performance_contract`)

**Action:** `write_candidate`. Write bandwidth, latency, and backpressure obligations.

### `generate_interface_assertions` (`tools.generate_interface_assertions`)

**Action:** `write_candidate`. Draft assertions that check this interface contract, not general block properties.

### `generate_interface_coverpoints` (`tools.generate_interface_coverpoints`)

**Action:** `write_candidate`. Draft coverpoints for the legal and illegal transactions of this interface.

### `revise_interface_draft` (`tools.revise_interface_draft`)

**Action:** `write_candidate`. Edit a draft contract that has not been qualified.

### `read_interface_contract` (`tools.read_interface_contract`)

**Action:** `read_reports`. Read the current contract for one interface.

### `diff_interface_revisions` (`tools.diff_interface_revisions`)

**Action:** `read_reports`. Show what changed between two contract revisions.

### `check_contract_against_ports` (`tools.check_contract_against_ports`)

**Action:** `read_reports`. Compare the contract signal list with the RTL or netlist ports.

### `flag_protocol_conflict` (`tools.flag_protocol_conflict`)

**Action:** `publish_finding`. Publish a contract clause that contradicts a requirement or another interface.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `human_intent`, `requirements`, `interface_contracts`, `decisions`, `open_findings`.
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
