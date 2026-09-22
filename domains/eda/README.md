# eda

The **EDA domain** is the shared base every chip-design agent under `agents/` subclasses. It owns design scope, typed tasks and results, role-based tool actions, engineering-memory envelopes, context assembly, agent specs loaded from `config.yaml`, fleet selection, and HTTP binding to the generic `AgentServer`.

Concrete agents set a class-level **`AgentSpec`**, run behind **`AgentService`**, and share memory through **`open_memory`** (file store by default; **`MEMORY_BACKEND=plane`** in fleet Compose so containers share the platform memory plane).

## Module map

| Module | Responsibility |
|--------|----------------|
| `agent.py` | **`EdaAgent`**: decode task → assemble context → journal → plan or execute → journal → encode result |
| `context.py` | **`ContextService`**, **`INCLUDE_TYPES`**: map `config.yaml` include names to `RecordType` queries |
| `spec.py` | **`AgentSpec`**, **`AgentContext`**, **`ToolSpec`**, **`PlanStep`**, **`class_name_for`** |
| `registry.py` | Load/validate every `agents/**/config.yaml`; **`all_specs`**, **`get_spec`**, **`planner_catalog`** |
| `planning.py` | Build **`WorkflowSpec`** from lead `plan_steps` or `delegates_to` |
| `fleet.py` | **`select_agents`**, **`render_compose`**: fleet YAML → Docker Compose services |
| `server.py` | **`AgentService`**, **`BoundAgentRuntime`**: wire **`AgentServer`** to **`EdaAgent.handle`** |
| [`schemas/`](schemas/README.md) | Task, artifact, message, memory, enum contracts |
| [`memory/`](memory/README.md) | **`EngineeringMemory`**, placements, store bindings |
| [`eda/`](eda/README.md) | **`EdaAdapter`** protocol, no-op default, named framework factories |

Public re-exports live in **`domains.eda.__init__`** (`EdaAgent`, `ContextService`, `EngineeringMemory`, `open_memory`, catalog helpers, `AgentService`, …).

---

## EdaAgent lifecycle

`EdaAgent` extends the SDK **`TaskLifecycle`** hook sequence. The HTTP layer forwards **`AgentTaskRequest`** objects; this class owns EDA vocabulary end to end.

```text
AgentTaskRequest
    → decode_task()        TaskSpec.from_request
    → prepare_task()       idempotency_key, default stage from spec
    → assemble_context()   ContextService.assemble(task, spec.context)
    → journal_started()    append TASK_CHECKPOINT (provisional)
    → execute_task()       act() → plan (LEAD) or execute_tools (WORKER/VALIDATOR)
    → journal_finished()   append TASK_CHECKPOINT with TaskResult payload
    → encode_result()      TaskResult.to_agent_task_result()
AgentTaskResult
```

### Role behavior

| Role | Primary path | Memory side effects |
|------|--------------|---------------------|
| **LEAD** | `plan()` builds **`WorkflowSpec`**, publishes **`WORKFLOW_REVISION`** (provisional), may invoke declared tools | Workflow revision + tool observations |
| **WORKER** | `execute_tools()` runs skills from `tools.py` via **`SkillRegistry`** | Tool observations; outcome often **`PARTIALLY_COMPLETED`** / **`FRAMEWORK_UNBOUND`** when adapter is no-op |
| **VALIDATOR** | Same as worker, then **`_validator_result`** publishes provisional **`GATE_DECISION`** | Gate record does not grade the candidate until a real framework is bound |

### Permissions

Each tool declares a **`ToolAction`** in `config.yaml`. **`assert_action`** enforces:

1. The action is allowed for the agent's **`AgentRole`** (**`ROLE_ACTIONS`** matrix in `schemas/enums.py`).
2. The action is not in the task's forbidden list.
3. When the task sets an allow-list, the action appears on it.

Violations raise **`AgentPermissionError`**, converted to **`NONRETRYABLE_FAILURE`** / **`PERMISSION_DENIED`** at the HTTP boundary (not a 500).

