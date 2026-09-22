# SI/Noise Repair Agent (`si_noise_repair`)

This directory is the deployable microservice package for the **SI/Noise Repair Agent** in the fleet **routing** stage (role `worker`).

## EDA responsibility

Analyze coupling, crosstalk, and glitches, apply a repair on an isolated candidate, and verify it against noise and timing limits.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `si_noise_repair` |
| Stage | `routing` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8252** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read noise reports
- Apply spacing, shielding, or layer changes on an isolated candidate
- Submit a noise and timing check of that candidate

### May not

- Edit victim logic
- Claim a repair is closed without a noise and timing check
- Edit the canonical route
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_noise_report` | `read_reports` | `read_noise_report` | Read the noise report for this candidate. |
| `list_aggressor_victim_pairs` | `read_reports` | `list_aggressor_victim_pairs` | List aggressor and victim pairs over the noise limit. |
| `classify_crosstalk_delay` | `read_reports` | `classify_crosstalk_delay` | Classify crosstalk delay on one victim. |
| `classify_glitch` | `read_reports` | `classify_glitch` | Classify glitches on one victim. |
| `propose_spacing_repair` | `publish_finding` | `propose_spacing_repair` | Publish a spacing change and the tracks it consumes. |
| `propose_shield` | `publish_finding` | `propose_shield` | Publish a shield net and the layer it uses. |
| `propose_noise_layer_change` | `publish_finding` | `propose_noise_layer_change` | Publish a layer change for one victim or aggressor. |
| `apply_noise_repair` | `write_candidate` | `apply_noise_repair` | Apply one spacing, shield, or layer change on an isolated candidate. |
| `verify_noise_after_repair` | `submit_tool_job` | `verify_noise_after_repair` | Re-run noise analysis on the repaired candidate. |
| `report_noise_timing_impact` | `read_reports` | `report_noise_timing_impact` | Report setup and hold change caused by the noise repair. |
| `flag_noise_still_over_limit` | `publish_finding` | `flag_noise_still_over_limit` | Publish a pair that is still over the noise limit. |
| `flag_unverified_noise_repair` | `publish_finding` | `flag_unverified_noise_repair` | Publish a repair that has no noise or timing check. |
| `record_si_tool_version` | `publish_finding` | `record_si_tool_version` | Record the SI tool, version, and limits used. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/si_noise_repair:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `SiNoiseRepairAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, SiNoiseRepairAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (routing specialists under `routing/`).
- Stage lead(s) that delegate here:
  - [`routing_lead`](../routing_lead/) (port **8249**)
- Sibling agents in this folder:
  - [`antenna_manufacturability`](../antenna_manufacturability/) — worker, port **8253**
  - [`detailed_routing_repair`](../detailed_routing_repair/) — worker, port **8251**
  - [`global_routing`](../global_routing/) — worker, port **8250**
  - [`routing_lead`](../routing_lead/) — lead, port **8249**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `SiNoiseRepairAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8252`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `SiNoiseRepairAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_noise_report` (`tools.read_noise_report`)

**Action:** `read_reports`. Read the noise report for this candidate.

Read the SI/noise analysis report for this routed candidate.

### `list_aggressor_victim_pairs` (`tools.list_aggressor_victim_pairs`)

**Action:** `read_reports`. List aggressor and victim pairs over the noise limit.

List coupled aggressor/victim net pairs that exceed noise limits.

### `classify_crosstalk_delay` (`tools.classify_crosstalk_delay`)

**Action:** `read_reports`. Classify crosstalk delay on one victim.

Classify delay-pushout or speedup on a victim due to crosstalk.

### `classify_glitch` (`tools.classify_glitch`)

**Action:** `read_reports`. Classify glitches on one victim.

Classify static/dynamic glitch noise on a victim net.

### `propose_spacing_repair` (`tools.propose_spacing_repair`)

**Action:** `publish_finding`. Publish a spacing change and the tracks it consumes.

Propose increasing spacing (and track cost) to cut coupling.

### `propose_shield` (`tools.propose_shield`)

**Action:** `publish_finding`. Publish a shield net and the layer it uses.

Propose inserting a grounded/power shield net between aggressor and victim.

### `propose_noise_layer_change` (`tools.propose_noise_layer_change`)

**Action:** `publish_finding`. Publish a layer change for one victim or aggressor.

Propose moving a net to another metal layer to reduce coupling.

### `apply_noise_repair` (`tools.apply_noise_repair`)

**Action:** `write_candidate`. Apply one spacing, shield, or layer change on an isolated candidate.

### `verify_noise_after_repair` (`tools.verify_noise_after_repair`)

**Action:** `submit_tool_job`. Re-run noise analysis on the repaired candidate.

Re-run noise analysis after the SI repair.

### `report_noise_timing_impact` (`tools.report_noise_timing_impact`)

**Action:** `read_reports`. Report setup and hold change caused by the noise repair.

Report setup/hold impact of the SI repair.

### `flag_noise_still_over_limit` (`tools.flag_noise_still_over_limit`)

**Action:** `publish_finding`. Publish a pair that is still over the noise limit.

Finding: a pair remains over the noise limit after repair.

### `flag_unverified_noise_repair` (`tools.flag_unverified_noise_repair`)

**Action:** `publish_finding`. Publish a repair that has no noise or timing check.

Finding: a repair was applied without noise or timing re-check.

### `record_si_tool_version` (`tools.record_si_tool_version`)

**Action:** `publish_finding`. Record the SI tool, version, and limits used.

Record SI tool, version, and limit deck for provenance.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
