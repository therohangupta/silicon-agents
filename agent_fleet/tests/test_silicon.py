"""Silicon/EDA domain unit tests for catalog, memory, context, and agents.

Locks in: 70-agent catalog file completeness, WritePolicy placements,
lookup copies, journal idempotency, promotion races, FileStore reload,
ContextService conflict handling, lead/worker/validator handle outcomes,
and AgentService delegation to the agent object. Runs offline with
InMemoryStore / FileStore (no MEMORY_PLANE_TEST required).
"""

from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.agent_sdk.src.models import AgentTaskRequest
from packages.agent_sdk.src.schema.validator import AgentConfigValidator
from domains.eda.agent import workflow_from_result
from domains.eda.context import ContextService
from domains.eda.memory import EngineeringMemory, InMemoryStore, StoreCopy, WritePolicy
from domains.eda.memory.file_store import FileStore
from domains.eda.memory.service import MemoryPolicyError
from domains.eda.registry import all_specs, get_spec, validate_catalog
from domains.eda.server import AgentService
from domains.eda.schemas import (
    AuthorKind,
    ExperimentRecord,
    MemoryScope,
    RecordType,
    TaskOutcome,
    TaskSpec,
    ValidationState,
)

AGENTS = ROOT / "agents"


def _agent_dir(agent_id: str) -> Path:
    spec = get_spec(agent_id)
    return AGENTS / spec.path


def test_catalog_is_complete_and_files_match():
    """Catalog has 70 agents; each package has agent/server/Dockerfile/config/tools matching the spec."""
    # Locks in: not (ROOT / "packages" / "silicon").exists()
    assert not (ROOT / "packages" / "silicon").exists()
    validate_catalog()
    specs = all_specs()
    # Locks in: len(specs) == 70
    assert len(specs) == 70
    # Locks in: get_spec("chip_flow_lead").role.value == "lead"
    assert get_spec("chip_flow_lead").role.value == "lead"
    # Locks in: get_spec("signoff_validator").role.value == "validator"
    assert get_spec("signoff_validator").role.value == "validator"
    for spec in specs:
        directory = AGENTS / spec.path
        # Locks in: (directory / "agent.py").exists()
        assert (directory / "agent.py").exists()
        # Locks in: (directory / "server.py").exists()
        assert (directory / "server.py").exists()
        # Locks in: (directory / "Dockerfile").exists()
        assert (directory / "Dockerfile").exists()
        config = AgentConfigValidator().validate_file(directory / "config.yaml")
        # Locks in: config.connection.port == spec.port
        assert config.connection.port == spec.port
        # Locks in: config.metadata.name == spec.agent_id
        assert config.metadata.name == spec.agent_id
        tool_names = {item.name for item in spec.tools}
        # Locks in: {skill.callable for skill in config.skills} == tool_names
        assert {skill.callable for skill in config.skills} == tool_names
        tree = ast.parse((directory / "tools.py").read_text())
        defined = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        # Locks in: tool_names <= defined
        assert tool_names <= defined
        # Locks in: f"class {spec.class_name}" in (directory / "agent.py").read_text()
        assert f"class {spec.class_name}" in (directory / "agent.py").read_text()


def test_write_policy_places_different_payloads_on_chosen_stores():
    """WritePolicy copies land on named stores; vault secrets never leak into postgres payloads."""
    # Drive the async test body from sync pytest.
    asyncio.run(_write_policy())