### Construction and testing

- **`EdaAgent.read_spec(directory)`** loads **`AgentSpec`** via **`registry.load_spec`**.
- Inject **`engineering_memory`** and **`context_service`** in tests so multiple agents share one store.
- **`AgentService`** injects the process **`SkillRegistry`** that loaded the agent's `tools.py` at startup.

### Failure mapping

| Exception / condition | TaskOutcome | reason_code |
|----------------------|-------------|-------------|
| `AgentPermissionError` | `NONRETRYABLE_FAILURE` | `PERMISSION_DENIED` |
| `TimeoutError` | `RETRYABLE_FAILURE` | `TIMEOUT` |
| Other execution errors | `NONRETRYABLE_FAILURE` | `EXECUTION_ERROR` |

Missing **`spec`** on the subclass raises **`TypeError`** at construction. Missing **`tools.py`** raises **`ImportError`** when tools load.

---

## Engineering memory (summary)

Agents must use **`EngineeringMemory`** (via **`open_memory`**) rather than raw store clients so envelope invariants stay centralized. See [`memory/README.md`](memory/README.md) for backends and placements.

| Path | Use |
|------|-----|
| **`append`** | Task-local journal (started/finished checkpoints); no publish policy |
| **`publish`** / **`write`** | Visible records; **`_check_publish`** + idempotency + **`compile_policy`** |
| **`promote_candidate`** | Only way to move **`DESIGN_BASELINE`** (compare-and-swap + gate checks) |
| **`query`** / **`search`** | Context assembly and operator tooling |

**`MemoryScope`** (project, revision, subsystem, block, stage) defines the logical `/programs/...` path used for filtering and baseline keys.

Backend selection: **`MEMORY_BACKEND`** or **`SILICON_MEMORY_BACKEND`** → `memory`, `postgres`, `plane`, or `file` (default local file directory).

---

## Schemas (summary)

Versioned Pydantic models under [`schemas/`](schemas/README.md) separate transport, memory envelopes, and workflow messages:

- **`TaskSpec`** / **`TaskResult`**: bounded work unit and domain answer (outcome, reason, observations, optional workflow JSON).
- **`MemoryRecord`**: system envelope; agent owns the payload dict.
- **`WorkflowSpec`**, **`GateDecision`**, **`ToolObservation`**: planner and adapter surfaces.

Import from **`domains.eda.schemas`** for stable call sites.

---

## Catalog and fleet

- **`registry.validate_catalog()`** — structural checks over all `agents/**` (used by **`scripts/check_agents.py`**).
- **`fleet.select_agents(fleet_yaml)`** — resolves directory paths to **`SelectedAgent`** rows with host port shifting from **`config/platform.yaml`**.
- **`fleet.render_compose(...)`** — writes agent Compose services (image, env, **`MEMORY_BACKEND=plane`**, working dir).

Fleet files list paths under **`agents:`**; see [`../../fleets/README.md`](../../fleets/README.md).

---

## Framework adapters

Agent tools must not shell out to OpenROAD/Yosys directly. They call **`get_eda_adapter().invoke(...)`** (see [`eda/README.md`](eda/README.md)). Until **`bind_eda_adapter`** installs a real implementation, **`NoOpEdaAdapter`** returns **`status=not_run`** — not engineering evidence.

---

## Quick reference: wiring a new catalog agent

1. Add `agents/<domain>/<stage>/<name>/` with `config.yaml`, `agent.py` (subclass **`EdaAgent`**, **`spec = EdaAgent.read_spec(__file__)` or equivalent), `tools.py`, `server.py`, Dockerfile.
2. Ensure **`registry`** can load the spec (context **`include`** + **`precedence`** required).
3. Add the directory to a fleet YAML and run **`scripts/startup.sh`** or **`scripts/fleet_select.py render`**.

Related: [`../../docs/RUN.md`](../../docs/RUN.md), [`../README.md`](../README.md).
