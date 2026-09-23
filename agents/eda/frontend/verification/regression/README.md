# Regression Agent (`regression`)

This directory is the deployable microservice package for the **Regression Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Regression Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Select seeds, shard the workload, and run a reproducible regression.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `regression` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8221** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a test manifest
- Submit a regression job
- Read results including failing seeds

### May not

- Drop a failing seed from the manifest
- Edit RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_prior_failures` | `read_reports` | `read_prior_failures` | Read seeds and tests that failed in the previous campaign. |
| `read_uncovered_bins` | `read_reports` | `read_uncovered_bins` | Read bins that still need stimulus. |
| `choose_regression_seeds` | `read_reports` | `choose_regression_seeds` | Choose seeds from prior failures and uncovered bins. Keep every seed that previously failed. |
| `write_regression_manifest` | `write_candidate` | `write_regression_manifest` | Write the test, seed, and plusarg manifest for this campaign. |
| `shard_regression` | `write_candidate` | `shard_regression` | Split the manifest into shards with stable shard ids. |
| `submit_regression` | `submit_tool_job` | `submit_regression` | Submit the regression manifest to the bound simulator. |
| `rerun_failed_shard` | `submit_tool_job` | `rerun_failed_shard` | Rerun one failed shard with the same idempotency key. |
| `read_regression_results` | `read_reports` | `read_regression_results` | Read pass, fail, and infrastructure-error counts. |
| `read_failing_seeds` | `read_reports` | `read_failing_seeds` | List failing tests and seeds. Do not omit any. |
| `compare_regression_to_baseline` | `read_reports` | `compare_regression_to_baseline` | Show tests that newly fail or newly pass versus the baseline campaign. |
| `record_simulator_version` | `publish_finding` | `record_simulator_version` | Record the simulator, version, and compile options. |
| `flag_manifest_dropped_seed` | `publish_finding` | `flag_manifest_dropped_seed` | Publish a manifest that omitted a previously failing seed. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/regression:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RegressionAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RegressionAgent)`.
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
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RegressionAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8221`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RegressionAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_prior_failures` (`tools.read_prior_failures`)

**Action:** `read_reports`. Read seeds and tests that failed in the previous campaign.

### `read_uncovered_bins` (`tools.read_uncovered_bins`)

**Action:** `read_reports`. Read bins that still need stimulus.

### `choose_regression_seeds` (`tools.choose_regression_seeds`)

**Action:** `read_reports`. Choose seeds from prior failures and uncovered bins. Keep every seed that previously failed.

### `write_regression_manifest` (`tools.write_regression_manifest`)

**Action:** `write_candidate`. Write the test, seed, and plusarg manifest for this campaign.

### `shard_regression` (`tools.shard_regression`)

**Action:** `write_candidate`. Split the manifest into shards with stable shard ids.

### `submit_regression` (`tools.submit_regression`)

**Action:** `submit_tool_job`. Submit the regression manifest to the bound simulator.

### `rerun_failed_shard` (`tools.rerun_failed_shard`)

**Action:** `submit_tool_job`. Rerun one failed shard with the same idempotency key.

### `read_regression_results` (`tools.read_regression_results`)

**Action:** `read_reports`. Read pass, fail, and infrastructure-error counts.

### `read_failing_seeds` (`tools.read_failing_seeds`)

**Action:** `read_reports`. List failing tests and seeds. Do not omit any.

### `compare_regression_to_baseline` (`tools.compare_regression_to_baseline`)

**Action:** `read_reports`. Show tests that newly fail or newly pass versus the baseline campaign.

### `record_simulator_version` (`tools.record_simulator_version`)

**Action:** `publish_finding`. Record the simulator, version, and compile options.

### `flag_manifest_dropped_seed` (`tools.flag_manifest_dropped_seed`)

**Action:** `publish_finding`. Publish a manifest that omitted a previously failing seed.

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