async def _write_policy():
    memory = EngineeringMemory(InMemoryStore())
    scope = MemoryScope(project="chip-a", revision="r1", block="dma", stage="rtl")
    secret = "foundry-token-value"
    record = await memory.write(
        scope=scope,
        record_type=RecordType.INTERFACE_CONTRACT,
        summary="dma timing slices",
        payload={"unused": True},
        idempotency_key="policy-slices",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
        policy=WritePolicy(copies=[
            StoreCopy(store="postgres", payload={"spec": "ready-valid"}),
            StoreCopy(store="cassandra_kv", key="chip-a/dma/period", payload={"period_ns": 2.5}),
            StoreCopy(store="cassandra_kv", key="chip-a/dma/ready", payload={"ready": "level"}),
            StoreCopy(store="clickhouse", key="exp-dma", payload={"metric": "wns", "value": -0.042, "corner": "ss"}),
            StoreCopy(store="object", key="reports/dma.txt", payload={"text": "wns -0.042"}),
            StoreCopy(store="vault", key="foundry-token", payload={"value": secret}),
        ]),
    )
    # Locks in: record.payload == {"spec": "ready-valid"}
    assert record.payload == {"spec": "ready-valid"}
    # Locks in: secret not in record.model_dump_json()
    assert secret not in record.model_dump_json()
    # Locks in: "postgres" in record.placements
    assert "postgres" in record.placements
    # Locks in: "cassandra_kv" in record.placements
    assert "cassandra_kv" in record.placements
    # Locks in: "clickhouse" in record.placements
    assert "clickhouse" in record.placements
    # Locks in: "opensearch" not in record.placements
    assert "opensearch" not in record.placements

    period = await memory.get_lookup(project_id="chip-a", key="chip-a/dma/period")
    ready = await memory.get_lookup(project_id="chip-a", key="chip-a/dma/ready")
    # Locks in: period is not None and period.payload == {"period_ns": 2.5}
    assert period is not None and period.payload == {"period_ns": 2.5}
    # Locks in: ready is not None and ready.payload == {"ready": "level"}
    assert ready is not None and ready.payload == {"ready": "level"}
    # Locks in: await memory.read_copy(store="clickhouse", project_id="chip-a", key="exp-dma") == {
    assert await memory.read_copy(store="clickhouse", project_id="chip-a", key="exp-dma") == {
        "metric": "wns",
        "value": -0.042,
        "corner": "ss",
    }
    # Locks in: await memory.read_copy(store="object", project_id="chip-a", key="reports/dma.txt") == {"text": "wns 
    assert await memory.read_copy(store="object", project_id="chip-a", key="reports/dma.txt") == {"text": "wns -0.042"}
    # Locks in: await memory.read_copy(store="vault", project_id="chip-a", key="foundry-token") == {"value": secret}
    assert await memory.read_copy(store="vault", project_id="chip-a", key="foundry-token") == {"value": secret}
    # Locks in: await memory.read_copy(store="postgres", project_id="chip-a", key="") == {"spec": "ready-valid"}
    assert await memory.read_copy(store="postgres", project_id="chip-a", key="") == {"spec": "ready-valid"}

    omitted = await memory.write(
        scope=scope,
        record_type=RecordType.EXPERIMENT_RESULT,
        summary="numbers only",
        payload={"not_stored": True},
        idempotency_key="policy-no-postgres",
        policy=WritePolicy(copies=[
            StoreCopy(store="clickhouse", key="exp-only", payload={"metric": "tns", "value": 0.1}),
        ]),
    )
    # Locks in: omitted.payload == {}
    assert omitted.payload == {}
    # Locks in: "postgres" not in omitted.placements
    assert "postgres" not in omitted.placements
    # Locks in: "not_stored" not in omitted.model_dump_json()
    assert "not_stored" not in omitted.model_dump_json()

    # Expect the following block to raise (policy / validation guard).
    try:
        await memory.write(
            scope=scope,
            record_type=RecordType.INTERFACE_CONTRACT,
            summary="leaked secret",
            payload={"value": secret},
            idempotency_key="policy-leak",
            author_kind=AuthorKind.HUMAN,
            validation_state=ValidationState.HUMAN_AUTHORED,
            policy=WritePolicy(copies=[
                StoreCopy(store="postgres"),
                StoreCopy(store="vault", key="foundry-token-2", payload={"value": secret}),
            ]),
        )
        # Expected failure path did not trigger — fail the test.
        raise AssertionError("vault payload must not be copied to postgres")
    # Policy correctly rejected the write.
    except MemoryPolicyError:
        pass


