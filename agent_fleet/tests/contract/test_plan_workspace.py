"""Tests for the plan workspace (artifact ref / shared memory) system.

Locks in ArtifactRef serialization, LocalWorkspaceBackend CRUD, PlanWorkspace
publish/load/load_json/from_request, URI backend parsing (local + S3), and
artifact_refs on AgentTaskResult / ExecutionContextSnapshot / AgentTaskRequest.
Each assertion documents the contract a planner/executor relies on.
"""

from __future__ import annotations

# Drive async backend methods from sync tests.
import asyncio
# JSON publish/load_json round trips.
import json
# Unused historically; kept for parity with prior imports.
import tempfile  # noqa: F401
from pathlib import Path

import pytest

# Models that carry workspace URIs and artifact refs.
from packages.agent_sdk.src.models import (
    AgentTaskRequest,
    AgentTaskResult,
    ArtifactRef,
    ExecutionContextSnapshot,
)
# Local filesystem backend under test.
from packages.agent_sdk.src.workspace.backend import LocalWorkspaceBackend
# High-level workspace client + URI factory.
from packages.agent_sdk.src.workspace.plan_workspace import PlanWorkspace, _create_backend_from_uri


# ---------------------------------------------------------------------------
# ArtifactRef model
# ---------------------------------------------------------------------------

class TestArtifactRef:
    """Contracts for the ArtifactRef pydantic model."""

    def test_create_basic(self):
        """Constructed ArtifactRef retains uri/format/size/schema_hint fields."""
        ref = ArtifactRef(
            uri="workspace://7/task_3/results.json",
            name="results.json",
            format="json",
            size_bytes=1024,
            schema_hint={"columns": {"id": "int", "name": "str"}},
            description="Query results",
            producer_task_id="3",
            producer_agent_id="db_analyst",
        )
        # URI is the durable pointer consumers load.
        assert ref.uri == "workspace://7/task_3/results.json"
        # Format hint for loaders.
        assert ref.format == "json"
        # Size metadata for UI/budgeting.
        assert ref.size_bytes == 1024
        # Nested schema_hint preserved for column-aware consumers.
        assert ref.schema_hint["columns"]["id"] == "int"

    def test_serialization_roundtrip(self):
        """model_dump(mode=json) round-trips through ArtifactRef(**data)."""
        ref = ArtifactRef(
            uri="workspace://1/2/data.pkl",
            name="data.pkl",
            format="pickle",
            size_bytes=500000,
            description="Large dataframe",
            producer_task_id="2",
        )
        # Serialize as JSON-compatible dict (fleet gRPC / HTTP boundary).
        data = ref.model_dump(mode="json")
        restored = ArtifactRef(**data)
        # URI and size survive the round trip.
        assert restored.uri == ref.uri
        assert restored.size_bytes == 500000


# ---------------------------------------------------------------------------
# LocalWorkspaceBackend
# ---------------------------------------------------------------------------

