# Low-Power Agent (`low_power`)

This directory is the deployable microservice package for the **Low-Power Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

Low-Power Agent — agent class entry point.

Charter from `config.yaml`: Maintain power domains, isolation, retention, and UPF consistency.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `low_power` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8212** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read UPF and RTL
- Edit UPF on an isolated candidate

### May not

- Drop an isolation cell to save area
- Change a power domain without a finding
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_upf` | `read_reports` | `read_upf` | Read power domains, supply nets, and isolation strategies. |
| `check_upf_consistency` | `read_reports` | `check_upf_consistency` | Compare UPF domains and RTL hierarchy. |
| `check_isolation_retention` | `read_reports` | `check_isolation_retention` | Check isolation, retention, and level-shifter strategy. |
| `list_power_domains` | `read_reports` | `list_power_domains` | List domains, their supplies, and the modules inside them. |
| `list_domain_crossings` | `read_reports` | `list_domain_crossings` | List signals that cross power domains. |
| `check_retention_registers` | `read_reports` | `check_retention_registers` | Check which registers require retention and which cells implement it. |
| `write_isolation_strategy` | `write_candidate` | `write_isolation_strategy` | Add a missing isolation strategy on an isolated UPF candidate. |
| `write_retention_strategy` | `write_candidate` | `write_retention_strategy` | Add a missing retention strategy on an isolated UPF candidate. |
| `write_level_shifter` | `write_candidate` | `write_level_shifter` | Add a level shifter on one domain crossing in the candidate. |
| `run_upf_lint` | `submit_tool_job` | `run_upf_lint` | Run UPF consistency checks. |
| `flag_missing_power_isolation` | `publish_finding` | `flag_missing_power_isolation` | Publish a domain crossing with no isolation. |
| `flag_upf_rtl_mismatch` | `publish_finding` | `flag_upf_rtl_mismatch` | Publish a module whose UPF domain and RTL hierarchy disagree. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/low_power:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `LowPowerAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, LowPowerAgent)`.
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
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `LowPowerAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8212`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `LowPowerAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_upf` (`tools.read_upf`)

**Action:** `read_reports`. Read power domains, supply nets, and isolation strategies.

### `check_upf_consistency` (`tools.check_upf_consistency`)

**Action:** `read_reports`. Compare UPF domains and RTL hierarchy.

### `check_isolation_retention` (`tools.check_isolation_retention`)

**Action:** `read_reports`. Check isolation, retention, and level-shifter strategy.

### `list_power_domains` (`tools.list_power_domains`)

**Action:** `read_reports`. List domains, their supplies, and the modules inside them.

### `list_domain_crossings` (`tools.list_domain_crossings`)

**Action:** `read_reports`. List signals that cross power domains.

### `check_retention_registers` (`tools.check_retention_registers`)

**Action:** `read_reports`. Check which registers require retention and which cells implement it.

### `write_isolation_strategy` (`tools.write_isolation_strategy`)

**Action:** `write_candidate`. Add a missing isolation strategy on an isolated UPF candidate.

### `write_retention_strategy` (`tools.write_retention_strategy`)

**Action:** `write_candidate`. Add a missing retention strategy on an isolated UPF candidate.

### `write_level_shifter` (`tools.write_level_shifter`)

**Action:** `write_candidate`. Add a level shifter on one domain crossing in the candidate.

### `run_upf_lint` (`tools.run_upf_lint`)

**Action:** `submit_tool_job`. Run UPF consistency checks.

### `flag_missing_power_isolation` (`tools.flag_missing_power_isolation`)

**Action:** `publish_finding`. Publish a domain crossing with no isolation.

### `flag_upf_rtl_mismatch` (`tools.flag_upf_rtl_mismatch`)

**Action:** `publish_finding`. Publish a module whose UPF domain and RTL hierarchy disagree.

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
