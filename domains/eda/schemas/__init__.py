"""EDA schema package: tasks, artifacts, messages, memory envelopes, and enums.

These Pydantic models are the shared contracts between agents, engineering
memory, the HTTP fleet layer, and planners. They deliberately separate:

* **Enums** (``enums.py``) — outcomes, record types, validation states, roles,
  tool actions, and the ``ROLE_ACTIONS`` permission matrix.
* **Artifacts** (``artifact.py``) — versioned file pointers whose bytes live
  in artifact storage, not in the envelope.
* **Tasks** (``task.py``) — bounded work units and results, with conversion
  helpers to and from fleet ``AgentTaskRequest`` / ``AgentTaskResult``.
* **Messages** (``messages.py``) — findings, gates, experiments, decisions,
  workflows, job handles, and tool observations.
* **Memory** (``memory.py``) — ``MemoryScope``, ``MemoryRecord``, context
  packages/manifests, promotion results, and re-exported write-policy types.

Importing ``domains.eda.schemas`` re-exports the common symbols listed in
``__all__``. Prefer this package import in agent code so call sites stay
stable when modules are split further.
"""

from __future__ import annotations

# Versioned pointer to bytes stored outside the memory envelope.
from .artifact import ArtifactRef
# Outcomes, record kinds, roles, actions, and the role→action matrix.
from .enums import (
    ROLE_ACTIONS,
    AgentRole,
    AuthorKind,
    PayloadSchemaStatus,
    RecordType,
    TaskOutcome,
    ToolAction,
    ValidationState,
)
# Scope, record envelope, context package types, and write-policy re-exports.
from .memory import (
    ContextConflict,
    ContextManifest,
    ContextPackage,
    MemoryRecord,
    MemoryScope,
    PromotionResult,
    StoreCopy,
    StoredCopy,
    WritePolicy,
    new_id,
)
# Inter-agent and tool-facing payload models.
from .messages import (
    AgentMessage,
    Decision,
    ExperimentRecord,
    Finding,
    GateDecision,
    JobHandle,
    ToolObservation,
    WorkflowSpec,
    WorkflowTask,
)
# Task contract, resource budget, and result conversion helpers.
from .task import ResourceBudget, TaskResult, TaskSpec

# Public surface for ``from domains.eda.schemas import ...``.
__all__ = [
    "ROLE_ACTIONS",
    "AgentMessage",
    "AgentRole",
    "ArtifactRef",
    "AuthorKind",
    "ContextConflict",
    "ContextManifest",
    "ContextPackage",
    "Decision",
    "ExperimentRecord",
    "Finding",
    "GateDecision",
    "JobHandle",
    "MemoryRecord",
    "MemoryScope",
    "PayloadSchemaStatus",
    "PromotionResult",
    "RecordType",
    "ResourceBudget",
    "StoreCopy",
    "StoredCopy",
    "TaskOutcome",
    "TaskResult",
    "TaskSpec",
    "ToolAction",
    "ToolObservation",
    "ValidationState",
    "WorkflowSpec",
    "WritePolicy",
    "WorkflowTask",
    "new_id",
]
