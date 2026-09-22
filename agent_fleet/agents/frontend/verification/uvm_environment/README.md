# UVM Environment Agent (`uvm_environment`)

This directory is the deployable microservice package for the **UVM Environment Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

UVM Environment Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Generate and maintain drivers, monitors, scoreboards, and sequences for one block.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `uvm_environment` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8216** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write verification collateral on an isolated branch
- Read the interface contract
- Compile the environment and run a smoke test

### May not

- Edit the RTL under test
- Weaken the scoreboard to make a test pass
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `generate_uvm_environment` | `write_candidate` | `generate_uvm_environment` | Create the UVM environment package from the interface contract. |
| `write_uvm_driver` | `write_candidate` | `write_uvm_driver` | Write the driver for one interface. |
| `write_uvm_monitor` | `write_candidate` | `write_uvm_monitor` | Write the monitor for one interface. |
| `write_uvm_scoreboard` | `write_candidate` | `write_uvm_scoreboard` | Write the scoreboard that compares DUT outputs with the reference model. |
| `write_uvm_agent` | `write_candidate` | `write_uvm_agent` | Write the agent that binds driver, monitor, and sequencer. |
| `write_uvm_sequence_library` | `write_candidate` | `write_uvm_sequence_library` | Write the base sequence library for this block. |
| `write_uvm_config` | `write_candidate` | `write_uvm_config` | Write the configuration object and factory overrides. |
| `bind_uvm_interfaces` | `write_candidate` | `bind_uvm_interfaces` | Bind virtual interfaces to the DUT ports in the isolated branch. |
| `update_scoreboard` | `write_candidate` | `update_scoreboard` | Adjust the scoreboard for one clarified requirement. |
| `read_uvm_interface_contract` | `read_reports` | `read_uvm_interface_contract` | Read the interface contract this environment implements. |
| `compile_uvm_environment` | `submit_tool_job` | `compile_uvm_environment` | Compile the environment and the DUT in the isolated branch. |
| `run_uvm_smoke` | `submit_tool_job` | `run_uvm_smoke` | Run one smoke test and return the log. |
| `flag_scoreboard_gap` | `publish_finding` | `flag_scoreboard_gap` | Publish a requirement the scoreboard does not check. |
| `flag_protocol_monitor_mismatch` | `publish_finding` | `flag_protocol_monitor_mismatch` | Publish a monitor that does not implement a contract clause. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/uvm_environment:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `UvmEnvironmentAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, UvmEnvironmentAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that delegate here:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `UvmEnvironmentAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8216`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `UvmEnvironmentAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `generate_uvm_environment` (`tools.generate_uvm_environment`)

**Action:** `write_candidate`. Create the UVM environment package from the interface contract.

### `write_uvm_driver` (`tools.write_uvm_driver`)

**Action:** `write_candidate`. Write the driver for one interface.

### `write_uvm_monitor` (`tools.write_uvm_monitor`)

**Action:** `write_candidate`. Write the monitor for one interface.

### `write_uvm_scoreboard` (`tools.write_uvm_scoreboard`)

**Action:** `write_candidate`. Write the scoreboard that compares DUT outputs with the reference model.

### `write_uvm_agent` (`tools.write_uvm_agent`)

**Action:** `write_candidate`. Write the agent that binds driver, monitor, and sequencer.

### `write_uvm_sequence_library` (`tools.write_uvm_sequence_library`)

**Action:** `write_candidate`. Write the base sequence library for this block.

### `write_uvm_config` (`tools.write_uvm_config`)

**Action:** `write_candidate`. Write the configuration object and factory overrides.

### `bind_uvm_interfaces` (`tools.bind_uvm_interfaces`)

**Action:** `write_candidate`. Bind virtual interfaces to the DUT ports in the isolated branch.

### `update_scoreboard` (`tools.update_scoreboard`)

**Action:** `write_candidate`. Adjust the scoreboard for one clarified requirement.

### `read_uvm_interface_contract` (`tools.read_uvm_interface_contract`)

**Action:** `read_reports`. Read the interface contract this environment implements.

### `compile_uvm_environment` (`tools.compile_uvm_environment`)

**Action:** `submit_tool_job`. Compile the environment and the DUT in the isolated branch.

### `run_uvm_smoke` (`tools.run_uvm_smoke`)

**Action:** `submit_tool_job`. Run one smoke test and return the log.

### `flag_scoreboard_gap` (`tools.flag_scoreboard_gap`)

**Action:** `publish_finding`. Publish a requirement the scoreboard does not check.

### `flag_protocol_monitor_mismatch` (`tools.flag_protocol_monitor_mismatch`)

**Action:** `publish_finding`. Publish a monitor that does not implement a contract clause.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `open_findings`, `experiments`, `decisions`.
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
