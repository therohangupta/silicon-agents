# Clock/Reset Agent (`clock_reset`)

This directory is the deployable microservice package for the **Clock/Reset Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

Clock/Reset Agent — agent class entry point.

Charter from `config.yaml`: Check clocking, reset topology, and clock gating against the declared intent.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `clock_reset` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8210** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read RTL and clock intent
- Publish a clock or reset finding
- Edit clock or reset RTL only on an isolated candidate when the task asks for a fix

### May not

- Rewrite the clock architecture
- Add a waiver
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_clock_intent` | `read_reports` | `read_clock_intent` | Read declared clocks, generated clocks, and gating intent. |
| `analyze_clock_intent` | `read_reports` | `analyze_clock_intent` | Check clocks, generated clocks, and gating against the intent. |
| `list_clock_domains` | `read_reports` | `list_clock_domains` | List clock domains and the registers in each. |
| `list_generated_clocks` | `read_reports` | `list_generated_clocks` | List generated and gated clocks and their sources. |
| `analyze_reset_topology` | `read_reports` | `analyze_reset_topology` | Check reset synchronizers, tree shape, and deassertion. |
| `list_reset_domains` | `read_reports` | `list_reset_domains` | List reset domains and asynchronous-reset registers. |
| `check_reset_synchronizers` | `read_reports` | `check_reset_synchronizers` | Check that asynchronous resets are synchronized once per domain. |
| `write_clock_gate_fix` | `write_candidate` | `write_clock_gate_fix` | Edit one illegal clock gate on an isolated candidate. |
| `write_reset_synchronizer` | `write_candidate` | `write_reset_synchronizer` | Add one missing reset synchronizer on an isolated candidate. |
| `lint_clock_reset` | `submit_tool_job` | `lint_clock_reset` | Run the clock and reset lint rules on the candidate. |
| `flag_ungated_clock_mux` | `publish_finding` | `flag_ungated_clock_mux` | Publish a clock mux or gate that does not match the intent. |
| `flag_reset_tree_issue` | `publish_finding` | `flag_reset_tree_issue` | Publish a reset that is asynchronous, missing, or reconvergent. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/clock_reset:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ClockResetAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ClockResetAgent)`.
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
  - [`lint_quality`](../lint_quality/) — worker, port **8213**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ClockResetAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8210`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ClockResetAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_clock_intent` (`tools.read_clock_intent`)

**Action:** `read_reports`. Read declared clocks, generated clocks, and gating intent.

### `analyze_clock_intent` (`tools.analyze_clock_intent`)

**Action:** `read_reports`. Check clocks, generated clocks, and gating against the intent.

### `list_clock_domains` (`tools.list_clock_domains`)

**Action:** `read_reports`. List clock domains and the registers in each.

### `list_generated_clocks` (`tools.list_generated_clocks`)

**Action:** `read_reports`. List generated and gated clocks and their sources.

### `analyze_reset_topology` (`tools.analyze_reset_topology`)

**Action:** `read_reports`. Check reset synchronizers, tree shape, and deassertion.

### `list_reset_domains` (`tools.list_reset_domains`)

**Action:** `read_reports`. List reset domains and asynchronous-reset registers.

### `check_reset_synchronizers` (`tools.check_reset_synchronizers`)

**Action:** `read_reports`. Check that asynchronous resets are synchronized once per domain.

### `write_clock_gate_fix` (`tools.write_clock_gate_fix`)

**Action:** `write_candidate`. Edit one illegal clock gate on an isolated candidate.

### `write_reset_synchronizer` (`tools.write_reset_synchronizer`)

**Action:** `write_candidate`. Add one missing reset synchronizer on an isolated candidate.

### `lint_clock_reset` (`tools.lint_clock_reset`)

**Action:** `submit_tool_job`. Run the clock and reset lint rules on the candidate.

### `flag_ungated_clock_mux` (`tools.flag_ungated_clock_mux`)

**Action:** `publish_finding`. Publish a clock mux or gate that does not match the intent.

### `flag_reset_tree_issue` (`tools.flag_reset_tree_issue`)

**Action:** `publish_finding`. Publish a reset that is asynchronous, missing, or reconvergent.

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
