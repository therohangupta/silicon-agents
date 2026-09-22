# Failure-Triage Agent (`failure_triage`)

This directory is the deployable microservice package for the **Failure-Triage Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Failure-Triage Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Cluster failures and assign a likely owner with confidence and evidence.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `failure_triage` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8222** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read logs and waveform indexes
- Publish a failure cluster

### May not

- Close an issue
- Edit RTL or the test that failed
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_failure_logs` | `read_reports` | `read_failure_logs` | Read failing simulation logs for this campaign. |
| `read_waveform_index` | `read_reports` | `read_waveform_index` | Read the waveform index for failing tests. |
| `cluster_failures` | `read_reports` | `cluster_failures` | Group failures that share a signature. |
| `extract_failure_signature` | `read_reports` | `extract_failure_signature` | Extract the first error, time, and hierarchy for one failure. |
| `separate_infrastructure_failures` | `read_reports` | `separate_infrastructure_failures` | Separate license, timeout, and compile failures from functional failures. |
| `assign_likely_owner` | `publish_finding` | `assign_likely_owner` | Name the likely owner, confidence, and evidence for a cluster. |
| `rank_clusters_by_frequency` | `read_reports` | `rank_clusters_by_frequency` | Rank clusters by how many seeds they cover. |
| `read_cluster_evidence` | `read_reports` | `read_cluster_evidence` | Read the logs and waves attached to one cluster. |
| `flag_unowned_cluster` | `publish_finding` | `flag_unowned_cluster` | Publish a cluster that has evidence but no likely owner. |
| `flag_mixed_signature_cluster` | `publish_finding` | `flag_mixed_signature_cluster` | Publish a cluster whose members do not share a signature. |
| `record_triage_confidence` | `publish_finding` | `record_triage_confidence` | Record the confidence and the evidence refs for a cluster assignment. |
| `publish_failure_cluster` | `publish_finding` | `publish_failure_cluster` | Publish the cluster id, signature, seeds, and likely owner. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/failure_triage:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `FailureTriageAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, FailureTriageAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that delegate here:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `FailureTriageAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8222`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `FailureTriageAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_failure_logs` (`tools.read_failure_logs`)

**Action:** `read_reports`. Read failing simulation logs for this campaign.

### `read_waveform_index` (`tools.read_waveform_index`)

**Action:** `read_reports`. Read the waveform index for failing tests.

### `cluster_failures` (`tools.cluster_failures`)

**Action:** `read_reports`. Group failures that share a signature.

### `extract_failure_signature` (`tools.extract_failure_signature`)

**Action:** `read_reports`. Extract the first error, time, and hierarchy for one failure.

### `separate_infrastructure_failures` (`tools.separate_infrastructure_failures`)

**Action:** `read_reports`. Separate license, timeout, and compile failures from functional failures.

### `assign_likely_owner` (`tools.assign_likely_owner`)

**Action:** `publish_finding`. Name the likely owner, confidence, and evidence for a cluster.

### `rank_clusters_by_frequency` (`tools.rank_clusters_by_frequency`)

**Action:** `read_reports`. Rank clusters by how many seeds they cover.

### `read_cluster_evidence` (`tools.read_cluster_evidence`)

**Action:** `read_reports`. Read the logs and waves attached to one cluster.

### `flag_unowned_cluster` (`tools.flag_unowned_cluster`)

**Action:** `publish_finding`. Publish a cluster that has evidence but no likely owner.

### `flag_mixed_signature_cluster` (`tools.flag_mixed_signature_cluster`)

**Action:** `publish_finding`. Publish a cluster whose members do not share a signature.

### `record_triage_confidence` (`tools.record_triage_confidence`)

**Action:** `publish_finding`. Record the confidence and the evidence refs for a cluster assignment.

### `publish_failure_cluster` (`tools.publish_failure_cluster`)

**Action:** `publish_finding`. Publish the cluster id, signature, seeds, and likely owner.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
