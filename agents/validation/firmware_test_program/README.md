# Firmware and Test-Program Agent (`firmware_test_program`)

This directory is the deployable microservice package for the **Firmware and Test-Program Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Firmware / Test Program agent class (firmware_test_program).

Charter from `config.yaml`: Draft and debug low-level firmware, diagnostics, boot flows, and test programs used to exercise silicon.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `firmware_test_program` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8266** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Edit firmware on an isolated branch
- Draft a test program
- Compile the firmware

### May not

- Flash a part
- Change bring-up limits
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `draft_firmware_change` | `write_candidate` | `draft_firmware_change` | Write one bounded firmware or diagnostic change. |
| `write_boot_flow` | `write_candidate` | `write_boot_flow` | Write or edit the boot sequence on the isolated branch. |
| `write_diagnostic` | `write_candidate` | `write_diagnostic` | Write one diagnostic that exercises a named block. |
| `draft_test_program` | `write_candidate` | `draft_test_program` | Write a characterization or production test program. |
| `write_test_limits` | `write_candidate` | `write_test_limits` | Write pass limits copied from the approved specification. This agent cannot widen them. |
| `write_test_pattern` | `write_candidate` | `write_test_pattern` | Write one pattern the test program applies. |
| `compile_firmware` | `submit_tool_job` | `compile_firmware` | Compile the firmware branch. |
| `compile_test_program` | `submit_tool_job` | `compile_test_program` | Compile the test program. |
| `read_firmware_diff` | `read_reports` | `read_firmware_diff` | Read the diff against the firmware baseline. |
| `flag_limit_widening` | `publish_finding` | `flag_limit_widening` | Publish a test program whose limits are looser than the approved specification. |
| `flag_firmware_without_diagnostic` | `publish_finding` | `flag_firmware_without_diagnostic` | Publish a change that has no way to observe the block it touches. |
| `record_firmware_revision` | `publish_finding` | `record_firmware_revision` | Record the firmware revision, compiler, and test program. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/firmware_test_program:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `FirmwareTestProgramAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, FirmwareTestProgramAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Stage lead(s) that delegate here:
  - [`bringup_lead`](../bringup_lead/) (port **8263**)
- Sibling agents in this folder:
  - [`bringup_lead`](../bringup_lead/) — lead, port **8263**
  - [`characterization`](../characterization/) — worker, port **8268**
  - [`errata_drafting`](../errata_drafting/) — worker, port **8270**
  - [`failure_correlation`](../failure_correlation/) — worker, port **8269**
  - [`instrument_control`](../instrument_control/) — worker, port **8265**
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `FirmwareTestProgramAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8266`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `FirmwareTestProgramAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `draft_firmware_change` (`tools.draft_firmware_change`)

**Action:** `write_candidate`. Write one bounded firmware or diagnostic change.

### `write_boot_flow` (`tools.write_boot_flow`)

**Action:** `write_candidate`. Write or edit the boot sequence on the isolated branch.

### `write_diagnostic` (`tools.write_diagnostic`)

**Action:** `write_candidate`. Write one diagnostic that exercises a named block.

### `draft_test_program` (`tools.draft_test_program`)

**Action:** `write_candidate`. Write a characterization or production test program.

### `write_test_limits` (`tools.write_test_limits`)

**Action:** `write_candidate`. Write pass limits copied from the approved specification. This agent cannot widen them.

### `write_test_pattern` (`tools.write_test_pattern`)

**Action:** `write_candidate`. Write one pattern the test program applies.

### `compile_firmware` (`tools.compile_firmware`)

**Action:** `submit_tool_job`. Compile the firmware branch.

### `compile_test_program` (`tools.compile_test_program`)

**Action:** `submit_tool_job`. Compile the test program.

### `read_firmware_diff` (`tools.read_firmware_diff`)

**Action:** `read_reports`. Read the diff against the firmware baseline.

### `flag_limit_widening` (`tools.flag_limit_widening`)

**Action:** `publish_finding`. Publish a test program whose limits are looser than the approved specification.

### `flag_firmware_without_diagnostic` (`tools.flag_firmware_without_diagnostic`)

**Action:** `publish_finding`. Publish a change that has no way to observe the block it touches.

### `record_firmware_revision` (`tools.record_firmware_revision`)

**Action:** `publish_finding`. Record the firmware revision, compiler, and test program.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `experiments`, `gates`, `decisions`, `open_findings`, `canonical_source`.
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
