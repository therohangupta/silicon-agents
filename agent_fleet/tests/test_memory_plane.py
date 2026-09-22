"""Exercise every physical store behind EngineeringMemory.

Skipped unless MEMORY_PLANE_TEST=1. Start the compose stack first; this
process talks to the published ports.

Locks in round-trips for journal/KV/search/vector/decisions/gates/promotion,
S3 artifacts, git source, ClickHouse QoR, Vault secrets (never in postgres
payloads), leases, approvals, and WritePolicy multi-store fan-out.
"""

from __future__ import annotations

# Drive async memory APIs from sync pytest tests.
import asyncio
# Gate the module on MEMORY_PLANE_TEST.
import os
# git ls-remote check for put_source.
import subprocess
# sys.path for domains imports.
import sys
from pathlib import Path

import pytest

# agent_fleet root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Skip unless the live memory plane containers are up.
pytestmark = pytest.mark.skipif(
    os.environ.get("MEMORY_PLANE_TEST") != "1",
    reason="Set MEMORY_PLANE_TEST=1 when the memory containers are running",
)


def _prepare_env() -> None:
    """Point MEMORY_* env vars at the host view of config/platform.yaml."""
    from packages.platform_config import host_settings

    for key, value in host_settings().items():
        if key.startswith("MEMORY_"):
            os.environ[key] = value


def test_every_store_round_trips():
    """Sync wrapper: configure env then run the async multi-store round trip."""
    _prepare_env()
    asyncio.run(_every_store())


