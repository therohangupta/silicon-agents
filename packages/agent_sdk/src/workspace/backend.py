"""Module ``agent_sdk/src/workspace/backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Plan workspace storage backends for shared plan artifacts.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Storage backends for plan workspaces.

Each backend implements write/read/list/delete for arbitrary blobs scoped
under a plan_id namespace.  The fleet server creates one workspace per plan
execution; agents get a PlanWorkspace client backed by one of these.
"""


from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class WorkspaceBackend(ABC):
    """Abstract blob storage for plan artifacts."""

    @abstractmethod
    async def write(self, plan_id: int, path: str, data: bytes) -> str:
        """Write bytes and return a URI agents can use to load the artifact."""

    @abstractmethod
    async def read(self, plan_id: int, path: str) -> bytes:
        """Read artifact bytes by relative path within the plan workspace."""

    @abstractmethod
    async def list_paths(self, plan_id: int) -> list[str]:
        """List all relative paths stored for this plan."""

    @abstractmethod
    async def delete(self, plan_id: int, path: str) -> None:
        """Remove an artifact from the workspace."""

    @abstractmethod
    async def exists(self, plan_id: int, path: str) -> bool:
        """Check if an artifact path exists."""

    @abstractmethod
    def uri_for(self, plan_id: int, path: str) -> str:
        """Return the canonical URI for a given path (without reading)."""


class LocalWorkspaceBackend(WorkspaceBackend):
    """Stores plan artifacts on local filesystem under a root directory.

    Layout: {root}/{plan_id}/{task_id}/{filename}
    """

    def __init__(self, root: Optional[str] = None):
        """``__init__``"""
        from packages.config import WORKSPACE_STORAGE_ROOT

        self._root = Path(
            root or os.environ.get("WORKSPACE_STORAGE_ROOT") or WORKSPACE_STORAGE_ROOT
        )

    def _plan_dir(self, plan_id: int) -> Path:
        """``_plan_dir``"""
        return self._root / str(plan_id)

    def uri_for(self, plan_id: int, path: str) -> str:
        """``_plan_dir``"""
        return f"workspace://{plan_id}/{path}"

    async def write(self, plan_id: int, path: str, data: bytes) -> str:
        """``uri_for``"""
        dest = self._plan_dir(plan_id) / path
        # Call ``dest.parent.mkdir``.
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Call ``dest.write_bytes``.
        dest.write_bytes(data)
        # Hand ``self.uri_for(plan_id, path)`` back to the caller.
        return self.uri_for(plan_id, path)

    async def read(self, plan_id: int, path: str) -> bytes:
        """``read``"""
        target = self._plan_dir(plan_id) / path
        # Only when (not target.exists()).
        if not target.exists():
            # Raise ``FileNotFoundError`` to signal this failure mode to callers.
            raise FileNotFoundError(f"Artifact not found: {self.uri_for(plan_id, path)}")
        # Hand ``target.read_bytes()`` back to the caller.
        return target.read_bytes()

    async def list_paths(self, plan_id: int) -> list[str]:
        """``list_paths``"""
        plan_dir = self._plan_dir(plan_id)
        # Only when (not plan_dir.exists()).
        if not plan_dir.exists():
            # Hand ``[]`` back to the caller.
            return []
        # Local ``base`` ← plan_dir.
        base = plan_dir
        # Hand ``[str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()]`` back to the caller.
        return [str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()]

    async def delete(self, plan_id: int, path: str) -> None:
        """``delete``"""
        target = self._plan_dir(plan_id) / path
        # Only when (target.exists()).
        if target.exists():
            # Call ``target.unlink``.
            target.unlink()

    async def exists(self, plan_id: int, path: str) -> bool:
        """``exists``"""
        return (self._plan_dir(plan_id) / path).exists()


