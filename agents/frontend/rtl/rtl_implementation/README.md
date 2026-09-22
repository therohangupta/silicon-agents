# RTL Implementation Agent (`rtl_implementation`)

This directory is the deployable microservice package for the **RTL Implementation Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

RTL Implementation Agent — agent class entry point.

Charter from `config.yaml`: Make one bounded source change in an isolated branch and record the hypothesis it is testing.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `rtl_implementation` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8209** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Create one candidate branch from a pinned baseline
- Edit RTL only on that branch

### May not

- Push to the canonical revision
- Declare the change functionally correct
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `create_candidate_branch` | `write_candidate` | `create_candidate_branch` | Create an isolated worktree from the pinned baseline. |
| `apply_bounded_rtl_edit` | `write_candidate` | `apply_bounded_rtl_edit` | Apply one RTL edit that matches the task hypothesis. |
| `add_module_port` | `write_candidate` | `add_module_port` | Add one port required by an interface contract. |
| `rename_signal` | `write_candidate` | `rename_signal` | Rename one signal and its references inside the candidate. |
| `insert_pipeline_stage` | `write_candidate` | `insert_pipeline_stage` | Add one pipeline stage on a named path inside the candidate. |
| `register_output` | `write_candidate` | `register_output` | Register one combinational output in the candidate. |
| `write_file_header` | `write_candidate` | `write_file_header` | Write the candidate's change note, hypothesis, and baseline ref into the touched files. |
| `summarize_candidate_diff` | `read_reports` | `summarize_candidate_diff` | Summarize the diff, the hypothesis, and the files touched. |
| `list_candidate_files` | `read_reports` | `list_candidate_files` | List files this candidate changed relative to the baseline. |
| `read_module_ports` | `read_reports` | `read_module_ports` | Read the ports of one module in the candidate. |
| `compile_candidate` | `submit_tool_job` | `compile_candidate` | Compile or elaborate the candidate and return syntax and elaboration errors. |
| `record_edit_hypothesis` | `publish_finding` | `record_edit_hypothesis` | Publish the hypothesis, diff stat, and files for this candidate. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/rtl_implementation:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RtlImplementationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RtlImplementationAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (rtl specialists under `rtl/`).
- Stage lead(s) that delegate here:
  - [`rtl_lead`](../rtl_lead/) (port **8208**)
- Sibling agents in this folder:
  - [`cdc_rdc`](../cdc_rdc/) — worker, port **8211**
  - [`clock_reset`](../clock_reset/) — worker, port **8210**
  - [`lint_quality`](../lint_quality/) — worker, port **8213**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RtlImplementationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8209`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RtlImplementationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `create_candidate_branch` (`tools.create_candidate_branch`)

**Action:** `write_candidate`. Create an isolated worktree from the pinned baseline.

### `apply_bounded_rtl_edit` (`tools.apply_bounded_rtl_edit`)

**Action:** `write_candidate`. Apply one RTL edit that matches the task hypothesis.

### `add_module_port` (`tools.add_module_port`)

**Action:** `write_candidate`. Add one port required by an interface contract.

### `rename_signal` (`tools.rename_signal`)

**Action:** `write_candidate`. Rename one signal and its references inside the candidate.

### `insert_pipeline_stage` (`tools.insert_pipeline_stage`)

**Action:** `write_candidate`. Add one pipeline stage on a named path inside the candidate.

### `register_output` (`tools.register_output`)

**Action:** `write_candidate`. Register one combinational output in the candidate.

### `write_file_header` (`tools.write_file_header`)

**Action:** `write_candidate`. Write the candidate's change note, hypothesis, and baseline ref into the touched files.

### `summarize_candidate_diff` (`tools.summarize_candidate_diff`)

**Action:** `read_reports`. Summarize the diff, the hypothesis, and the files touched.

### `list_candidate_files` (`tools.list_candidate_files`)

**Action:** `read_reports`. List files this candidate changed relative to the baseline.

### `read_module_ports` (`tools.read_module_ports`)

**Action:** `read_reports`. Read the ports of one module in the candidate.

### `compile_candidate` (`tools.compile_candidate`)

**Action:** `submit_tool_job`. Compile or elaborate the candidate and return syntax and elaboration errors.

### `record_edit_hypothesis` (`tools.record_edit_hypothesis`)

**Action:** `publish_finding`. Publish the hypothesis, diff stat, and files for this candidate.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