async def _every_store():
    """Async body: journal, publish, search, promote, artifact, source, QoR, secret, lease, approval."""
    from uuid import uuid4

    from domains.eda.memory import open_memory
    from domains.eda.schemas import (
        AuthorKind,
        MemoryScope,
        RecordType,
        ValidationState,
    )

    # Unique suffix so parallel/repeated runs do not collide on keys.
    suffix = uuid4().hex[:8]
    project = f"chip-{suffix}"
    # Open the multi-backend plane memory implementation.
    memory = open_memory("plane")
    scope = MemoryScope(project=project, revision="r1", block="dma", stage="verification")
    secret = f"plane-secret-{suffix}"

    # Append-only journal row (Cassandra journal placement, not KV/search).
    journal = await memory.append(
        task_id=f"plane-task-{suffix}",
        idempotency_key=f"plane-task-{suffix}:journal",
        payload={"note": "append-only journal row"},
        project_id=project,
        scope=scope,
        agent_id="requirements",
        summary="journal row for the plane test",
    )
    # get by memory_id returns the same summary.
    loaded = await memory.get(journal.memory_id)
    assert loaded is not None
    assert loaded.summary == journal.summary
    # Journal hits cassandra_journal only (not KV / opensearch).
    assert "cassandra_journal" in journal.placements
    assert "cassandra_kv" not in journal.placements
    assert "opensearch" not in journal.placements
    # Journal read by task includes this row from cassandra.
    rows = await memory.read_journal(project_id=project, task_id=f"plane-task-{suffix}")
    assert any(row["memory_id"] == journal.memory_id and row["source"] == "cassandra" for row in rows)
    # Scope projection includes the journal row for stage/block filters.
    scoped = await memory.read_scope_projection(project_id=project, stage="verification", block="dma")
    assert any(row["memory_id"] == journal.memory_id for row in scoped)

    # Agent finding publishes to search + vector, not cassandra_kv.
    finding = await memory.publish(
        scope=scope,
        record_type=RecordType.AGENT_FINDING,
        summary="clock skew exceeds the limit on the dma block",
        payload={"subject": "clock", "claim": "skew exceeds the limit"},
        evidence=["artifact://reports/skew"],
        idempotency_key=f"plane-finding-{suffix}",
        validation_state=ValidationState.PROVISIONAL,
    )
    assert "opensearch" in finding.placements
    assert "vector" in finding.placements
    assert "cassandra_kv" not in finding.placements
    # Interface contract with lookup_keys lands in KV for point reads.
    looked_up = await memory.publish(
        scope=scope,
        record_type=RecordType.INTERFACE_CONTRACT,
        summary="dma ready protocol for a point read",
        payload={"ready": "level"},
        idempotency_key=f"plane-kv-{suffix}",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
        lookup_keys=[f"{project}/dma/ready-protocol"],
    )
    by_key = await memory.get_lookup(project_id=project, key=f"{project}/dma/ready-protocol")
    assert by_key is not None
    assert by_key.memory_id == looked_up.memory_id
    assert by_key.payload["ready"] == "level"
    # Text search finds the finding by summary terms.
    text_hits = await memory.search(project=project, query="clock skew")
    assert any(hit.memory_id == finding.memory_id for hit in text_hits)
    # Semantic search also finds the finding.
    vector_hits = await memory.search_semantic(project=project, query="clock skew limit")
    assert any(hit.memory_id == finding.memory_id for hit in vector_hits)

    # Human decision listable by scope path.
    decision = await memory.publish(
        scope=scope,
        record_type=RecordType.DECISION,
        summary="Keep the current dma floorplan",
        payload={"choice": "candidate-3"},
        idempotency_key=f"plane-decision-{suffix}",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
    )
    decisions = await memory.list_decisions(scope.path)
    assert any(item["decision_id"] == decision.memory_id for item in decisions)

    # Gate + promote sets baseline when expected_current_baseline is None.
    gate = await memory.publish(
        scope=scope,
        record_type=RecordType.GATE_DECISION,
        summary="verification passed for the plane candidate",
        payload={"passed": True, "candidate": f"candidate://dma/{suffix}"},
        idempotency_key=f"plane-gate-{suffix}",
        validation_state=ValidationState.VALIDATED,
    )
    promoted = await memory.promote_candidate(
        candidate=f"candidate://dma/{suffix}",
        expected_current_baseline=None,
        required_gate_ids=[gate.memory_id],
        scope=scope,
    )
    assert promoted.promoted is True
    assert await memory.store.get_baseline(scope.path) == f"candidate://dma/{suffix}"

    # Object store put/get for SPEF-like bytes.
    uri = await memory.put_artifact(key=f"{project}/dma.spef", data=b"SPEF-PLACEHOLDER")
    from packages.platform_config import host_settings

    assert uri == f"s3://{host_settings()['MEMORY_S3_BUCKET']}/{project}/dma.spef"
    assert await memory.get_artifact(f"{project}/dma.spef") == b"SPEF-PLACEHOLDER"

    # Source store commits and is visible via git daemon ls-remote.
    sha = await memory.put_source(path=f"rtl/dma-{suffix}.v", data=b"module dma; endmodule\n", message="Add dma")
    assert len(sha) >= 7
    assert await memory.get_source(f"rtl/dma-{suffix}.v") == b"module dma; endmodule\n"
    remote = subprocess.run(
        ["git", "ls-remote", "git://127.0.0.1:9418/memory.git"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert sha in remote.stdout

    # ClickHouse QoR metric round trip.
    await memory.record_qor(
        project_id=project,
        experiment_id=f"exp-{suffix}",
        metric="wns",
        value=-0.042,
        corner="ss_0p72v_125c",
    )
    metrics = await memory.query_qor(project_id=project, experiment_id=f"exp-{suffix}")
    assert any(item["metric"] == "wns" and abs(float(item["value"]) - -0.042) < 1e-9 for item in metrics)

    # Vault secret round trip; secret must not appear in scanned postgres JSON.
    await memory.put_secret(name=f"lab-token-{suffix}", value=secret)
    assert await memory.get_secret(f"lab-token-{suffix}") == secret
    stored = " ".join(record.model_dump_json() for record in await memory.store.scan())
    assert secret not in stored

    # Lease: first holder wins; second denied until release.
    assert await memory.acquire_lease(
        lease_id=f"lease-{suffix}-1", task_id=f"plane-lease-{suffix}", holder="requirements", scope_path=scope.path
    )
    assert await memory.acquire_lease(
        lease_id=f"lease-{suffix}-2", task_id=f"plane-lease-{suffix}", holder="rtl_implementation", scope_path=scope.path
    ) is False
    assert await memory.release_lease(task_id=f"plane-lease-{suffix}", holder="requirements")
    assert await memory.acquire_lease(
        lease_id=f"lease-{suffix}-3", task_id=f"plane-lease-{suffix}", holder="rtl_implementation", scope_path=scope.path
    )

    # Approval record round trip.
    await memory.record_approval(
        approval_id=f"approval-{suffix}",
        subject_ref=f"candidate://dma/{suffix}",
        approver="human-owner",
        decision="approved",
        evidence_ref=gate.memory_id,
    )
    approval = await memory.get_approval(f"approval-{suffix}")
    assert approval is not None
    assert approval["decision"] == "approved"

    # At least one memory event was emitted during the test.
    assert await memory.event_count() >= 1


def test_policy_writes_each_payload_to_the_store_it_names():
    """Sync wrapper for WritePolicy multi-copy fan-out against the live plane."""
    _prepare_env()
    asyncio.run(_policy_fanout())


async def _policy_fanout():
    """WritePolicy copies land on postgres/cassandra_kv/clickhouse/object/vault as named."""
    from uuid import uuid4

    from domains.eda.memory import StoreCopy, WritePolicy, open_memory
    from domains.eda.schemas import AuthorKind, MemoryScope, RecordType, ValidationState

    suffix = uuid4().hex[:8]
    secret = f"policy-secret-{suffix}"
    memory = open_memory("plane")
    scope = MemoryScope(project="chip-plane", revision="r1", block="dma", stage="rtl")
    # Explicit per-store payloads; postgres copy becomes the record.payload.
    record = await memory.write(
        scope=scope,
        record_type=RecordType.INTERFACE_CONTRACT,
        summary="dma slices for a point read and a measurement",
        payload={"unused": True},
        idempotency_key=f"plane-policy-{suffix}",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
        policy=WritePolicy(copies=[
            StoreCopy(store="postgres", payload={"spec": "ready-valid"}),
            StoreCopy(store="cassandra_kv", key=f"chip-plane/dma/period-{suffix}", payload={"period_ns": 2.5}),
            StoreCopy(store="clickhouse", key=f"exp-policy-{suffix}", payload={"metric": "wns", "value": -0.011, "corner": "tt"}),
            StoreCopy(store="object", key=f"chip-plane/policy-{suffix}.txt", payload={"text": "wns -0.011"}),
            StoreCopy(store="vault", key=f"policy-token-{suffix}", payload={"value": secret}),
        ]),
    )
    # Canonical payload is the postgres copy, not the unused placeholder.
    assert record.payload == {"spec": "ready-valid"}
    # Secret never appears in the record JSON.
    assert secret not in record.model_dump_json()
    loaded = await memory.get(record.memory_id)
    assert loaded is not None
    assert loaded.payload == {"spec": "ready-valid"}
    assert secret not in loaded.model_dump_json()

    # KV point read for the cassandra_kv copy.
    by_key = await memory.get_lookup(project_id="chip-plane", key=f"chip-plane/dma/period-{suffix}")
    assert by_key is not None
    assert by_key.payload == {"period_ns": 2.5}
    # ClickHouse copy readable via read_copy.
    metrics = await memory.read_copy(store="clickhouse", project_id="chip-plane", key=f"exp-policy-{suffix}")
    assert any(item["metric"] == "wns" and abs(float(item["value"]) - -0.011) < 1e-9 for item in metrics)
    # Object store holds the text bytes from the copy payload.
    assert await memory.get_artifact(f"chip-plane/policy-{suffix}.txt") == b"wns -0.011"
    # Vault holds the secret value.
    assert await memory.get_secret(f"policy-token-{suffix}") == secret
    # Scanned store JSON must not contain the secret.
    stored = " ".join(item.model_dump_json() for item in await memory.store.scan())
    assert secret not in stored
