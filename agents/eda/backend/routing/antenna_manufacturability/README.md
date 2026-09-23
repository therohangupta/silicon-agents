# Antenna and Manufacturability Agent (`antenna_manufacturability`)

This directory is the deployable microservice package for the **Antenna and Manufacturability Agent** in the fleet **routing** stage (role `worker`).

## EDA responsibility

Tools for the Antenna and Manufacturability Agent.

Charter from `config.yaml`: Detect antenna, via-reliability, density, and patterning risks, apply a fix on an isolated candidate, and check electrical side effects. Adapter target: OpenROAD repair_antennas.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `antenna_manufacturability` |
| Stage | `routing` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8253** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read physical-verification markers
- Apply a diode, jumper, layer, or via fix on an isolated candidate
- Submit an antenna check and a side-effect report

### May not

- Delete a marker
- Claim a fix is closed without an electrical side-effect check
- Edit the canonical layout
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_antenna_report` | `read_reports` | `read_antenna_report` | Read antenna markers. |
| `list_antenna_violations` | `read_reports` | `list_antenna_violations` | List antenna violations by net and gate. |
| `list_via_reliability_risks` | `read_reports` | `list_via_reliability_risks` | List vias that fail the reliability rule. |
| `list_density_violations` | `read_reports` | `list_density_violations` | List density windows that fail. |
| `list_patterning_risks` | `read_reports` | `list_patterning_risks` | List patterning and manufacturability markers. |
| `propose_diode_insertion` | `publish_finding` | `propose_diode_insertion` | Publish a diode insertion and the electrical load it adds. |
| `propose_antenna_jumper` | `publish_finding` | `propose_antenna_jumper` | Publish a jumper and the layer it uses. |
| `propose_antenna_layer_hop` | `publish_finding` | `propose_antenna_layer_hop` | Publish a layer hop for one antenna net. |
| `apply_antenna_fix` | `write_candidate` | `apply_antenna_fix` | Apply one diode, jumper, layer, or via fix on an isolated candidate. Adapter target: OpenROAD repair_antennas. |
| `run_antenna_check` | `submit_tool_job` | `run_antenna_check` | Re-run the antenna check. Adapter target: OpenROAD check_antennas. |
| `verify_antenna_electrical_impact` | `submit_tool_job` | `verify_antenna_electrical_impact` | Check input capacitance, delay, and noise after the fix. |
| `report_antenna_timing_side_effect` | `read_reports` | `report_antenna_timing_side_effect` | Report the timing change caused by the fix. |
| `flag_unchecked_antenna_fix` | `publish_finding` | `flag_unchecked_antenna_fix` | Publish a fix that has no electrical side-effect check. |
| `record_antenna_rule_deck` | `publish_finding` | `record_antenna_rule_deck` | Record the antenna rule deck and the candidate it graded. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/antenna_manufacturability:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `AntennaManufacturabilityAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, AntennaManufacturabilityAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (routing specialists under `routing/`).
- Stage lead(s) that delegate here:
  - [`routing_lead`](../routing_lead/) (port **8249**)
- Sibling agents in this folder:
  - [`detailed_routing_repair`](../detailed_routing_repair/) — worker, port **8251**
  - [`global_routing`](../global_routing/) — worker, port **8250**
  - [`routing_lead`](../routing_lead/) — lead, port **8249**
  - [`si_noise_repair`](../si_noise_repair/) — worker, port **8252**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `AntennaManufacturabilityAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8253`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `AntennaManufacturabilityAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_antenna_report` (`tools.read_antenna_report`)

**Action:** `read_reports`. Read antenna markers.

Read process-antenna and related manufacturability reports.

### `list_antenna_violations` (`tools.list_antenna_violations`)

**Action:** `read_reports`. List antenna violations by net and gate.

List nets/pins violating antenna ratio rules.

### `list_via_reliability_risks` (`tools.list_via_reliability_risks`)

**Action:** `read_reports`. List vias that fail the reliability rule.

List via stacks with reliability (current density / stress) risk.

### `list_density_violations` (`tools.list_density_violations`)

**Action:** `read_reports`. List density windows that fail.

List metal/via density window violations.

### `list_patterning_risks` (`tools.list_patterning_risks`)

**Action:** `read_reports`. List patterning and manufacturability markers.

List lithography/patterning risks (e.g. forbidden pitches).

### `propose_diode_insertion` (`tools.propose_diode_insertion`)

**Action:** `publish_finding`. Publish a diode insertion and the electrical load it adds.

Propose antenna diode insertion near a vulnerable gate.

### `propose_antenna_jumper` (`tools.propose_antenna_jumper`)

**Action:** `publish_finding`. Publish a jumper and the layer it uses.

Propose a metal jumper that breaks a long antenna collector.

### `propose_antenna_layer_hop` (`tools.propose_antenna_layer_hop`)

**Action:** `publish_finding`. Publish a layer hop for one antenna net.

Propose hopping to another layer to discharge antenna area.

### `apply_antenna_fix` (`tools.apply_antenna_fix`)

**Action:** `write_candidate`. Apply one diode, jumper, layer, or via fix on an isolated candidate. Adapter target: OpenROAD repair_antennas.

Apply one antenna/manufacturability fix on an isolated candidate.

### `run_antenna_check` (`tools.run_antenna_check`)

**Action:** `submit_tool_job`. Re-run the antenna check. Adapter target: OpenROAD check_antennas.

Re-run antenna checks (OpenROAD repair_antennas / check flow).

### `verify_antenna_electrical_impact` (`tools.verify_antenna_electrical_impact`)

**Action:** `submit_tool_job`. Check input capacitance, delay, and noise after the fix.

Verify the fix did not create new electrical failures.

### `report_antenna_timing_side_effect` (`tools.report_antenna_timing_side_effect`)

**Action:** `read_reports`. Report the timing change caused by the fix.

Report timing side effects of diode/jumper/layer-hop fixes.

### `flag_unchecked_antenna_fix` (`tools.flag_unchecked_antenna_fix`)

**Action:** `publish_finding`. Publish a fix that has no electrical side-effect check.

Finding: a fix was applied without re-checking antenna rules.

### `record_antenna_rule_deck` (`tools.record_antenna_rule_deck`)

**Action:** `publish_finding`. Record the antenna rule deck and the candidate it graded.

Record the antenna/density rule deck and tool versions used.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `canonical_source`, `open_findings`, `experiments`, `gates`, `decisions`.
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
