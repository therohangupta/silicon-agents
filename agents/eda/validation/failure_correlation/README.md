# Failure-Correlation Agent (`failure_correlation`)

This directory is the deployable microservice package for the **Failure-Correlation Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Failure Correlation agent class (failure_correlation).

Charter from `config.yaml`: Correlate a silicon failure with simulation, formal, signoff, firmware, and manufacturing evidence, and name the earliest abstraction that reproduces it.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `failure_correlation` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8269** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read silicon and pre-silicon evidence
- Name the earliest abstraction that reproduces the failure

### May not

- Close the failure
- Edit RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_silicon_symptom` | `read_reports` | `read_silicon_symptom` | Read the silicon symptom, board, and conditions. |
| `read_simulation_evidence` | `read_reports` | `read_simulation_evidence` | Read simulation failures that share the symptom. |
| `read_formal_evidence` | `read_reports` | `read_formal_evidence` | Read formal counterexamples that share the symptom. |
| `read_signoff_evidence` | `read_reports` | `read_signoff_evidence` | Read timing, power, and reliability results at the failing condition. |
| `read_firmware_evidence` | `read_reports` | `read_firmware_evidence` | Read the firmware revision and diagnostic output. |
| `read_manufacturing_evidence` | `read_reports` | `read_manufacturing_evidence` | Read lot, wafer, and test-program results. |
| `correlate_silicon_failure` | `read_reports` | `correlate_silicon_failure` | Link a silicon symptom to pre-silicon and manufacturing evidence. |
| `identify_earliest_abstraction` | `publish_finding` | `identify_earliest_abstraction` | Name the earliest model that reproduces the failure. |
| `rank_correlation_hypotheses` | `read_reports` | `rank_correlation_hypotheses` | Rank likely causes with the evidence for and against each. |
| `flag_uncorrelated_symptom` | `publish_finding` | `flag_uncorrelated_symptom` | Publish a symptom with no matching pre-silicon evidence. |
| `record_correlation_evidence` | `publish_finding` | `record_correlation_evidence` | Record every artifact the correlation used. |
| `publish_failure_correlation` | `publish_finding` | `publish_failure_correlation` | Publish the symptom, the earliest reproducing abstraction, and the evidence refs. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/failure_correlation:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `FailureCorrelationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, FailureCorrelationAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Stage lead(s) that delegate here:
  - [`bringup_lead`](../bringup_lead/) (port **8263**)
- Sibling agents in this folder:
  - [`bringup_lead`](../bringup_lead/) — lead, port **8263**
  - [`characterization`](../characterization/) — worker, port **8268**
  - [`errata_drafting`](../errata_drafting/) — worker, port **8270**
  - [`firmware_test_program`](../firmware_test_program/) — worker, port **8266**
  - [`instrument_control`](../instrument_control/) — worker, port **8265**
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `FailureCorrelationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8269`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `FailureCorrelationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_silicon_symptom` (`tools.read_silicon_symptom`)

**Action:** `read_reports`. Read the silicon symptom, board, and conditions.

### `read_simulation_evidence` (`tools.read_simulation_evidence`)

**Action:** `read_reports`. Read simulation failures that share the symptom.

### `read_formal_evidence` (`tools.read_formal_evidence`)

**Action:** `read_reports`. Read formal counterexamples that share the symptom.

### `read_signoff_evidence` (`tools.read_signoff_evidence`)

**Action:** `read_reports`. Read timing, power, and reliability results at the failing condition.

### `read_firmware_evidence` (`tools.read_firmware_evidence`)

**Action:** `read_reports`. Read the firmware revision and diagnostic output.

### `read_manufacturing_evidence` (`tools.read_manufacturing_evidence`)

**Action:** `read_reports`. Read lot, wafer, and test-program results.

### `correlate_silicon_failure` (`tools.correlate_silicon_failure`)

**Action:** `read_reports`. Link a silicon symptom to pre-silicon and manufacturing evidence.

### `identify_earliest_abstraction` (`tools.identify_earliest_abstraction`)

**Action:** `publish_finding`. Name the earliest model that reproduces the failure.

### `rank_correlation_hypotheses` (`tools.rank_correlation_hypotheses`)

**Action:** `read_reports`. Rank likely causes with the evidence for and against each.

### `flag_uncorrelated_symptom` (`tools.flag_uncorrelated_symptom`)

**Action:** `publish_finding`. Publish a symptom with no matching pre-silicon evidence.

### `record_correlation_evidence` (`tools.record_correlation_evidence`)

**Action:** `publish_finding`. Record every artifact the correlation used.

### `publish_failure_correlation` (`tools.publish_failure_correlation`)

**Action:** `publish_finding`. Publish the symptom, the earliest reproducing abstraction, and the evidence refs.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
