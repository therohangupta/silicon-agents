# Clock Validation Agent (`clock_validation`)

This directory is the deployable microservice package for the **Clock Validation Agent** in the fleet **clock** stage (role `validator`).

## EDA responsibility

Independently analyze clock reachability, generated clocks, gating, pulse width, skew, latency, transition, and mode coverage before routing.

As a **validator**, this process independently grades gate evidence, audits waivers, and publishes pass/fail outcomes. It does not mutate design candidates on behalf of workers.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `clock_validation` |
| Stage | `clock` |
| Role | `validator` |
| Host | `host.docker.internal` |
| Port | **8248** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Re-run clock checks
- Read the clock spec and CTS reports
- Emit a gate

### May not

- Edit the clock tree
- Ignore an uncovered mode
- Accept the CTS summary in place of the report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_clock_validation_spec` | `read_reports` | `read_clock_validation_spec` | Read the clocks, modes, and limits this gate must cover. |
| `read_primary_cts_reports` | `read_reports` | `read_primary_cts_reports` | Read skew, latency, and transition reports from primary artifacts. |
| `check_cts_provenance` | `read_reports` | `check_cts_provenance` | Check the CTS tool version and recipe against the frozen flow. |
| `validate_clock_reachability` | `submit_tool_job` | `validate_clock_reachability` | Check that every sink is reached in every required mode. |
| `check_generated_clock_relationships` | `submit_tool_job` | `check_generated_clock_relationships` | Check generated-clock sources and divide ratios. |
| `check_clock_gating` | `submit_tool_job` | `check_clock_gating` | Check integrated clock gates against the declared intent. |
| `check_pulse_width` | `submit_tool_job` | `check_pulse_width` | Check pulse width at the sinks. |
| `check_clock_skew_limit` | `read_reports` | `check_clock_skew_limit` | Check skew against the spec. |
| `check_clock_mode_coverage` | `read_reports` | `check_clock_mode_coverage` | List required modes that have no clock report. |
| `compare_cts_summary` | `read_reports` | `compare_cts_summary` | Compare the CTS summary with the primary reports. |
| `emit_clock_gate` | `emit_gate` | `emit_clock_gate` | Record whether the clock contract passed. |
| `publish_uncovered_clock_mode` | `publish_finding` | `publish_uncovered_clock_mode` | Publish a required mode with no clock check. |
| `publish_clock_spec_miss` | `publish_finding` | `publish_clock_spec_miss` | Publish a skew, latency, or transition miss. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/clock_validation:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ClockValidationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ClockValidationAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (clock specialists under `clock/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`cts`](../cts/) — worker, port **8247**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ClockValidationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8248`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ClockValidationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_clock_validation_spec` (`tools.read_clock_validation_spec`)

**Action:** `read_reports`. Read the clocks, modes, and limits this gate must cover.

Read the independent clock validation checklist and limits.

### `read_primary_cts_reports` (`tools.read_primary_cts_reports`)

**Action:** `read_reports`. Read skew, latency, and transition reports from primary artifacts.

Read primary CTS reports that validation will re-check.

### `check_cts_provenance` (`tools.check_cts_provenance`)

**Action:** `read_reports`. Check the CTS tool version and recipe against the frozen flow.

Verify CTS provenance before trusting the tree metrics.

### `validate_clock_reachability` (`tools.validate_clock_reachability`)

**Action:** `submit_tool_job`. Check that every sink is reached in every required mode.

Ensure every required sink is reached by its clock.

### `check_generated_clock_relationships` (`tools.check_generated_clock_relationships`)

**Action:** `submit_tool_job`. Check generated-clock sources and divide ratios.

Validate generated-clock source/divide/edge relationships.

### `check_clock_gating` (`tools.check_clock_gating`)

**Action:** `submit_tool_job`. Check integrated clock gates against the declared intent.

Check integrated clock-gating enable and timing arcs.

### `check_pulse_width` (`tools.check_pulse_width`)

**Action:** `submit_tool_job`. Check pulse width at the sinks.

Check minimum pulse-width constraints on clock pins.

### `check_clock_skew_limit` (`tools.check_clock_skew_limit`)

**Action:** `read_reports`. Check skew against the spec.

Check reported skew against the allowed skew budget.

### `check_clock_mode_coverage` (`tools.check_clock_mode_coverage`)

**Action:** `read_reports`. List required modes that have no clock report.

Ensure every required functional/test mode was analyzed.

### `compare_cts_summary` (`tools.compare_cts_summary`)

**Action:** `read_reports`. Compare the CTS summary with the primary reports.

Compare validator summary against CTS worker claims.

### `emit_clock_gate` (`tools.emit_clock_gate`)

**Action:** `emit_gate`. Record whether the clock contract passed.

Emit a pass/fail clock gate before routing may begin.

### `publish_uncovered_clock_mode` (`tools.publish_uncovered_clock_mode`)

**Action:** `publish_finding`. Publish a required mode with no clock check.

Publish that a required clock mode lacks coverage.

### `publish_clock_spec_miss` (`tools.publish_clock_spec_miss`)

**Action:** `publish_finding`. Publish a skew, latency, or transition miss.

Publish that the built tree misses part of the clock spec.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `gates`, `open_findings`.
- **Context exclude:** `stale_candidates`, `unverified_agent_claims`.
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