def test_lookup_copy_is_optional_and_not_applied_to_every_record():
    """Journal skips KV/search; lookup_keys opt into cassandra_kv; unknown also_stores fail."""
    # Drive the async test body from sync pytest.
    asyncio.run(_lookup_copy())


async def _lookup_copy():
    memory = EngineeringMemory(InMemoryStore())
    scope = MemoryScope(project="chip-a", revision="r1", block="dma", stage="rtl")
    journal = await memory.append(
        task_id="rtl-1",
        idempotency_key="rtl-1:start",
        payload={"note": "checkpoint"},
        project_id="chip-a",
        scope=scope,
        summary="started",
    )
    # Locks in: "postgres" in journal.placements
    assert "postgres" in journal.placements
    # Locks in: "cassandra_journal" in journal.placements
    assert "cassandra_journal" in journal.placements
    # Locks in: "cassandra_kv" not in journal.placements
    assert "cassandra_kv" not in journal.placements
    # Locks in: "opensearch" not in journal.placements
    assert "opensearch" not in journal.placements

    copied = await memory.publish(
        scope=scope,
        record_type=RecordType.INTERFACE_CONTRACT,
        summary="dma ready protocol",
        payload={"ready": "level"},
        idempotency_key="iface-kv",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
        lookup_keys=["chip-a/dma/ready-protocol"],
    )
    # Locks in: "postgres" in copied.placements
    assert "postgres" in copied.placements
    # Locks in: "cassandra_kv" in copied.placements
    assert "cassandra_kv" in copied.placements
    # Locks in: "opensearch" in copied.placements
    assert "opensearch" in copied.placements
    found = await memory.get_lookup(project_id="chip-a", key="chip-a/dma/ready-protocol")
    # Locks in: found is not None
    assert found is not None
    # Locks in: found.memory_id == copied.memory_id
    assert found.memory_id == copied.memory_id
    # Locks in: found.payload["ready"] == "level"
    assert found.payload["ready"] == "level"
    # Locks in: await memory.get_lookup(project_id="chip-a", key="chip-a/dma/missing") is None
    assert await memory.get_lookup(project_id="chip-a", key="chip-a/dma/missing") is None

    # Expect the following block to raise (policy / validation guard).
    try:
        await memory.append(
            task_id="rtl-1",
            idempotency_key="rtl-1:bad",
            payload={},
            project_id="chip-a",
            scope=scope,
            also_stores=["tape"],
        )
        # Expected failure path did not trigger — fail the test.
        raise AssertionError("unknown placement should fail")
    # Policy correctly rejected the write.
    except MemoryPolicyError:
        pass


def test_journal_publish_and_promotion():
    """Idempotent append, evidence/author guards, stale/race promotion, search, experiments."""
    # Drive the async test body from sync pytest.
    asyncio.run(_journal_publish_and_promotion())


