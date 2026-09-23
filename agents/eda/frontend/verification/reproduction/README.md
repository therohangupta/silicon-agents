# Reproduction Agent (`reproduction`)

This directory is the deployable microservice package for the **Reproduction Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Reproduction Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Produce a minimal stable reproduction and a waveform slice for one failure cluster.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `reproduction` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8223** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a minimized test on an isolated branch
- Read the failing waveform
- Rerun the minimized test to confirm it still fails

### May not

- Edit RTL
- Declare the root cause fixed
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_failing_waveform` | `read_reports` | `read_failing_waveform` | Read the waveform for the seed that represents this cluster. |
| `minimize_failure` | `write_candidate` | `minimize_failure` | Reduce a failing test to a stable reproduction. |
| `slice_waveform` | `read_reports` | `slice_waveform` | Extract the signals and time window that show the failure. |
| `write_reproduction_test` | `write_candidate` | `write_reproduction_test` | Write the minimized test on an isolated branch. |
| `confirm_reproduction_fails` | `submit_tool_job` | `confirm_reproduction_fails` | Rerun the minimized test and confirm it still fails. |
| `confirm_reproduction_stable` | `submit_tool_job` | `confirm_reproduction_stable` | Rerun the minimized test across the requested seeds and report which still fail. |
| `list_reproduction_signals` | `read_reports` | `list_reproduction_signals` | List the signals required to see the failure. |
| `diff_reproduction_against_original` | `read_reports` | `diff_reproduction_against_original` | Show what the minimization removed. |
| `flag_unstable_reproduction` | `publish_finding` | `flag_unstable_reproduction` | Publish a minimized test that does not fail reliably. |
| `flag_reproduction_changed_symptom` | `publish_finding` | `flag_reproduction_changed_symptom` | Publish a minimized test whose first error differs from the original. |
| `record_reproduction_artifact` | `publish_finding` | `record_reproduction_artifact` | Record the test, seed, waveform slice, and original cluster. |
| `publish_reproduction` | `publish_finding` | `publish_reproduction` | Publish the minimized test ref and the waveform slice. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/reproduction:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ReproductionAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ReproductionAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
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
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ReproductionAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8223`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ReproductionAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_failing_waveform` (`tools.read_failing_waveform`)

**Action:** `read_reports`. Read the waveform for the seed that represents this cluster.

### `minimize_failure` (`tools.minimize_failure`)

**Action:** `write_candidate`. Reduce a failing test to a stable reproduction.

### `slice_waveform` (`tools.slice_waveform`)

**Action:** `read_reports`. Extract the signals and time window that show the failure.

### `write_reproduction_test` (`tools.write_reproduction_test`)

**Action:** `write_candidate`. Write the minimized test on an isolated branch.

### `confirm_reproduction_fails` (`tools.confirm_reproduction_fails`)

**Action:** `submit_tool_job`. Rerun the minimized test and confirm it still fails.

### `confirm_reproduction_stable` (`tools.confirm_reproduction_stable`)

**Action:** `submit_tool_job`. Rerun the minimized test across the requested seeds and report which still fail.

### `list_reproduction_signals` (`tools.list_reproduction_signals`)

**Action:** `read_reports`. List the signals required to see the failure.

### `diff_reproduction_against_original` (`tools.diff_reproduction_against_original`)

**Action:** `read_reports`. Show what the minimization removed.

### `flag_unstable_reproduction` (`tools.flag_unstable_reproduction`)

**Action:** `publish_finding`. Publish a minimized test that does not fail reliably.

### `flag_reproduction_changed_symptom` (`tools.flag_reproduction_changed_symptom`)

**Action:** `publish_finding`. Publish a minimized test whose first error differs from the original.

### `record_reproduction_artifact` (`tools.record_reproduction_artifact`)

**Action:** `publish_finding`. Record the test, seed, waveform slice, and original cluster.

### `publish_reproduction` (`tools.publish_reproduction`)

**Action:** `publish_finding`. Publish the minimized test ref and the waveform slice.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
