"""No-op EDA adapter: records the requested operation without running a tool.

This is the default process-wide binding installed by ``eda.__init__``. It
returns ``ToolObservation`` objects with ``status="not_run"`` and a
``JobHandle`` in ``not_submitted`` state. Metrics are always empty.

If ``EDA_FRAMEWORK`` is set in the environment, the summary mentions that
intended framework so operators can see a misconfiguration (framework named
but not bound). Bind a real adapter before any metric from this path is
treated as engineering evidence or promotion input.
"""

from __future__ import annotations

# Read EDA_FRAMEWORK to mention an intended-but-unbound tool in summaries.
import os
# Params typing for invoke().
from typing import Any
# Unique suffixes for noop job ids.
from uuid import uuid4

# Job handle and observation models returned to callers.
from ..schemas.messages import JobHandle, ToolObservation


class NoOpEdaAdapter:
    """Records the operation and does not run a tool.

    Bind a real adapter before any metric from this path is treated as evidence.
    Satisfies ``EdaAdapter`` structurally with ``framework="unbound"``.
    """

    # Framework name stamped on every observation from this adapter.
    framework = "unbound"

    def invoke(
        self,
        operation: str,
        params: dict[str, Any],
        *,
        agent_id: str = "",
    ) -> ToolObservation:
        """Build a not_run observation describing the skipped operation.

        Args:
            operation: Named operation the agent requested.
            params: Parameter dict; ``task_id`` (if present) is copied onto
                the job handle.
            agent_id: Optional calling agent id stamped on the observation.

        Returns:
            A ``ToolObservation`` with empty metrics, ``status="not_run"``,
            and a ``JobHandle`` whose state is ``not_submitted``.

        Side effects:
            Reads ``EDA_FRAMEWORK`` from the environment when set.

        Failures:
            None.
        """
        # Optional hint that an operator intended a real framework.
        intended = os.environ.get("EDA_FRAMEWORK", "")
        # Tailor the summary when a framework was named but never bound.
        if intended:
            summary = (
                f"Intended framework '{intended}' is not bound. "
                f"Operation '{operation}' was not executed."
            )
        else:
            summary = f"No EDA framework is bound. Operation '{operation}' was not executed."
        # Return a structured observation suitable for TaskResult.observations.
        return ToolObservation(
            framework=self.framework,
            intended_framework=intended,
            operation=operation,
            status="not_run",
            summary=summary,
            metrics={},
            job=JobHandle(
                job_id=f"noop-{uuid4().hex[:8]}",
                scheduler="none",
                task_id=str(params.get("task_id", "")),
                state="not_submitted",
            ),
            agent_id=agent_id,
        )
