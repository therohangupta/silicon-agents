"""
Per-plan execution world-state reconstruction for agent task context.

When the Executor dispatches a task to an agent, it attaches an
``ExecutionContextSnapshot`` describing what has already happened in the plan:
completed task summaries, free-form world facts (result messages), and
artifact references produced by prior tasks.

``ExecutionContext`` builds that snapshot by reading durable task-execution
rows from ``AgentInstanceRegistry.list_task_executions`` and filtering out
in-flight / non-terminal dispatch rows (those still marked
``dispatch_state == "dispatched"`` or lacking a result message/success flag).

This module does not mutate the registry; it is a read-only view used by
``executor.executor.Executor._start_task_inner``.
"""

# Postpone evaluation of annotations so forward refs / modern typing work on
# older Python runtimes without quotes everywhere.
from __future__ import annotations

# Any is used for loosely-typed result dict payloads from the registry.
from typing import Any

# Snapshot / summary / artifact models defined by the agent SDK contract that
# agent task servers expect inside AgentTaskRequest.context.
from packages.agent_sdk.src.models import ArtifactRef, ExecutionContextSnapshot, TaskSummary
# Registry provides list_task_executions(plan_id) for durable execution rows.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry


class ExecutionContext:
    """
    Structured per-plan world state reconstructed from task executions.

    Instances are cheap to construct: they only store the registry handle and
    plan id. The expensive work happens in ``snapshot()``, which scans all
    execution rows for the plan and projects them into SDK models suitable
    for inclusion in an ``AgentTaskRequest``.
    """

    def __init__(self, registry: AgentInstanceRegistry, plan_id: int):
        """
        Bind this context builder to a registry and plan.

        Args:
            registry: Fleet registry used to list task execution records.
            plan_id: Plan whose historical executions form the world state.
        """
        # Keep the registry for async queries inside snapshot().
        self.registry = registry
        # Scope all reads to this plan's execution history.
        self.plan_id = plan_id

    async def snapshot(self) -> ExecutionContextSnapshot:
        """
        Build an ``ExecutionContextSnapshot`` from persisted task executions.

        Skips rows that are still only dispatch acknowledgements (no terminal
        result) and rows whose result dict lacks both ``message`` and
        ``success`` keys (treated as incomplete). For each accepted row, appends
        a ``TaskSummary``, optionally a world-fact string from the message,
        and any parseable ``artifact_refs`` entries.

        Returns:
            An ``ExecutionContextSnapshot`` with plan summary text, completed
            task summaries, world facts, and available artifact refs.
        """
        # Load all recorded executions for this plan from the registry/DB.
        executions = await self.registry.list_task_executions(self.plan_id)
        # Accumulators projected into the final snapshot fields.
        completed_tasks: list[TaskSummary] = []
        world_facts: list[str] = []
        available_artifacts: list[ArtifactRef] = []
        # Walk every execution row and decide whether it is terminal enough
        # to contribute to agent context for subsequent tasks.
        for execution in executions:
            # Result payload may be missing; normalize to empty dict.
            result: dict[str, Any] = execution.get("result") or {}
            # Skip pure dispatch markers — task has not finished yet.
            if isinstance(result, dict) and result.get("dispatch_state") == "dispatched":
                continue
            # Skip incomplete result shapes that lack success/message signals.
            if isinstance(result, dict) and "message" not in result and "success" not in result:
                continue
            # Prefer the agent-provided message; empty string if absent.
            message = str(result.get("message", ""))
            # Artifacts map (legacy) is retained on TaskSummary for clients.
            artifacts = result.get("artifacts") or {}
            # Project a compact TaskSummary for the snapshot's completed list.
            completed_tasks.append(TaskSummary(
                task_id=execution["task_id"],
                # Truncate long messages for the description field.
                description=message[:200] or f"Task {execution['task_id']}",
                agent_id=execution.get("agent_id"),
                result_summary=message,
                artifacts=artifacts,
            ))
            # Non-empty messages become free-form world facts for the LLM agent.
            if message:
                world_facts.append(message)
            # Structured artifact refs (if present) are validated into models.
            for ref_data in result.get("artifact_refs") or []:
                if isinstance(ref_data, dict):
                    try:
                        # Construct ArtifactRef; ignore malformed entries.
                        available_artifacts.append(ArtifactRef(**ref_data))
                    except Exception:
                        # Malformed refs must not abort snapshot construction.
                        pass
        # Assemble the SDK snapshot consumed by AgentTaskRequest.context.
        return ExecutionContextSnapshot(
            plan_summary=f"Plan {self.plan_id} has {len(completed_tasks)} completed task execution(s).",
            completed_tasks=completed_tasks,
            world_facts=world_facts,
            available_artifacts=available_artifacts,
        )
