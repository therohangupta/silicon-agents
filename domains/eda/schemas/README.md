# schemas

Versioned **Pydantic** contracts shared by EDA agents, **`EngineeringMemory`**, the HTTP fleet layer, planners, and tests. Models are split by concern so enums, artifacts, tasks, messages, and memory envelopes can evolve independently while **`domains.eda.schemas`** keeps a stable import surface.

Prefer **`from domains.eda.schemas import ...`** (see **`__init__.py`** / **`__all__`**) rather than deep imports into individual modules unless you are editing the schema itself.

---

## enums.py — shared closed sets

String enums serialize cleanly to JSON in memory payloads and fleet artifacts.

### TaskOutcome

What the **parent workflow** should do after a task finishes:

| Value | Fleet mapping (via **`TaskResult.to_agent_task_result`**) |
|-------|-----------------------------------------------------------|
| **`COMPLETED`**, **`PARTIALLY_COMPLETED`** | `success=True` |
| **`REPLAN_REQUIRED`**, **`UPSTREAM_CHANGE_REQUIRED`** | `replan=True` |
| Failures (`RETRYABLE_FAILURE`, `NONRETRYABLE_FAILURE`, …) | `success=False`; engineering detail stays in **`outcome`** |

Partial completion is intentional when EDA frameworks are still unbound (**`FRAMEWORK_UNBOUND`**).

### RecordType

Engineering-memory **envelope kind**. Drives:

- Default **placements** in **`memory/placements.py`**
- **Publish checks** in **`EngineeringMemory._check_publish`**
- **Context include** expansion via **`INCLUDE_TYPES`** in **`context.py`**

Examples: **`HumanIntent`**, **`Requirement`**, **`AgentFinding`**, **`ExperimentResult`**, **`Decision`**, **`GateDecision`**, **`WorkflowRevision`**, **`TaskCheckpoint`**, **`DesignBaseline`**, **`ArtifactRef`**, …

### ValidationState

Trust rank for assembly and promotion. **`REJECTED`** records are dropped in context assembly. Provisional workflow and gate records remain visible but exclude filters (e.g. **`stale_candidates`**) may remove superseded rows.

### AuthorKind

Distinguishes **`HUMAN`** vs **`AGENT`** authorship; publish rules use this (agents cannot publish human intent).

### AgentRole and ToolAction

**`AgentRole`**: **`LEAD`**, **`WORKER`**, **`VALIDATOR`** — selects **`EDAAgent.act`** branch.

**`ToolAction`**: permission verb each skill declares in `config.yaml` (read, write, run_tool, propose_workflow, emit_gate, …).

**`ROLE_ACTIONS`**: static matrix **`assert_action`** and fleet registry validation enforce — e.g. workers cannot **`PROPOSE_WORKFLOW`**, validators cannot publish requirements without policy, leads cannot **`EMIT_GATE`** in ways workers do.

### PayloadSchemaStatus

How strictly a named payload schema (**`schema_record_name`**) is registered for validation.

---

## task.py — bounded work

**Conversations are not the contract.** A **`TaskBrief`** is one bounded unit of work:

- **`objective`**, **`task_id`**, **`project_id`**
- Design fields: **`design_revision`**, **`subsystem`**, **`block`**, **`stage`**
- **`constraints`**, optional **`ResourceBudget`**
- **`allowed_actions`** / **`forbidden_actions`** for tool permission narrowing

**`TaskBrief.from_request`** builds a brief from **`AgentTaskRequest`** (embedded **`inputs["task"]`** or synthesized from loose request fields).

**`TaskResult`** is the domain answer:

- **`outcome`**, **`reason_code`**, **`summary`**
- Optional **`evidence`**, **`observations`**, **`workflow`** JSON
- **`to_agent_task_result()`** maps into SDK **`AgentTaskResult`**

---

## artifact.py — pointers, not bytes

**`ArtifactRef`** points at versioned artifact storage (path, digest, media type). Large blobs live in object/workspace storage; memory holds references. **`to_fleet_ref`** converts to the generic SDK artifact shape for gateway consumers.

---

## messages.py — workflow and tool surfaces

| Model | Role |
|-------|------|
| **`Finding`** | Structured agent finding |
| **`AgentMessage`** | Inter-agent message envelope |
| **`JobHandle`** | Async tool job reference |
| **`GateDecision`** | Validator gate payload |
| **`ExperimentRecord`** | Hypothesis, metrics, evidence |
| **`Decision`** | Recorded engineering decision |
| **`ProposedTask`** / **`WorkflowProposal`** | Lead-proposed DAG of child tasks |
| **`ToolObservation`** | Adapter/skill result (status, metrics, framework name) |

**`WorkflowProposal`** is what **`EDAAgent.plan`** publishes under **`WORKFLOW_REVISION`**. **`ToolObservation`** is what **`EdaAdapter.invoke`** and skill functions return.

---

## memory.py — envelope and context packages

### MemoryScope

Logical path under **`/programs/{project}/...`**. Empty optional segments mean “applies to whole program along that axis.” Methods:

- **`path`** — canonical string for baseline CAS keys
- **`contains(other)`** — ancestor check for query filtering

### MemoryRecord

Full **system envelope**: ids, scope, type, validation, author, evidence artifact refs, tags, lookup keys, payload dict, timestamps, schema name, etc. **`new_id(prefix)`** allocates short prefixed ids (**`mem-…`**).

### Context assembly types

| Model | Role |
|-------|------|
| **`ContextConflict`** | Subject pair surfaced when policies disagree |
| **`ContextPackage`** | Selected records, conflicts, omitted count, token estimate |
| **`ContextManifest`** | Snapshot of request parameters for audit |

### Promotion

**`PromotionResult`** reports compare-and-swap baseline promotion outcomes from **`EngineeringMemory.promote_candidate`**.

### Write policy re-exports

**`StoreCopy`**, **`StoredCopy`**, **`WritePolicy`** re-exported from **`packages.memory.policy`** so EDA callers need not import the generic kit for typed policies. Placement **defaults** remain in **`domains.eda.memory.placements`**.

---

## Module index

| File | Exports (representative) |
|------|--------------------------|
| **`enums.py`** | **`TaskOutcome`**, **`RecordType`**, **`ValidationState`**, **`AgentRole`**, **`ToolAction`**, **`ROLE_ACTIONS`** |
| **`task.py`** | **`ResourceBudget`**, **`TaskBrief`**, **`TaskResult`** |
| **`artifact.py`** | **`ArtifactRef`** |
| **`messages.py`** | Workflow, gate, experiment, **`ToolObservation`** |
| **`memory.py`** | **`MemoryScope`**, **`MemoryRecord`**, **`ContextPackage`**, **`PromotionResult`**, write-policy types |

---

## Versioning and compatibility

- Prefer additive fields with defaults on Pydantic models.
- Fleet and gateway code should tolerate unknown **`RecordType`** values only at the storage layer — domain code assumes the closed enum.
- When splitting modules, update **`schemas/__init__.py`** **`__all__`** so agent imports remain stable.

Related: [`../README.md`](../README.md), [`../memory/README.md`](../memory/README.md), [`../../../docs/OPENAPI_CONTRACT.md`](../../../docs/OPENAPI_CONTRACT.md).
