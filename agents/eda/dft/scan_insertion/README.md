# Scan Insertion Agent (`scan_insertion`)

This directory is the deployable microservice package for the **Scan Insertion Agent** in the fleet **dft** stage (role `worker`).

## EDA responsibility

Scan Insertion agent class (scan_insertion).

Charter from `config.yaml`: Insert scan chains, compression, test clocks, and lockup elements while preserving functional behavior, and produce a scan-connectivity report.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `scan_insertion` |
| Stage | `dft` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8226** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Edit a DFT candidate
- Submit scan insertion
- Write the scan configuration

### May not

- Change functional behavior without an equivalence check
- Edit the canonical RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_scan_configuration` | `write_candidate` | `write_scan_configuration` | Write chain count, scan clocks, and compression settings for this candidate. |
| `write_test_mode_ports` | `write_candidate` | `write_test_mode_ports` | Add the test-mode ports required by the scan configuration. |
| `insert_scan` | `submit_tool_job` | `insert_scan` | Insert scan on an isolated candidate. Adapter target: scan insertion in the bound DFT tool. |
| `insert_compression` | `submit_tool_job` | `insert_compression` | Insert scan compression and decompression logic. |
| `insert_lockup_elements` | `submit_tool_job` | `insert_lockup_elements` | Insert lockup latches or flops on cross-clock scan paths. |
| `insert_test_clocks` | `submit_tool_job` | `insert_test_clocks` | Insert the dedicated test clocks named in the configuration. |
| `write_scan_def` | `write_candidate` | `write_scan_def` | Write scan chain order into the candidate database. |
| `read_scan_connectivity` | `read_reports` | `read_scan_connectivity` | Read chain counts, lockup cells, and broken connections. |
| `read_scan_chain_lengths` | `read_reports` | `read_scan_chain_lengths` | Read the length of every scan chain. |
| `check_scan_vs_functional_ports` | `read_reports` | `check_scan_vs_functional_ports` | Check that functional ports were not retimed or removed. |
| `report_scan_connectivity` | `publish_finding` | `report_scan_connectivity` | Publish chain counts, lockup cells, and connectivity evidence. |
| `flag_unbalanced_scan_chain` | `publish_finding` | `flag_unbalanced_scan_chain` | Publish a chain whose length exceeds the test-time budget. |
| `flag_missing_lockup` | `publish_finding` | `flag_missing_lockup` | Publish a cross-clock scan path with no lockup element. |
| `record_scan_tool_version` | `publish_finding` | `record_scan_tool_version` | Record the DFT tool, version, and scan recipe. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/scan_insertion:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ScanInsertionAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ScanInsertionAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Stage lead(s) that delegate here:
  - [`dft_lead`](../dft_lead/) (port **8225**)
- Sibling agents in this folder:
  - [`atpg_campaign`](../atpg_campaign/) — worker, port **8227**
  - [`dft_lead`](../dft_lead/) — lead, port **8225**
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ScanInsertionAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8226`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ScanInsertionAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_scan_configuration` (`tools.write_scan_configuration`)

**Action:** `write_candidate`. Write chain count, scan clocks, and compression settings for this candidate.

### `write_test_mode_ports` (`tools.write_test_mode_ports`)

**Action:** `write_candidate`. Add the test-mode ports required by the scan configuration.

### `insert_scan` (`tools.insert_scan`)

**Action:** `submit_tool_job`. Insert scan on an isolated candidate. Adapter target: scan insertion in the bound DFT tool.

### `insert_compression` (`tools.insert_compression`)

**Action:** `submit_tool_job`. Insert scan compression and decompression logic.

### `insert_lockup_elements` (`tools.insert_lockup_elements`)

**Action:** `submit_tool_job`. Insert lockup latches or flops on cross-clock scan paths.

### `insert_test_clocks` (`tools.insert_test_clocks`)

**Action:** `submit_tool_job`. Insert the dedicated test clocks named in the configuration.

### `write_scan_def` (`tools.write_scan_def`)

**Action:** `write_candidate`. Write scan chain order into the candidate database.

### `read_scan_connectivity` (`tools.read_scan_connectivity`)

**Action:** `read_reports`. Read chain counts, lockup cells, and broken connections.

### `read_scan_chain_lengths` (`tools.read_scan_chain_lengths`)

**Action:** `read_reports`. Read the length of every scan chain.

### `check_scan_vs_functional_ports` (`tools.check_scan_vs_functional_ports`)

**Action:** `read_reports`. Check that functional ports were not retimed or removed.

### `report_scan_connectivity` (`tools.report_scan_connectivity`)

**Action:** `publish_finding`. Publish chain counts, lockup cells, and connectivity evidence.

### `flag_unbalanced_scan_chain` (`tools.flag_unbalanced_scan_chain`)

**Action:** `publish_finding`. Publish a chain whose length exceeds the test-time budget.

### `flag_missing_lockup` (`tools.flag_missing_lockup`)

**Action:** `publish_finding`. Publish a cross-clock scan path with no lockup element.

### `record_scan_tool_version` (`tools.record_scan_tool_version`)

**Action:** `publish_finding`. Record the DFT tool, version, and scan recipe.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `canonical_source`, `open_findings`, `gates`.
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