async def _journal_publish_and_promotion():
    memory = EngineeringMemory(InMemoryStore())
    scope = MemoryScope(project="chip-a", revision="r1", block="dma", stage="verification")
    first = await memory.append(
        task_id="verify-1",
        idempotency_key="verify-1:obs:1",
        payload={"failure_cluster": {"seeds": [17]}},
        project_id="chip-a",
        scope=scope,
        agent_id="verification_lead",
        summary="cluster",
    )
    again = await memory.append(
        task_id="verify-1",
        idempotency_key="verify-1:obs:1",
        payload={"failure_cluster": {"seeds": [99]}},
        project_id="chip-a",
        scope=scope,
        agent_id="verification_lead",
        summary="cluster",
    )
    # Locks in: again.memory_id == first.memory_id
    assert again.memory_id == first.memory_id
    # Locks in: again.payload["failure_cluster"]["seeds"] == [17]
    assert again.payload["failure_cluster"]["seeds"] == [17]

    # Expect the following block to raise (policy / validation guard).
    try:
        await memory.publish(
            scope=scope,
            record_type=RecordType.AGENT_FINDING,
            summary="no evidence",
            payload={},
            idempotency_key="finding-empty",
        )
        # Expected failure path did not trigger — fail the test.
        raise AssertionError("finding without evidence should fail")
    # Policy correctly rejected the write.
    except MemoryPolicyError:
        pass

    # Expect the following block to raise (policy / validation guard).
    try:
        await memory.publish(
            scope=scope,
            record_type=RecordType.HUMAN_INTENT,
            summary="agent wrote intent",
            payload={},
            idempotency_key="intent-agent",
            author_kind=AuthorKind.AGENT,
        )
        # Expected failure path did not trigger — fail the test.
        raise AssertionError("agent human-intent write should fail")
    # Policy correctly rejected the write.
    except MemoryPolicyError:
        pass

    await memory.publish(
        scope=scope,
        record_type=RecordType.HUMAN_INTENT,
        summary="Burst termination is defined",
        payload={"subject": "burst", "claim": "ends on last beat"},
        idempotency_key="intent-human",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
    )
    finding = await memory.publish(
        scope=scope,
        record_type=RecordType.AGENT_FINDING,
        summary="RTL ends one cycle early",
        payload={"subject": "burst", "claim": "ends one cycle early"},
        evidence=["artifact://waves/1"],
        idempotency_key="finding-1",
        validation_state=ValidationState.PROVISIONAL,
    )
    # Locks in: finding.record_type == RecordType.AGENT_FINDING
    assert finding.record_type == RecordType.AGENT_FINDING
    gate = await memory.publish(
        scope=scope,
        record_type=RecordType.GATE_DECISION,
        summary="verification passed",
        payload={"passed": True, "candidate": "candidate://dma/v2"},
        idempotency_key="gate-1",
        validation_state=ValidationState.VALIDATED,
    )
    stale = await memory.promote_candidate(
        candidate="candidate://dma/v2",
        expected_current_baseline="candidate://dma/v1",
        required_gate_ids=[gate.memory_id],
        scope=scope,
    )
    # Locks in: stale.promoted is False
    assert stale.promoted is False
    # Locks in: stale.reason == "stale_baseline"
    assert stale.reason == "stale_baseline"

    promoted = await memory.promote_candidate(
        candidate="candidate://dma/v2",
        expected_current_baseline=None,
        required_gate_ids=[gate.memory_id],
        scope=scope,
    )
    # Locks in: promoted.promoted is True
    assert promoted.promoted is True
    raced = await memory.promote_candidate(
        candidate="candidate://dma/v3",
        expected_current_baseline=None,
        required_gate_ids=[gate.memory_id],
        scope=scope,
    )
    # Locks in: raced.promoted is False
    assert raced.promoted is False
    # Locks in: raced.current_baseline == "candidate://dma/v2"
    assert raced.current_baseline == "candidate://dma/v2"

    hits = await memory.search(project="chip-a", query="ends on last beat")
    # Locks in: any(record.payload.get("claim") == "ends on last beat" for record in hits)
    assert any(record.payload.get("claim") == "ends on last beat" for record in hits)
    experiment = await memory.record_experiment(
        ExperimentRecord(
            experiment_id="exp-1",
            hypothesis="retiming the adder improves WNS",
            baseline="candidate://dma/v2",
            variables_changed=["adder_pipeline"],
        ),
        scope=scope,
        agent_id="synthesis_experiment",
        task_id="synth-1",
        idempotency_key="exp-1",
    )
    # Locks in: experiment.record_type == RecordType.EXPERIMENT_RESULT
    assert experiment.record_type == RecordType.EXPERIMENT_RESULT


def test_file_store_reloads(tmp_path: Path):
    """FileStore persists journal rows across EngineeringMemory re-instantiation."""
    # Drive the async test body from sync pytest.
    asyncio.run(_file_store_reloads(tmp_path))


async def _file_store_reloads(tmp_path: Path):
    scope = MemoryScope(project="chip-a", revision="r1", stage="rtl")
    memory = EngineeringMemory(FileStore(tmp_path))
    await memory.append(
        task_id="t1",
        idempotency_key="t1:1",
        payload={"note": "kept"},
        project_id="chip-a",
        scope=scope,
        summary="kept",
    )
    reloaded = EngineeringMemory(FileStore(tmp_path))
    records = await reloaded.query(project="chip-a", task_id="t1")
    # Locks in: len(records) == 1
    assert len(records) == 1
    # Locks in: records[0].payload["note"] == "kept"
    assert records[0].payload["note"] == "kept"


