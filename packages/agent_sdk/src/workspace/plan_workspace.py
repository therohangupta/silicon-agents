"""Module ``agent_sdk/src/workspace/plan_workspace.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Plan workspace storage backends for shared plan artifacts.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

PlanWorkspace — the agent-facing API for reading/writing plan-scoped artifacts.

Each task invocation receives a PlanWorkspace scoped to the current plan.
Agents use `publish()` to write large artifacts and `load()` to read artifacts
from prior tasks.  The fleet executor collects published refs after each task
and makes them available to subsequent tasks via `context.available_artifacts`.
"""


from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from ..models import ArtifactRef
from .backend import LocalWorkspaceBackend, S3WorkspaceBackend, WorkspaceBackend

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


def _create_backend_from_uri(workspace_uri: str) -> tuple[WorkspaceBackend, int]:
    """Parse a workspace URI and return (backend, plan_id).

    Supported URI formats:
      # Call ``- workspace://{plan_id}          → LocalWorkspaceBackend``.
      - workspace://{plan_id}          → LocalWorkspaceBackend (default root)
      - workspace://{plan_id}?root=/x  → LocalWorkspaceBackend with custom root
      - s3://{bucket}/workspaces/{plan_id}  → S3WorkspaceBackend
    """
    if workspace_uri.startswith("s3://"):
        # Local ``parts`` ← workspace_uri[len("s3://"):].split("/").
        parts = workspace_uri[len("s3://"):].split("/")
        # Local ``bucket`` ← parts[0].
        bucket = parts[0]
        # Local ``plan_id`` ← int(parts[-1]) if parts[-1].isdigit() else 0.
        plan_id = int(parts[-1]) if parts[-1].isdigit() else 0
        # Hand ``S3WorkspaceBackend(bucket=bucket), plan_id`` back to the caller.
        return S3WorkspaceBackend(bucket=bucket), plan_id

    # workspace://{plan_id}[?root=...]
    stripped = workspace_uri.replace("workspace://", "")
    # Call ``plan_str, _, query = stripped.partition``.
    plan_str, _, query = stripped.partition("?")
    # Local ``plan_id`` ← int(plan_str) if plan_str.isdigit() else 0.
    plan_id = int(plan_str) if plan_str.isdigit() else 0
    # Local ``root`` ← None.
    root = None
    # Only when (query).
    if query:
        # Loop: for kv in query.split("&").
        for kv in query.split("&"):
            # Only when (kv.startswith("root=")).
            if kv.startswith("root="):
                # Local ``root`` ← kv[len("root="):].
                root = kv[len("root="):]
    # Hand ``LocalWorkspaceBackend(root=root), plan_id`` back to the caller.
    return LocalWorkspaceBackend(root=root), plan_id