class S3WorkspaceBackend(WorkspaceBackend):
    """Stores plan artifacts in S3 under a key prefix.

    Layout: s3://{bucket}/workspaces/{plan_id}/{path}
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        prefix: str = "workspaces",
    ):
        """``callable``"""
        from packages.config import S3_BUCKET, S3_REGION, WORKSPACE_S3_BUCKET

        self._bucket = bucket or os.environ.get("WORKSPACE_S3_BUCKET") or WORKSPACE_S3_BUCKET or S3_BUCKET
        self._region = region or os.environ.get("S3_REGION") or S3_REGION
        # Bind ``_prefix`` from prefix for later use on this instance.
        self._prefix = prefix
        # Bind ``_client`` from None for later use on this instance.
        self._client = None

    def _get_client(self):
        """``_get_client``"""
        if self._client is None:
            import boto3
            # Bind ``_client`` from boto3.client("s3", region_name=self._region) for later use on this instance.
            self._client = boto3.client("s3", region_name=self._region)
        # Hand ``self._client`` back to the caller.
        return self._client

    def _key(self, plan_id: int, path: str) -> str:
        """``_key``"""
        return f"{self._prefix}/{plan_id}/{path}"

    def uri_for(self, plan_id: int, path: str) -> str:
        """``_key``"""
        return f"s3://{self._bucket}/{self._key(plan_id, path)}"

    async def write(self, plan_id: int, path: str, data: bytes) -> str:
        """``uri_for``"""
        client = self._get_client()
        # Local ``key`` ← self._key(plan_id, path).
        key = self._key(plan_id, path)
        # Call ``client.put_object``.
        client.put_object(Bucket=self._bucket, Key=key, Body=data)
        # Hand ``self.uri_for(plan_id, path)`` back to the caller.
        return self.uri_for(plan_id, path)

    async def read(self, plan_id: int, path: str) -> bytes:
        """``read``"""
        client = self._get_client()
        # Local ``key`` ← self._key(plan_id, path).
        key = self._key(plan_id, path)
        # Local ``response`` ← client.get_object(Bucket=self._bucket, Key=key).
        response = client.get_object(Bucket=self._bucket, Key=key)
        # Hand ``response["Body"].read()`` back to the caller.
        return response["Body"].read()

    async def list_paths(self, plan_id: int) -> list[str]:
        """``list_paths``"""
        client = self._get_client()
        # Local ``prefix`` ← f"{self._prefix}/{plan_id}/".
        prefix = f"{self._prefix}/{plan_id}/"
        # Local ``paginator`` ← client.get_paginator("list_objects_v2").
        paginator = client.get_paginator("list_objects_v2")
        # Local ``paths`` ← [].
        paths = []
        # Loop: for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix).
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            # Loop: for obj in page.get("Contents", []).
            for obj in page.get("Contents", []):
                # Local ``rel`` ← obj["Key"][len(prefix):].
                rel = obj["Key"][len(prefix):]
                # Call ``paths.append``.
                paths.append(rel)
        # Hand ``paths`` back to the caller.
        return paths

    async def delete(self, plan_id: int, path: str) -> None:
        """``delete``"""
        client = self._get_client()
        # Local ``key`` ← self._key(plan_id, path).
        key = self._key(plan_id, path)
        # Call ``client.delete_object``.
        client.delete_object(Bucket=self._bucket, Key=key)

    async def exists(self, plan_id: int, path: str) -> bool:
        """``exists``"""
        client = self._get_client()
        # Local ``key`` ← self._key(plan_id, path).
        key = self._key(plan_id, path)
        # Try the fallible work below.
        try:
            # Call ``client.head_object``.
            client.head_object(Bucket=self._bucket, Key=key)
            # Hand ``True`` back to the caller.
            return True
        # On except client.exceptions.NoSuchKey: recover or re-raise as appropriate.
        except client.exceptions.NoSuchKey:
            # Hand ``False`` back to the caller.
            return False
        # On except Exception: recover or re-raise as appropriate.
        except Exception:
            # Hand ``False`` back to the caller.
            return False
