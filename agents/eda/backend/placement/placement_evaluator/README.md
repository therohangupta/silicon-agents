# Independent Multi-Corner Placement Evaluator (`placement_evaluator`)

This directory is the deployable microservice package for the **Independent Multi-Corner Placement Evaluator** in the fleet **placement** stage (role `validator`).

## EDA responsibility

Independent Multi-Corner Placement Evaluator.

Charter from `config.yaml`: Re-check a placement across required modes and corners, and reject a gain that only shifts violations.

As a **validator**, this process independently grades gate evidence, audits waivers, and publishes pass/fail outcomes. It does not mutate design candidates on behalf of workers.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `placement_evaluator` |
| Stage | `placement` |
| Role | `validator` |
| Host | `host.docker.internal` |
| Port | **8245** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Re-run placement checks
- Read every required corner
- Emit a gate

### May not

- Edit the placement
- Grade only the corner that improved
- Accept the experiment summary in place of the reports
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_required_corners` | `read_reports` | `read_required_corners` | Read the modes and corners this placement must pass. |
| `read_primary_placement_reports` | `read_reports` | `read_primary_placement_reports` | Read legality, timing, and congestion reports for every corner. |
| `check_placement_provenance` | `read_reports` | `check_placement_provenance` | Check that the recipe and library match the frozen flow. |
| `evaluate_multicorner_placement` | `submit_tool_job` | `evaluate_multicorner_placement` | Re-evaluate legality and timing across modes and corners. |
| `recheck_placement_legality` | `submit_tool_job` | `recheck_placement_legality` | Re-run the legality check on the pinned DEF. |
| `compare_corner_violations` | `read_reports` | `compare_corner_violations` | Show violations that moved from one corner to another. |
| `check_constraint_coverage` | `read_reports` | `check_constraint_coverage` | Check that every required mode has constraints and a report. |
| `compare_placement_summary` | `read_reports` | `compare_placement_summary` | Compare the experiment summary with the primary reports. |
| `emit_placement_gate` | `emit_gate` | `emit_placement_gate` | Record whether the placement candidate passed in every required corner. |
| `publish_shifted_violation` | `publish_finding` | `publish_shifted_violation` | Publish a candidate whose improvement is a violation moved to another corner. |
| `publish_missing_corner_report` | `publish_finding` | `publish_missing_corner_report` | Publish a required corner with no report. |
| `record_placement_grade_inputs` | `publish_finding` | `record_placement_grade_inputs` | Record the DEF ref and the reports this grade used. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/placement_evaluator:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PlacementEvaluatorAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PlacementEvaluatorAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (placement specialists under `placement/`).
- Stage lead(s) that schedule this gate:
  - [`placement_lead`](../placement_lead/) (port **8243**)
- Sibling agents in this folder:
  - [`boundary_coordinator`](../boundary_coordinator/) — worker, port **8246**
  - [`placement_experiment`](../placement_experiment/) — worker, port **8244**
  - [`placement_lead`](../placement_lead/) — lead, port **8243**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PlacementEvaluatorAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8245`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PlacementEvaluatorAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_required_corners` (`tools.read_required_corners`)

**Action:** `read_reports`. Read the modes and corners this placement must pass.

Read the required PVT corners and modes for placement signoff-style checks.

### `read_primary_placement_reports` (`tools.read_primary_placement_reports`)

**Action:** `read_reports`. Read legality, timing, and congestion reports for every corner.

Read the primary placement reports produced by the experiment worker.

### `check_placement_provenance` (`tools.check_placement_provenance`)

**Action:** `read_reports`. Check that the recipe and library match the frozen flow.

Verify the candidate's provenance chain is complete and trustworthy.

### `evaluate_multicorner_placement` (`tools.evaluate_multicorner_placement`)

**Action:** `submit_tool_job`. Re-evaluate legality and timing across modes and corners.

Re-evaluate placement metrics across all required corners/modes.

### `recheck_placement_legality` (`tools.recheck_placement_legality`)

**Action:** `submit_tool_job`. Re-run the legality check on the pinned DEF.

Independently re-check legality so the worker cannot self-certify.

### `compare_corner_violations` (`tools.compare_corner_violations`)

**Action:** `read_reports`. Show violations that moved from one corner to another.

Detect whether violations merely shifted across corners.

### `check_constraint_coverage` (`tools.check_constraint_coverage`)

**Action:** `read_reports`. Check that every required mode has constraints and a report.

Ensure SDC/exceptions covering this partition were applied.

### `compare_placement_summary` (`tools.compare_placement_summary`)

**Action:** `read_reports`. Compare the experiment summary with the primary reports.

Compare evaluator summary vs worker-claimed summary.

### `emit_placement_gate` (`tools.emit_placement_gate`)

**Action:** `emit_gate`. Record whether the placement candidate passed in every required corner.

Emit a pass/fail placement gate record into engineering memory.

### `publish_shifted_violation` (`tools.publish_shifted_violation`)

**Action:** `publish_finding`. Publish a candidate whose improvement is a violation moved to another corner.

Publish that a claimed improvement only shifted a violation.

### `publish_missing_corner_report` (`tools.publish_missing_corner_report`)

**Action:** `publish_finding`. Publish a required corner with no report.

Publish that a required corner report is missing.

### `record_placement_grade_inputs` (`tools.record_placement_grade_inputs`)

**Action:** `publish_finding`. Record the DEF ref and the reports this grade used.

Record inputs used to grade the placement candidate.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