class TestLocalWorkspaceBackend:
    """Contracts for filesystem-backed workspace storage."""

    @pytest.fixture
    def backend(self, tmp_path):
        """Fresh LocalWorkspaceBackend rooted at pytest tmp_path."""
        return LocalWorkspaceBackend(root=str(tmp_path))

    def test_write_and_read(self, backend, tmp_path):
        """write returns workspace:// URI and materializes bytes on disk; read returns them."""
        plan_id = 42
        data = b"hello world"

        # Persist under plan_id/task path.
        uri = asyncio.run(backend.write(plan_id, "task_1/output.txt", data))
        # URI scheme encodes plan id and relative path.
        assert uri == "workspace://42/task_1/output.txt"
        # File exists at the expected relative path under the backend root.
        assert (tmp_path / "42" / "task_1" / "output.txt").exists()

        # Read back exact bytes.
        loaded = asyncio.run(backend.read(plan_id, "task_1/output.txt"))
        assert loaded == data

    def test_list_paths(self, backend, tmp_path):
        """list_paths returns sorted relative paths for a plan."""
        asyncio.run(backend.write(1, "a/file1.json", b"{}"))
        asyncio.run(backend.write(1, "b/file2.csv", b"x,y"))

        paths = asyncio.run(backend.list_paths(1))
        # Sorted lexicographically for stable UI/tests.
        assert sorted(paths) == ["a/file1.json", "b/file2.csv"]

    def test_exists(self, backend):
        """exists is False before write and True after."""
        assert asyncio.run(backend.exists(99, "nope.txt")) is False
        asyncio.run(backend.write(99, "yes.txt", b"data"))
        assert asyncio.run(backend.exists(99, "yes.txt")) is True

    def test_delete(self, backend):
        """delete removes a previously written object."""
        asyncio.run(backend.write(5, "temp.bin", b"\x00"))
        assert asyncio.run(backend.exists(5, "temp.bin")) is True
        asyncio.run(backend.delete(5, "temp.bin"))
        assert asyncio.run(backend.exists(5, "temp.bin")) is False

    def test_read_missing_raises(self, backend):
        """read of a missing path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            asyncio.run(backend.read(1, "missing.txt"))


# ---------------------------------------------------------------------------
# PlanWorkspace client
# ---------------------------------------------------------------------------

class TestPlanWorkspace:
    """Contracts for the high-level PlanWorkspace helper."""

    @pytest.fixture
    def workspace(self, tmp_path):
        """PlanWorkspace bound to plan 10 / task_5 / db_analyst on tmp backend."""
        backend = LocalWorkspaceBackend(root=str(tmp_path))
        return PlanWorkspace(
            plan_id=10,
            task_id="task_5",
            agent_id="db_analyst",
            backend=backend,
        )

    def test_publish(self, workspace):
        """publish writes bytes and returns an ArtifactRef with producer metadata."""
        data = json.dumps({"rows": [1, 2, 3]}).encode()
        ref = asyncio.run(workspace.publish(
            "results.json",
            data,
            format="json",
            schema_hint={"type": "array"},
            description="test data",
        ))
        # Name/format/size match the publish arguments / payload.
        assert ref.name == "results.json"
        assert ref.format == "json"
        assert ref.size_bytes == len(data)
        # Producer identity comes from the workspace constructor.
        assert ref.producer_task_id == "task_5"
        assert ref.producer_agent_id == "db_analyst"
        # URI nests plan/task/name.
        assert "workspace://10/task_5/results.json" == ref.uri

    def test_publish_then_load(self, workspace, tmp_path):
        """A second PlanWorkspace with the same backend root can load a published ref."""
        original = b'{"key": "value"}'
        ref = asyncio.run(workspace.publish("out.json", original, format="json"))

        # Consumer uses a different task_id/agent_id but same plan + root.
        consumer_ws = PlanWorkspace(
            plan_id=10,
            task_id="task_6",
            agent_id="video_parser",
            backend=LocalWorkspaceBackend(root=str(tmp_path)),
        )
        loaded = asyncio.run(consumer_ws.load(ref))
        # Bytes identical to what the producer published.
        assert loaded == original

    def test_load_json(self, workspace, tmp_path):
        """load_json decodes a published JSON artifact into a Python object."""
        obj = {"users": [{"id": 1}, {"id": 2}]}
        asyncio.run(workspace.publish("data.json", json.dumps(obj).encode(), format="json"))

        # published_refs accumulates refs from publish calls.
        ref = workspace.published_refs[0]
        consumer = PlanWorkspace(
            plan_id=10, task_id="task_7", agent_id="other",
            backend=LocalWorkspaceBackend(root=str(tmp_path)),
        )
        result = asyncio.run(consumer.load_json(ref))
        # Object equality after JSON round trip.
        assert result == obj

    def test_published_refs_accumulate(self, workspace):
        """Multiple publish calls append to published_refs in order."""
        asyncio.run(workspace.publish("a.json", b"[]", format="json"))
        asyncio.run(workspace.publish("b.csv", b"x,y", format="csv"))
        assert len(workspace.published_refs) == 2
        assert workspace.published_refs[0].name == "a.json"
        assert workspace.published_refs[1].name == "b.csv"

    def test_from_request(self, tmp_path):
        """from_request builds a PlanWorkspace from AgentTaskRequest workspace_uri."""
        uri = f"workspace://15?root={tmp_path}"
        request = AgentTaskRequest(
            task_id="t1",
            description="test",
            plan_id=15,
            workspace_uri=uri,
        )
        ws = PlanWorkspace.from_request(request)
        # plan_id/task_id taken from the request.
        assert ws.plan_id == 15
        assert ws.task_id == "t1"
        ref = asyncio.run(ws.publish("x.json", b'{"a":1}', format="json"))
        assert ref.uri == "workspace://15/t1/x.json"


# ---------------------------------------------------------------------------
# URI parsing
# ---------------------------------------------------------------------------

class TestURIParsing:
    """Contracts for _create_backend_from_uri."""

    def test_local_workspace_uri(self, tmp_path):
        """workspace://plan?root=… yields LocalWorkspaceBackend and plan_id."""
        backend, plan_id = _create_backend_from_uri(f"workspace://42?root={tmp_path}")
        assert isinstance(backend, LocalWorkspaceBackend)
        assert plan_id == 42

    def test_s3_workspace_uri(self):
        """s3://bucket/workspaces/plan yields S3WorkspaceBackend and plan_id."""
        from packages.agent_sdk.src.workspace.backend import S3WorkspaceBackend
        backend, plan_id = _create_backend_from_uri("s3://my-bucket/workspaces/99")
        assert isinstance(backend, S3WorkspaceBackend)
        assert plan_id == 99


# ---------------------------------------------------------------------------
# Integration: artifact_refs on AgentTaskResult
# ---------------------------------------------------------------------------

class TestResultWithArtifactRefs:
    """Contracts for artifact refs on result/context/request models."""

    def test_result_carries_refs(self):
        """AgentTaskResult serializes artifact_refs through model_dump."""
        ref = ArtifactRef(
            uri="workspace://1/2/data.json",
            name="data.json",
            format="json",
            size_bytes=100,
            producer_task_id="2",
        )
        result = AgentTaskResult(
            success=True,
            message="done",
            artifact_refs=[ref],
        )
        assert len(result.artifact_refs) == 1
        dumped = result.model_dump(mode="json")
        assert dumped["artifact_refs"][0]["name"] == "data.json"

    def test_context_carries_available_artifacts(self):
        """ExecutionContextSnapshot retains available_artifacts for downstream tasks."""
        ref = ArtifactRef(
            uri="workspace://5/3/output.parquet",
            name="output.parquet",
            format="parquet",
            size_bytes=50000,
            schema_hint={"columns": ["a", "b"]},
            description="Processed data",
            producer_task_id="3",
            producer_agent_id="db_analyst",
        )
        ctx = ExecutionContextSnapshot(
            plan_summary="Plan 5",
            available_artifacts=[ref],
        )
        assert len(ctx.available_artifacts) == 1
        assert ctx.available_artifacts[0].name == "output.parquet"

    def test_request_has_workspace_uri(self):
        """AgentTaskRequest stores workspace_uri for PlanWorkspace.from_request."""
        req = AgentTaskRequest(
            task_id="1",
            description="do something",
            plan_id=5,
            workspace_uri="workspace://5?root=/tmp/ws",
        )
        assert req.workspace_uri == "workspace://5?root=/tmp/ws"