class PlanWorkspace:
    """Agent-facing workspace client for a single plan execution.

    Agents never construct this directly — it is provided by the runtime
    from the AgentTaskRequest.workspace_uri field.
    """

    def __init__(
        self,
        plan_id: int,
        task_id: str,
        agent_id: str,
        backend: Optional[WorkspaceBackend] = None,
        workspace_uri: Optional[str] = None,
    ):
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self.plan_id = plan_id
        # Bind ``task_id`` from task_id for later use on this instance.
        self.task_id = task_id
        # Bind ``agent_id`` from agent_id for later use on this instance.
        self.agent_id = agent_id
        self._published: list[ArtifactRef] = []

        # Only when (backend).
        if backend:
            # Bind ``_backend`` from backend for later use on this instance.
            self._backend = backend
        elif workspace_uri:
            # Call ``self._backend, _ = _create_backend_from_uri``.
            self._backend, _ = _create_backend_from_uri(workspace_uri)
        else:
            # Bind ``_backend`` from LocalWorkspaceBackend() for later use on this instance.
            self._backend = LocalWorkspaceBackend()

    @classmethod
    def from_request(cls, request) -> "PlanWorkspace":
        """Factory from an AgentTaskRequest."""
        from ..models import AgentTaskRequest
        req: AgentTaskRequest = request
        # Local ``backend`` ← None.
        backend = None
        # Only when (req.workspace_uri).
        if req.workspace_uri:
            # Call ``backend, _ = _create_backend_from_uri``.
            backend, _ = _create_backend_from_uri(req.workspace_uri)
        # Hand ``cls(`` back to the caller.
        return cls(
            # Local ``plan_id`` ← req.plan_id or 0,.
            plan_id=req.plan_id or 0,
            # Local ``task_id`` ← req.task_id,.
            task_id=req.task_id,
            # Local ``agent_id`` ← "",.
            agent_id="",
            # Local ``backend`` ← backend,.
            backend=backend,
            # Local ``workspace_uri`` ← req.workspace_uri,.
            workspace_uri=req.workspace_uri,
        )

    @property
    def published_refs(self) -> list[ArtifactRef]:
        """Refs published during this task execution (for executor to collect)."""
        return list(self._published)

    def _artifact_path(self, name: str) -> str:
        """Relative path within plan workspace: {task_id}/{name}"""
        return f"{self.task_id}/{name}"

    async def publish(
        self,
        name: str,
        data: bytes,
        *,
        format: str = "json",
        schema_hint: Optional[dict[str, Any]] = None,
        description: str = "",
    ) -> ArtifactRef:
        """Write an artifact to the plan workspace and return its ref.

        The ref is automatically collected by the executor and made available
        to downstream agents in context.available_artifacts.
        """
        path = self._artifact_path(name)
        # Local ``uri`` ← await self._backend.write(self.plan_id, path, data).
        uri = await self._backend.write(self.plan_id, path, data)
        # Local ``ref`` ← ArtifactRef(.
        ref = ArtifactRef(
            # Local ``uri`` ← uri,.
            uri=uri,
            # Local ``name`` ← name,.
            name=name,
            # Local ``format`` ← format,.
            format=format,
            # Local ``size_bytes`` ← len(data),.
            size_bytes=len(data),
            # Local ``schema_hint`` ← schema_hint or {},.
            schema_hint=schema_hint or {},
            # Local ``description`` ← description,.
            description=description,
            # Local ``producer_task_id`` ← self.task_id,.
            producer_task_id=self.task_id,
            # Local ``producer_agent_id`` ← self.agent_id,.
            producer_agent_id=self.agent_id,
            # Local ``created_at`` ← datetime.now(timezone.utc),.
            created_at=datetime.now(timezone.utc),
        )
        # Call ``self._published.append``.
        self._published.append(ref)
        # Hand ``ref`` back to the caller.
        return ref

    async def publish_file(
        self,
        name: str,
        file_path: str,
        *,
        format: Optional[str] = None,
        schema_hint: Optional[dict[str, Any]] = None,
        description: str = "",
    ) -> ArtifactRef:
        """Publish a local file to the plan workspace."""
        from pathlib import Path as _P
        # Local ``p`` ← _P(file_path).
        p = _P(file_path)
        # Local ``data`` ← p.read_bytes().
        data = p.read_bytes()
        # Local ``fmt`` ← format or p.suffix.lstrip(".") or "bin".
        fmt = format or p.suffix.lstrip(".") or "bin"
        # Hand ``await self.publish(name, data, format=fmt, schema_hint=schema_hint, de…`` back to the caller.
        return await self.publish(name, data, format=fmt, schema_hint=schema_hint, description=description)

    async def load(self, ref: ArtifactRef) -> bytes:
        """Load artifact bytes from a ref (typically from context.available_artifacts)."""
        path = f"{ref.producer_task_id}/{ref.name}"
        # Hand ``await self._backend.read(self.plan_id, path)`` back to the caller.
        return await self._backend.read(self.plan_id, path)

    async def load_json(self, ref: ArtifactRef) -> Any:
        """Load and JSON-decode an artifact."""
        data = await self.load(ref)
        # Hand ``json.loads(data)`` back to the caller.
        return json.loads(data)

    async def list_artifacts(self) -> list[str]:
        """List all artifact paths in the current plan workspace."""
        return await self._backend.list_paths(self.plan_id)

    async def exists(self, name: str) -> bool:
        """Check if a specific artifact exists in this task's slot."""
        path = self._artifact_path(name)
        # Hand ``await self._backend.exists(self.plan_id, path)`` back to the caller.
        return await self._backend.exists(self.plan_id, path)
