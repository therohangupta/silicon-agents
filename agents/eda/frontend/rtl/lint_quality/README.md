# Lint/Quality Agent (`lint_quality`)

This directory is the deployable microservice package for the **Lint/Quality Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

Lint/Quality Agent — agent class entry point.

Charter from `config.yaml`: Detect structural, synthesis, style, and maintainability problems in a candidate.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `lint_quality` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8213** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the candidate RTL
- Publish lint findings

### May not

- Edit the RTL it is grading
- Suppress a lint class globally
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `run_lint` | `submit_tool_job` | `run_lint` | Run the bound lint flow on one candidate. |
| `run_synthesis_lint` | `submit_tool_job` | `run_synthesis_lint` | Run lint rules aimed at latch inference, loops, and undriven logic. |
| `read_lint_report` | `read_reports` | `read_lint_report` | Read the lint report for one candidate. |
| `filter_lint_by_severity` | `read_reports` | `filter_lint_by_severity` | Return lint messages at or above a severity. |
| `filter_lint_by_rule` | `read_reports` | `filter_lint_by_rule` | Return lint messages for one rule id. |
| `diff_lint_against_baseline` | `read_reports` | `diff_lint_against_baseline` | Show lint messages introduced or removed versus the baseline. |
| `classify_lint_findings` | `publish_finding` | `classify_lint_findings` | Group lint messages by likely owner and severity. |
| `flag_latch_inference` | `publish_finding` | `flag_latch_inference` | Publish inferred latches. |
| `flag_combinational_loop` | `publish_finding` | `flag_combinational_loop` | Publish combinational loops. |
| `flag_undriven_net` | `publish_finding` | `flag_undriven_net` | Publish undriven or multiply driven nets. |
| `flag_width_mismatch` | `publish_finding` | `flag_width_mismatch` | Publish assignment width mismatches. |
| `record_lint_waive_request` | `publish_finding` | `record_lint_waive_request` | Publish an unsigned request to waive one lint rule on one line. This does not waive it. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/lint_quality:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `LintQualityAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, LintQualityAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (rtl specialists under `rtl/`).
- Stage lead(s) that delegate here:
  - [`rtl_lead`](../rtl_lead/) (port **8208**)
- Sibling agents in this folder:
  - [`cdc_rdc`](../cdc_rdc/) — worker, port **8211**
  - [`clock_reset`](../clock_reset/) — worker, port **8210**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `LintQualityAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8213`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `LintQualityAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `run_lint` (`tools.run_lint`)

**Action:** `submit_tool_job`. Run the bound lint flow on one candidate.

### `run_synthesis_lint` (`tools.run_synthesis_lint`)

**Action:** `submit_tool_job`. Run lint rules aimed at latch inference, loops, and undriven logic.

### `read_lint_report` (`tools.read_lint_report`)

**Action:** `read_reports`. Read the lint report for one candidate.

### `filter_lint_by_severity` (`tools.filter_lint_by_severity`)

**Action:** `read_reports`. Return lint messages at or above a severity.

### `filter_lint_by_rule` (`tools.filter_lint_by_rule`)

**Action:** `read_reports`. Return lint messages for one rule id.

### `diff_lint_against_baseline` (`tools.diff_lint_against_baseline`)

**Action:** `read_reports`. Show lint messages introduced or removed versus the baseline.

### `classify_lint_findings` (`tools.classify_lint_findings`)

**Action:** `publish_finding`. Group lint messages by likely owner and severity.

### `flag_latch_inference` (`tools.flag_latch_inference`)

**Action:** `publish_finding`. Publish inferred latches.

### `flag_combinational_loop` (`tools.flag_combinational_loop`)

**Action:** `publish_finding`. Publish combinational loops.

### `flag_undriven_net` (`tools.flag_undriven_net`)

**Action:** `publish_finding`. Publish undriven or multiply driven nets.

### `flag_width_mismatch` (`tools.flag_width_mismatch`)

**Action:** `publish_finding`. Publish assignment width mismatches.

### `record_lint_waive_request` (`tools.record_lint_waive_request`)

**Action:** `publish_finding`. Publish an unsigned request to waive one lint rule on one line. This does not waive it.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `open_findings`, `experiments`.
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
