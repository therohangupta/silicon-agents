# Security/Reliability Agent (`security_reliability`)

This directory is the deployable microservice package for the **Security/Reliability Agent** in the fleet **architecture** stage (role `worker`).

## EDA responsibility

Security/Reliability Agent — agent class entry point.

Charter from `config.yaml`: Define threat, safety, isolation, and reliability obligations, and the verification tasks they require.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `security_reliability` |
| Stage | `architecture` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8207** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read product intent
- Write security and reliability requirements

### May not

- Waive a safety requirement
- Accept an isolation break as a performance optimization
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `define_security_obligations` | `write_candidate` | `define_security_obligations` | Write threat, isolation, and security requirements. |
| `define_threat_boundary` | `write_candidate` | `define_threat_boundary` | Write the assets and trust boundaries for one block. |
| `define_isolation_requirement` | `write_candidate` | `define_isolation_requirement` | Write an isolation rule between two domains. |
| `define_reliability_obligations` | `write_candidate` | `define_reliability_obligations` | Write safety and reliability requirements. |
| `define_fault_requirement` | `write_candidate` | `define_fault_requirement` | Write a fault detection or containment requirement. |
| `link_obligation_to_check` | `write_candidate` | `link_obligation_to_check` | Bind a security or reliability obligation to the check that closes it. |
| `read_threat_model` | `read_reports` | `read_threat_model` | Read the current threat and trust-boundary record. |
| `read_reliability_requirements` | `read_reports` | `read_reliability_requirements` | Read safety and reliability requirements for one block. |
| `check_obligation_coverage` | `read_reports` | `check_obligation_coverage` | List obligations that have no closing check. |
| `flag_missing_trust_isolation` | `publish_finding` | `flag_missing_trust_isolation` | Publish a path that crosses a trust boundary without an isolation rule. |
| `flag_untestable_safety_requirement` | `publish_finding` | `flag_untestable_safety_requirement` | Publish a safety requirement with no observable check. |
| `propose_security_verification_task` | `publish_finding` | `propose_security_verification_task` | Publish the verification task a security obligation still needs. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/security_reliability:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `SecurityReliabilityAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, SecurityReliabilityAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Stage lead(s) that delegate here:
  - [`architecture_lead`](../architecture_lead/) (port **8203**)
- Sibling agents in this folder:
  - [`architecture_lead`](../architecture_lead/) — lead, port **8203**
  - [`interface`](../interface/) — worker, port **8205**
  - [`performance_modeling`](../performance_modeling/) — worker, port **8204**
  - [`power_area_estimation`](../power_area_estimation/) — worker, port **8206**
  - [`requirements`](../requirements/) — worker, port **8202**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `SecurityReliabilityAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8207`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `SecurityReliabilityAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `define_security_obligations` (`tools.define_security_obligations`)

**Action:** `write_candidate`. Write threat, isolation, and security requirements.

### `define_threat_boundary` (`tools.define_threat_boundary`)

**Action:** `write_candidate`. Write the assets and trust boundaries for one block.

### `define_isolation_requirement` (`tools.define_isolation_requirement`)

**Action:** `write_candidate`. Write an isolation rule between two domains.

### `define_reliability_obligations` (`tools.define_reliability_obligations`)

**Action:** `write_candidate`. Write safety and reliability requirements.

### `define_fault_requirement` (`tools.define_fault_requirement`)

**Action:** `write_candidate`. Write a fault detection or containment requirement.

### `link_obligation_to_check` (`tools.link_obligation_to_check`)

**Action:** `write_candidate`. Bind a security or reliability obligation to the check that closes it.

### `read_threat_model` (`tools.read_threat_model`)

**Action:** `read_reports`. Read the current threat and trust-boundary record.

### `read_reliability_requirements` (`tools.read_reliability_requirements`)

**Action:** `read_reports`. Read safety and reliability requirements for one block.

### `check_obligation_coverage` (`tools.check_obligation_coverage`)

**Action:** `read_reports`. List obligations that have no closing check.

### `flag_missing_trust_isolation` (`tools.flag_missing_trust_isolation`)

**Action:** `publish_finding`. Publish a path that crosses a trust boundary without an isolation rule.

### `flag_untestable_safety_requirement` (`tools.flag_untestable_safety_requirement`)

**Action:** `publish_finding`. Publish a safety requirement with no observable check.

### `propose_security_verification_task` (`tools.propose_security_verification_task`)

**Action:** `publish_finding`. Publish the verification task a security obligation still needs.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `human_intent`, `requirements`, `interface_contracts`, `decisions`, `open_findings`.
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