def test_context_surfaces_conflicts_and_prefers_human_intent():
    """ContextService keeps human intent, drops stale findings, surfaces claim conflicts."""
    # Drive the async test body from sync pytest.
    asyncio.run(_context())


async def _context():
    memory = EngineeringMemory(InMemoryStore())
    scope = MemoryScope(project="chip-a", revision="r1", block="dma", stage="verification")
    await memory.publish(
        scope=scope,
        record_type=RecordType.HUMAN_INTENT,
        summary="spec",
        payload={"subject": "burst", "claim": "ends on last beat"},
        idempotency_key="human",
        author_kind=AuthorKind.HUMAN,
        validation_state=ValidationState.HUMAN_AUTHORED,
    )
    await memory.publish(
        scope=scope,
        record_type=RecordType.AGENT_FINDING,
        summary="rtl",
        payload={"subject": "burst", "claim": "ends early", "stale": True},
        evidence=["artifact://waves/stale"],
        idempotency_key="stale",
        validation_state=ValidationState.PROVISIONAL,
    )
    await memory.publish(
        scope=scope,
        record_type=RecordType.AGENT_FINDING,
        summary="rtl current",
        payload={"subject": "burst", "claim": "ends early"},
        evidence=["artifact://waves/current"],
        idempotency_key="current",
        validation_state=ValidationState.VALIDATED,
    )
    from domains.eda.spec import AgentContext

    service = ContextService(memory)
    package = await service.assemble(
        TaskSpec(task_id="verify-1", objective="check burst", project_id="chip-a", design_revision="r1", block="dma"),
        AgentContext(
            include=["human_intent", "open_findings"],
            exclude=["stale_candidates"],
            drop=["rejected"],
            precedence=["human-authored", "validated", "provisional"],
            protect=["human-authored"],
        ),
    )
    # Locks in: any(record.summary == "spec" for record in package.records)
    assert any(record.summary == "spec" for record in package.records)
    # Locks in: all(record.payload.get("stale") is not True for record in package.records)
    assert all(record.payload.get("stale") is not True for record in package.records)
    # Locks in: package.conflicts
    assert package.conflicts
    # Locks in: package.conflicts[0].subject == "burst"
    assert package.conflicts[0].subject == "burst"


def test_lead_plans_and_worker_does_not_grade_itself():
    """Lead emits workflow; worker is framework-unbound; forbidden actions denied; validator gates."""
    # Drive the async test body from sync pytest.
    asyncio.run(_agents())


