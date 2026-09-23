# Verification stage agents

This directory groups **verification**-stage agents. Pre-silicon verification: UVM environments, stimulus, assertions/formal, coverage, regression, triage, and reproduction feed an independent verification validator.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Verification Lead (`verification_lead`) | `lead` | **8215** | [`verification_lead/`](verification_lead/) |
| UVM Environment Agent (`uvm_environment`) | `worker` | **8216** | [`uvm_environment/`](uvm_environment/) |
| Reference Model Agent (`reference_model`) | `worker` | **8217** | [`reference_model/`](reference_model/) |
| Assertion/Formal Agent (`assertion_formal`) | `worker` | **8218** | [`assertion_formal/`](assertion_formal/) |
| Stimulus Agent (`stimulus`) | `worker` | **8219** | [`stimulus/`](stimulus/) |
| Coverage Agent (`coverage`) | `worker` | **8220** | [`coverage/`](coverage/) |
| Regression Agent (`regression`) | `worker` | **8221** | [`regression/`](regression/) |
| Failure-Triage Agent (`failure_triage`) | `worker` | **8222** | [`failure_triage/`](failure_triage/) |
| Reproduction Agent (`reproduction`) | `worker` | **8223** | [`reproduction/`](reproduction/) |
| Verification Validator (`verification_validator`) | `validator` | **8224** | [`verification_validator/`](verification_validator/) |

## Lead delegation graph

### `verification_lead` (port **8215**)

Own the verification plan and closure workflow for one pinned RTL revision. Do not personally write every test or inspect every waveform.

May schedule:
- [`uvm_environment`](uvm_environment/) — UVM Environment Agent (**8216**)
- [`reference_model`](reference_model/) — Reference Model Agent (**8217**)
- [`assertion_formal`](assertion_formal/) — Assertion/Formal Agent (**8218**)
- [`stimulus`](stimulus/) — Stimulus Agent (**8219**)
- [`regression`](regression/) — Regression Agent (**8221**)
- [`coverage`](coverage/) — Coverage Agent (**8220**)
- [`failure_triage`](failure_triage/) — Failure-Triage Agent (**8222**)
- [`reproduction`](reproduction/) — Reproduction Agent (**8223**)
- [`verification_validator`](verification_validator/) — Verification Validator (**8224**)

Validators:
- `verification_validator`

## Suggested workflow (mental model)

1. **verification_lead** plans environments, regressions, and closure strategy.
2. **uvm_environment**, **stimulus**, **assertion_formal**, and **reference_model** build checkers.
3. **coverage**, **regression**, **failure_triage**, and **reproduction** close the loop.
4. **verification_validator** independently grades verification signoff.

## Shared package layout (every child)

| File | Role |
|------|------|
| `config.yaml` | Manifest: identity, boundaries, port, skills, memory, telemetry, context. |
| `agent.py` | Thin `EDAAgent` subclass loading sibling YAML into `spec`. |
| `tools.py` | Skill contracts returning `tool_observation` until adapters bind. |
| `server.py` | `AgentService` FastAPI bootstrap (`/health`, `/tasks/execute`). |
| `Dockerfile` / `requirements.txt` | Container and Python deps for the HTTP surface. |
| `README.md` | Per-agent charter, skills, boundaries, boot path, and related agents. |

## Boot path (all children)

1. Compose or `python server.py` starts the container/process.
2. `server.py` loads `config.yaml` and the agent class into `AgentService`.
3. Orchestrator (or a lead's delegated workflow) POSTs to `/tasks/execute` with a skill id.
4. `EDAAgent.handle` journals, assembles context, and invokes the matching `tools.py` callable.
5. Observations and findings land in engineering memory and telemetry streams.

## Independent validators in this stage

- [`verification_validator`](verification_validator/) (port **8224**): Independently decide whether the verification contract passes for one candidate.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/runtime/agent.py`, `domains/eda/runtime/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8215** — `verification_lead` (lead)
- **8216** — `uvm_environment` (worker)
- **8217** — `reference_model` (worker)
- **8218** — `assertion_formal` (worker)
- **8219** — `stimulus` (worker)
- **8220** — `coverage` (worker)
- **8221** — `regression` (worker)
- **8222** — `failure_triage` (worker)
- **8223** — `reproduction` (worker)
- **8224** — `verification_validator` (validator)

## Child agent charters

### [`verification_lead`](verification_lead/) (port **8215**, `lead`)

Own the verification plan and closure workflow for one pinned RTL revision. Do not personally write every test or inspect every waveform.

- **Skills in manifest:** 18 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `uvm_environment`, `reference_model`, `assertion_formal`, `stimulus`, `regression`, `coverage`, `failure_triage`, `reproduction`, `verification_validator`.

### [`uvm_environment`](uvm_environment/) (port **8216**, `worker`)

Generate and maintain drivers, monitors, scoreboards, and sequences for one block.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`reference_model`](reference_model/) (port **8217**, `worker`)

Produce an executable behavioral reference model from the specification.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`assertion_formal`](assertion_formal/) (port **8218**, `worker`)

Create properties and assumptions, and submit formal proof tasks.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`stimulus`](stimulus/) (port **8219**, `worker`)

Create directed tests and constrained-random sequences aimed at coverage holes.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`coverage`](coverage/) (port **8220**, `worker`)

Write the coverage model from requirements, then analyze code, functional, and assertion coverage and list meaningful holes.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`regression`](regression/) (port **8221**, `worker`)

Select seeds, shard the workload, and run a reproducible regression.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`failure_triage`](failure_triage/) (port **8222**, `worker`)

Cluster failures and assign a likely owner with confidence and evidence.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`reproduction`](reproduction/) (port **8223**, `worker`)

Produce a minimal stable reproduction and a waveform slice for one failure cluster.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`verification_validator`](verification_validator/) (port **8224**, `validator`)

Independently decide whether the verification contract passes for one candidate.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own the verification plan and closure workflow for one pinned RTL revision. Do not persona | `verification_lead` |
| Generate and maintain drivers, monitors, scoreboards, and sequences for one block. | `uvm_environment` |
| Produce an executable behavioral reference model from the specification. | `reference_model` |
| Create properties and assumptions, and submit formal proof tasks. | `assertion_formal` |
| Create directed tests and constrained-random sequences aimed at coverage holes. | `stimulus` |
| Write the coverage model from requirements, then analyze code, functional, and assertion c | `coverage` |
| Select seeds, shard the workload, and run a reproducible regression. | `regression` |
| Cluster failures and assign a likely owner with confidence and evidence. | `failure_triage` |
| Produce a minimal stable reproduction and a waveform slice for one failure cluster. | `reproduction` |
| Independently decide whether the verification contract passes for one candidate. | `verification_validator` |