async def _agents():
    memory = EngineeringMemory(InMemoryStore())
    lead = _load("chip_flow_lead", "ChipFlowLeadAgent", memory)
    worker = _load("rtl_implementation", "RtlImplementationAgent", memory)
    validator = _load("verification_validator", "VerificationValidatorAgent", memory)

    planned = await lead.handle(AgentTaskRequest(
        task_id="program-1",
        description="Close a block through signoff",
        inputs={"task": {"project_id": "chip-a", "design_revision": "r1", "objective": "Close a block through signoff"}},
    ))
    # Locks in: planned.success is True
    assert planned.success is True
    # Locks in: planned.outcome == TaskOutcome.COMPLETED.value
    assert planned.outcome == TaskOutcome.COMPLETED.value
    workflow = workflow_from_result(planned)
    # Locks in: workflow is not None
    assert workflow is not None
    # Locks in: workflow.tasks[0].agent_type == "requirements"
    assert workflow.tasks[0].agent_type == "requirements"
    # Locks in: "signoff_validator" in {task.agent_type for task in workflow.tasks}
    assert "signoff_validator" in {task.agent_type for task in workflow.tasks}
    # Locks in: any(task.depends_on for task in workflow.tasks)
    assert any(task.depends_on for task in workflow.tasks)

    edited = await worker.handle(AgentTaskRequest(task_id="rtl-1", description="Pipeline the adder"))
    # Locks in: edited.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    assert edited.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    # Locks in: edited.reason_code == "FRAMEWORK_UNBOUND"
    assert edited.reason_code == "FRAMEWORK_UNBOUND"
    # Locks in: edited.success is True
    assert edited.success is True
    # Locks in: all(item["status"] == "not_run" for item in edited.artifacts["observations"])
    assert all(item["status"] == "not_run" for item in edited.artifacts["observations"])

    blocked = await worker.handle(AgentTaskRequest(
        task_id="rtl-2",
        description="Do not edit",
        inputs={"task": {
            "objective": "Do not edit",
            "forbidden_actions": ["write_candidate", "read_reports", "submit_tool_job", "publish_finding"],
        }},
    ))
    # Locks in: blocked.success is False
    assert blocked.success is False
    # Locks in: blocked.outcome == TaskOutcome.NONRETRYABLE_FAILURE.value
    assert blocked.outcome == TaskOutcome.NONRETRYABLE_FAILURE.value
    # Locks in: blocked.reason_code == "PERMISSION_DENIED"
    assert blocked.reason_code == "PERMISSION_DENIED"
    checkpoints = await memory.query(project="sandbox", record_types=[RecordType.TASK_CHECKPOINT])
    assert any(record.idempotency_key.endswith(":failed") for record in checkpoints)

    graded = await validator.handle(AgentTaskRequest(
        task_id="gate-1",
        description="Grade the candidate",
        inputs={"task": {"objective": "Grade", "inputs": {"candidate": "candidate://dma/v2"}}},
    ))
    # Locks in: graded.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    assert graded.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    gates = await memory.query(project="sandbox", record_types=[RecordType.GATE_DECISION])
    # Locks in: gates
    assert gates
    # Locks in: gates[-1].payload["passed"] is False
    assert gates[-1].payload["passed"] is False


def test_server_delegates_to_the_agent_object():
    """AgentService.from_agent executes RequirementsAgent and returns tool observation stubs."""
    # Drive the async test body from sync pytest.
    asyncio.run(_server())


async def _server():
    import importlib.util

    from domains.eda.server import AgentService

    path = _agent_dir("requirements") / "agent.py"
    spec = importlib.util.spec_from_file_location("_requirements_agent_mod", path)
    module = importlib.util.module_from_spec(spec)
    # Locks in: spec and spec.loader
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    memory = EngineeringMemory(InMemoryStore())
    server = AgentService.from_agent(
        _agent_dir("requirements") / "config.yaml",
        module.RequirementsAgent,
        engineering_memory=memory,
    )
    result = await server._runtime.execute(AgentTaskRequest(
        task_id="req-1",
        description="Extract requirements for a block",
        inputs={"candidate_ref": "artifact://candidate/req-1"},
    ))
    # Locks in: result.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    assert result.outcome == TaskOutcome.PARTIALLY_COMPLETED.value
    # Locks in: result.artifacts["observations"][0]["operation"] == "extract_requirements"
    assert result.artifacts["observations"][0]["operation"] == "extract_requirements"
    # Locks in: result.artifacts["observations"][0]["status"] == "not_run"
    assert result.artifacts["observations"][0]["status"] == "not_run"
    # The EDA lifecycle binds task inputs and assembled context through the SDK skill registry.
    invocation = result.artifacts["observations"][0]["input"]
    assert invocation["candidate_ref"] == "artifact://candidate/req-1"
    assert invocation["params"]["context"]["records"] == []


def _load(agent_id: str, class_name: str, memory: EngineeringMemory):
    """Build an agent through AgentService so it shares the SDK skill registry."""
    import importlib.util

    path = _agent_dir(agent_id) / "agent.py"
    module_name = f"_agent_mod_{agent_id}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    # Locks in: spec and spec.loader
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    cls = getattr(module, class_name)
    service = AgentService.from_agent(
        _agent_dir(agent_id) / "config.yaml",
        cls,
        engineering_memory=memory,
    )
    return service.bound_agent
