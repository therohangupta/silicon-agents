"""Engineering memory service: envelope rules over pluggable store backends.

``EngineeringMemory`` is the shared write/read facade every ``EDAAgent`` uses.
It owns the **envelope** (identity, scope, authorship, validation, evidence,
idempotency, placements). The writing agent owns the **payload** dict.

Write paths:

* ``append`` — task-local provisional journal (checkpoints). Does not run
  publish policy checks.
* ``publish`` / ``write`` — visible records; run ``_check_publish`` then commit.
* ``record_experiment`` — convenience publish for ``ExperimentRecord`` payloads.

Commit path (``_commit``):

1. Optional publish policy checks.
2. Idempotency short-circuit via ``store.find_idempotency``.
3. ``compile_policy`` merges placements with the primary payload.
4. Insert the envelope; optionally ``apply_copies`` for non-Postgres stores.
5. Special-case decision projection and supersede older records on publish.

Read paths include ``get``, ``query``, ``search``, ``get_lookup``, and
``read_copy``. Baseline movement is **only** through ``promote_candidate``
(compare-and-swap plus validated gate checks). Direct ``DESIGN_BASELINE``
publishes are rejected by policy.

``open_memory`` selects file, in-memory, Postgres, or plane backends from
environment variables so agent processes in compose share the plane while
local runs default to a shared file directory.
"""

from __future__ import annotations

# Flexible typing for payloads, optional sequences, and store duck-typing.
from typing import Any, Optional, Sequence

# Envelope enums for authorship, schema status, record kind, and trust.
from ..schemas.enums import AuthorKind, PayloadSchemaStatus, RecordType, ValidationState
# Envelope, scope, promotion result, and write-policy models.
from ..schemas.memory import MemoryRecord, MemoryScope, PromotionResult, WritePolicy
# Experiment payload helper used by record_experiment.
from ..schemas.messages import ExperimentRecord
# Default placements and policy compilation for EDA record types.
from .placements import PlacementError, compile_policy


class MemoryPolicyError(Exception):
    """Raised when a write violates envelope or placement rules.

    Examples: agents writing human intent, findings without evidence, direct
    baseline publishes, invalid lookup keys, or backends that cannot apply
    non-Postgres copies. Callers should treat this as a non-retryable
    configuration or policy fault unless the underlying cause is transient.
    """


class EngineeringMemory:
    """Shared engineering memory for chip-design agents.

    The envelope (identity, scope, authorship, validation, evidence) is owned
    by this service. The payload is owned by the writing agent.

    ``write`` accepts a policy that places one or more payloads onto any of
    the stores. A copy may reuse the primary payload or carry its own. Postgres
    is one of those stores, not a requirement that every payload land there.

    Journal appends are task-local and provisional. ``publish`` is the call that
    makes a record visible to other agents. Canonical baselines move only
    through compare-and-swap promotion.
    """

    def __init__(self, store: Any) -> None:
        """Bind this facade to a concrete store backend.

        Args:
            store: Object exposing at least ``get``, ``scan``, ``insert``,
                ``update``, and ``find_idempotency``. Plane backends also
                expose ``apply_copies``, journals, artifacts, leases, etc.

        Returns:
            None. Stores the backend on ``self.store``.

        Side effects:
            None beyond retaining the reference.

        Failures:
            None at construction; missing methods fail on first use.
        """
        # Duck-typed backend: file, memory, postgres, or plane.
        self.store = store

    async def append(
        self,
        *,
        task_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
        project_id: str,
        scope: MemoryScope,
        agent_id: str = "",
        run_id: str = "",
        summary: str = "",
        record_type: RecordType = RecordType.TASK_CHECKPOINT,
        design_revision: str = "",
        schema_record_name: str = "",
        artifact_refs: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        lookup_keys: Optional[Sequence[str]] = None,
        also_stores: Optional[Sequence[str]] = None,
        policy: Optional[WritePolicy] = None,
    ) -> MemoryRecord:
        """Append a provisional task-local journal record without publish checks.

        Used by ``EDAAgent.handle`` for started/finished checkpoints. Always
        writes ``ValidationState.PROVISIONAL`` and ``AuthorKind.AGENT``.

        Args:
            task_id: Task the checkpoint belongs to.
            idempotency_key: Dedup key (e.g. ``{key}:started``).
            payload: Agent-owned JSON body for the checkpoint.
            project_id: Memory project namespace.
            scope: Logical ``/programs`` scope for the write.
            agent_id: Writing agent id.
            run_id: Optional run identifier.
            summary: Short human summary.
            record_type: Defaults to ``TASK_CHECKPOINT``.
            design_revision: Revision denormalized onto the envelope.
            schema_record_name: Optional payload schema name.
            artifact_refs: Evidence URIs stored as envelope evidence.
            tags: Free-form tags.
            lookup_keys: KV keys for dictionary copies.
            also_stores: Extra store names beyond default placements.
            policy: Optional explicit write policy.

        Returns:
            The inserted or pre-existing ``MemoryRecord`` (idempotent).

        Side effects:
            Inserts into the store and may apply non-Postgres copies.

        Failures:
            Raises ``MemoryPolicyError`` on placement/lookup problems.
            Propagates store errors.
        """
        # Journal path: skip publish policy, force provisional agent authorship.
        return await self._commit(
            project_id=project_id,
            scope=scope,
            record_type=record_type,
            payload=payload,
            idempotency_key=idempotency_key,
            agent_id=agent_id,
            task_id=task_id,
            run_id=run_id,
            summary=summary,
            validation_state=ValidationState.PROVISIONAL,
            author_kind=AuthorKind.AGENT,
            evidence=list(artifact_refs or []),
            schema_record_name=schema_record_name,
            tags=list(tags or []),
            design_revision=design_revision,
            lookup_keys=lookup_keys,
            also_stores=also_stores,
            policy=policy,
            check_publish=False,
        )

    async def publish(
        self,
        *,
        scope: MemoryScope,
        record_type: RecordType,
        summary: str,
        payload: dict[str, Any],
        idempotency_key: str,
        agent_id: str = "",
        task_id: str = "",
        run_id: str = "",
        validation_state: ValidationState = ValidationState.PROVISIONAL,
        author_kind: AuthorKind = AuthorKind.AGENT,
        evidence: Optional[Sequence[str]] = None,
        schema_record_name: str = "",
        schema_version: int = 1,
        payload_schema_status: PayloadSchemaStatus = PayloadSchemaStatus.AGENT_DEFINED,
        tags: Optional[Sequence[str]] = None,
        supersedes: Optional[Sequence[str]] = None,
        design_revision: str = "",
        lookup_keys: Optional[Sequence[str]] = None,
        also_stores: Optional[Sequence[str]] = None,
        policy: Optional[WritePolicy] = None,
    ) -> MemoryRecord:
        """Publish a record visible to other agents (alias of ``write``).

        Runs publish policy checks and may mark superseded predecessors.

        Args:
            scope: Logical scope; ``scope.project`` becomes ``project_id``.
            record_type: Envelope kind (findings, gates, workflows, ...).
            summary: Human-readable summary for search and logs.
            payload: Agent-owned JSON body.
            idempotency_key: Dedup key for this publish.
            agent_id: Writing agent id.
            task_id: Optional originating task.
            run_id: Optional run id.
            validation_state: Trust ranking for the new record.
            author_kind: Human vs agent authorship.
            evidence: Evidence refs required for some record types.
            schema_record_name: Optional registered schema name.
            schema_version: Payload schema version.
            payload_schema_status: Registration strictness.
            tags: Free-form tags.
            supersedes: Prior memory ids to mark SUPERSEDED.
            design_revision: Revision denormalized onto the envelope.
            lookup_keys: KV keys for dictionary copies.
            also_stores: Extra store names.
            policy: Optional explicit write policy.

        Returns:
            The inserted or pre-existing ``MemoryRecord``.

        Side effects:
            Writes to the store, may apply copies, may supersede old records.

        Failures:
            Raises ``MemoryPolicyError`` when publish rules fail.
        """
        # Delegate to write with identical kwargs (publish is the public name).
        return await self.write(
            scope=scope,
            record_type=record_type,
            summary=summary,
            payload=payload,
            idempotency_key=idempotency_key,
            agent_id=agent_id,
            task_id=task_id,
            run_id=run_id,
            validation_state=validation_state,
            author_kind=author_kind,
            evidence=evidence,
            schema_record_name=schema_record_name,
            schema_version=schema_version,
            payload_schema_status=payload_schema_status,
            tags=tags,
            supersedes=supersedes,
            design_revision=design_revision,
            lookup_keys=lookup_keys,
            also_stores=also_stores,
            policy=policy,
        )

    async def write(
        self,
        *,
        scope: MemoryScope,
        record_type: RecordType,
        summary: str,
        payload: dict[str, Any],
        idempotency_key: str,
        agent_id: str = "",
        task_id: str = "",
        run_id: str = "",
        validation_state: ValidationState = ValidationState.PROVISIONAL,
        author_kind: AuthorKind = AuthorKind.AGENT,
        evidence: Optional[Sequence[str]] = None,
        schema_record_name: str = "",
        schema_version: int = 1,
        payload_schema_status: PayloadSchemaStatus = PayloadSchemaStatus.AGENT_DEFINED,
        tags: Optional[Sequence[str]] = None,
        supersedes: Optional[Sequence[str]] = None,
        design_revision: str = "",
        lookup_keys: Optional[Sequence[str]] = None,
        also_stores: Optional[Sequence[str]] = None,
        policy: Optional[WritePolicy] = None,
    ) -> MemoryRecord:
        """Write payloads according to ``policy`` with publish checks enabled.

        Each copy names a store and, when set, its own payload. Copies that
        omit a payload use ``payload``. The same store may appear more than
        once when the keys differ. With no policy, the record type selects a
        default set of copies that all share ``payload``.

        Args:
            See ``publish`` for field meanings; behavior is identical.

        Returns:
            The inserted or pre-existing ``MemoryRecord``.

        Side effects:
            Commits the envelope and optional copies; may supersede priors.

        Failures:
            Raises ``MemoryPolicyError`` on policy or backend limitations.
        """
        # Publish path: enable _check_publish and supersede handling in _commit.
        return await self._commit(
            project_id=scope.project,
            scope=scope,
            record_type=record_type,
            payload=payload,
            idempotency_key=idempotency_key,
            agent_id=agent_id,
            task_id=task_id,
            run_id=run_id,
            summary=summary,
            validation_state=validation_state,
            author_kind=author_kind,
            evidence=list(evidence or []),
            schema_record_name=schema_record_name,
            schema_version=schema_version,
            payload_schema_status=payload_schema_status,
            tags=list(tags or []),
            supersedes=list(supersedes or []),
            design_revision=design_revision,
            lookup_keys=lookup_keys,
            also_stores=also_stores,
            policy=policy,
            check_publish=True,
        )

    async def record_experiment(
        self,
        experiment: ExperimentRecord,
        *,
        scope: MemoryScope,
        agent_id: str,
        task_id: str,
        idempotency_key: str,
    ) -> MemoryRecord:
        """Publish an ``ExperimentRecord`` as a provisional experiment result.

        Args:
            experiment: Typed experiment payload (hypothesis becomes summary).
            scope: Scope for the published envelope.
            agent_id: Writing agent id.
            task_id: Originating task id.
            idempotency_key: Dedup key for this experiment write.

        Returns:
            The published ``MemoryRecord``.

        Side effects:
            Calls ``publish`` with ``EXPERIMENT_RESULT`` and registered schema.

        Failures:
            Propagates publish policy and store errors.
        """
        # Convenience wrapper that sets schema and evidence from the model.
        return await self.publish(
            scope=scope,
            record_type=RecordType.EXPERIMENT_RESULT,
            summary=experiment.hypothesis,
            payload=experiment.model_dump(mode="json"),
            idempotency_key=idempotency_key,
            agent_id=agent_id,
            task_id=task_id,
            evidence=[ref.uri for ref in experiment.evidence],
            schema_record_name="eda.experiment",
            payload_schema_status=PayloadSchemaStatus.REGISTERED_REQUIRED,
            validation_state=ValidationState.PROVISIONAL,
        )

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        """Fetch one record by memory id.

        Args:
            memory_id: Envelope id to look up.

        Returns:
            The ``MemoryRecord`` or ``None`` when missing.

        Side effects:
            Reads from the store.

        Failures:
            Propagates store errors.
        """
        # Thin pass-through to the backend primary key lookup.
        return await self.store.get(memory_id)

    async def get_lookup(self, *, project_id: str, key: str) -> Optional[MemoryRecord]:
        """Read one record by dictionary key. Uses the NoSQL copy when it exists.

        Args:
            project_id: Project namespace for the lookup.
            key: Lookup key previously stored on the envelope.

        Returns:
            Matching ``MemoryRecord`` or ``None``.

        Side effects:
            Reads from the store (native lookup or full scan fallback).

        Failures:
            Propagates store errors.
        """
        # Prefer a native KV reader when the backend implements one.
        reader = getattr(self.store, "get_lookup", None)
        if reader is not None:
            return await reader(project_id, key)
        # Fallback: linear scan matching project and lookup_keys membership.
        for record in await self.store.scan():
            if record.project_id == project_id and key in record.lookup_keys:
                return record
        # No match in the fallback scan.
        return None

    async def read_copy(self, *, store: str, project_id: str, key: str = "") -> Any:
        """Read the payload that a policy wrote to one store.

        Args:
            store: Destination store name (e.g. ``opensearch``).
            project_id: Project namespace for the copy.
            key: Optional key within that store.

        Returns:
            The copy payload as returned by the backend.

        Side effects:
            Reads from the named store via the plane.

        Failures:
            Raises ``MemoryPolicyError`` when the backend lacks ``read_copy``.
        """
        # Duck-type the optional multi-store reader.
        reader = getattr(self.store, "read_copy", None)
        if reader is None:
            raise MemoryPolicyError(f"This memory backend cannot read the {store} copy")
        # Delegate to the plane/backend implementation.
        return await reader(store, project_id, key)

    async def query(
        self,
        *,
        project: str,
        scope: Optional[MemoryScope] = None,
        record_types: Optional[Sequence[RecordType]] = None,
        validation_states: Optional[Sequence[ValidationState]] = None,
        block: str = "",
        stage: str = "",
        compatible_with_revision: str = "",
        schema_record_name: str = "",
        task_id: str = "",
    ) -> list[MemoryRecord]:
        """Scan and filter records for a project under optional constraints.

        Args:
            project: Required project id equality filter.
            scope: When set, keep records whose scope is contained by this one.
            record_types: Optional closed set of record kinds.
            validation_states: Optional closed set of trust states.
            block: When set, require matching or empty record block.
            stage: When set, require matching or empty record stage.
            compatible_with_revision: When set, require empty or equal revision.
            schema_record_name: Optional exact schema name filter.
            task_id: Optional exact task id filter.

        Returns:
            Matching records sorted by ``created_at`` ascending.

        Side effects:
            Scans the store (may be expensive on large backends).

        Failures:
            Propagates store scan errors.
        """
        # Materialize optional closed sets once for membership tests.
        wanted_types = set(record_types) if record_types else None
        wanted_states = set(validation_states) if validation_states else None
        # Accumulate survivors before sorting.
        found: list[MemoryRecord] = []
        # Full scan; backends may later specialize this path.
        for record in await self.store.scan():
            # Project is always required.
            if record.project_id != project:
                continue
            # Optional ancestor scope filter.
            if scope is not None and not scope.contains(record.scope):
                continue
            # Optional record-type filter.
            if wanted_types is not None and record.record_type not in wanted_types:
                continue
            # Optional validation-state filter.
            if wanted_states is not None and record.validation_state not in wanted_states:
                continue
            # Block filter: empty record block is treated as wildcard.
            if block and record.scope.block and record.scope.block != block:
                continue
            # Stage filter: empty record stage is treated as wildcard.
            if stage and record.scope.stage and record.scope.stage != stage:
                continue
            # Revision compatibility: empty revision is compatible with any.
            if compatible_with_revision and record.design_revision not in ("", compatible_with_revision):
                continue
            # Exact schema name when requested.
            if schema_record_name and record.schema_record_name != schema_record_name:
                continue
            # Exact task id when requested.
            if task_id and record.task_id != task_id:
                continue
            # Passed all filters.
            found.append(record)
        # Stable chronological order for context assembly consumers.
        found.sort(key=lambda item: item.created_at)
        return found

    async def query_payload(
        self,
        *,
        project: str,
        schema_record_name: str,
        filters: dict[str, Any],
    ) -> list[MemoryRecord]:
        """Query by schema name then filter on exact payload field equality.

        Args:
            project: Project namespace.
            schema_record_name: Required schema name on the envelope.
            filters: Payload key/value pairs that must all match.

        Returns:
            Records whose payload contains all filter equalities.

        Side effects:
            Performs a ``query`` then filters in process.

        Failures:
            Propagates underlying query errors.
        """
        # First narrow by project + schema name via query().
        records = await self.query(project=project, schema_record_name=schema_record_name)
        # Accumulate payload matches.
        matched: list[MemoryRecord] = []
        # Require every filter key to equal the payload value.
        for record in records:
            if all(record.payload.get(key) == value for key, value in filters.items()):
                matched.append(record)
        return matched

    async def search(self, *, project: str, query: str, scope: Optional[MemoryScope] = None) -> list[MemoryRecord]:
        """Full-text search within a project, preferring a native search backend.

        Args:
            project: Project namespace.
            query: Search string; empty returns an empty list on fallback.
            scope: Optional scope filter passed to native search or query.

        Returns:
            Matching records from native ``search_text`` or a naive substring
            scan over summary, tags, and JSON.

        Side effects:
            Reads from the store.

        Failures:
            Propagates store errors.
        """
        # Prefer OpenSearch (or similar) when the backend exposes search_text.
        search_text = getattr(self.store, "search_text", None)
        if search_text is not None:
            return await search_text(project=project, query=query, scope=scope)
        # Normalize the needle for case-insensitive substring matching.
        needle = query.lower().strip()
        if not needle:
            return []
        # Fallback hits list for file/memory backends without search_text.
        hits: list[MemoryRecord] = []
        # Scan via query() then substring-match a joined text blob.
        for record in await self.query(project=project, scope=scope):
            blob = " ".join([
                record.summary,
                " ".join(record.tags),
                record.model_dump_json(),
            ]).lower()
            if needle in blob:
                hits.append(record)
        return hits

    async def promote_candidate(
        self,
        *,
        candidate: str,
        expected_current_baseline: Optional[str],
        required_gate_ids: Sequence[str],
        scope: MemoryScope,
    ) -> PromotionResult:
        """Compare-and-swap the design baseline after validating required gates.

        Steps:

        1. Read the current baseline for ``scope.path``.
        2. Abort with ``stale_baseline`` if it does not match the expected value.
        3. Require each gate id to exist, be a ``GATE_DECISION``, be
           ``VALIDATED``, have ``passed is True``, and name this ``candidate``.
        4. CAS the baseline to ``candidate``.
        5. Insert a ``DESIGN_BASELINE`` record if one was not already written
           under the promotion idempotency key.

        Args:
            candidate: Candidate id to promote.
            expected_current_baseline: Baseline the caller believes is current
                (``None`` when promoting into an empty baseline).
            required_gate_ids: Memory ids of gates that must validate the candidate.
            scope: Scope whose ``path`` keys the baseline.

        Returns:
            A ``PromotionResult`` describing success or the failure reason.

        Side effects:
            May CAS the baseline and insert a design-baseline envelope.

        Failures:
            Propagates store errors; policy failures return ``promoted=False``.
        """
        # Read the baseline currently recorded for this scope path.
        current = await self.store.get_baseline(scope.path)
        # Optimistic concurrency: caller must still see the same baseline.
        if current != expected_current_baseline:
            return PromotionResult(
                promoted=False,
                candidate=candidate,
                reason="stale_baseline",
                current_baseline=current or "",
                scope_path=scope.path,
            )
        # Every required gate must independently validate this candidate.
        for gate_id in required_gate_ids:
            gate = await self.store.get(gate_id)
            # Missing or wrong record type cannot authorize promotion.
            if gate is None or gate.record_type != RecordType.GATE_DECISION:
                return PromotionResult(
                    promoted=False,
                    candidate=candidate,
                    reason=f"missing_gate:{gate_id}",
                    current_baseline=current or "",
                    scope_path=scope.path,
                )
            # Provisional or rejected gates are not enough.
            if gate.validation_state != ValidationState.VALIDATED:
                return PromotionResult(
                    promoted=False,
                    candidate=candidate,
                    reason=f"unvalidated_gate:{gate_id}",
                    current_baseline=current or "",
                    scope_path=scope.path,
                )
            # Gate must have passed for this exact candidate id.
            if gate.payload.get("passed") is not True or gate.payload.get("candidate") != candidate:
                return PromotionResult(
                    promoted=False,
                    candidate=candidate,
                    reason=f"gate_rejected:{gate_id}",
                    current_baseline=current or "",
                    scope_path=scope.path,
                )
        # Attempt the compare-and-set against the expected baseline.
        swapped = await self.store.compare_and_set_baseline(
            scope.path, expected_current_baseline, candidate
        )
        # Another writer won the race; report stale again with latest value.
        if not swapped:
            latest = await self.store.get_baseline(scope.path)
            return PromotionResult(
                promoted=False,
                candidate=candidate,
                reason="stale_baseline",
                current_baseline=latest or "",
                scope_path=scope.path,
            )
        # Idempotency key for the DESIGN_BASELINE envelope documenting the promote.
        baseline_key = f"promote:{scope.path}:{candidate}"
        # Insert the baseline record only once for this key.
        if await self.store.find_idempotency(baseline_key) is None:
            await self.store.insert(MemoryRecord(
                project_id=scope.project,
                design_revision=scope.revision,
                scope=scope,
                record_type=RecordType.DESIGN_BASELINE,
                validation_state=ValidationState.VALIDATED,
                summary=f"Promoted {candidate}",
                artifact_refs=list(required_gate_ids),
                payload={"candidate": candidate, "previous": expected_current_baseline or ""},
                idempotency_key=baseline_key,
                author_kind=AuthorKind.AGENT,
            ))
        # Success: candidate is now the current baseline for this scope.
        return PromotionResult(
            promoted=True,
            candidate=candidate,
            reason="promoted",
            current_baseline=candidate,
            scope_path=scope.path,
        )

    async def _commit(
        self,
        *,
        project_id: str,
        scope: MemoryScope,
        record_type: RecordType,
        payload: dict[str, Any],
        idempotency_key: str,
        agent_id: str,
        task_id: str,
        run_id: str,
        summary: str,
        validation_state: ValidationState,
        author_kind: AuthorKind,
        evidence: list[str],
        schema_record_name: str,
        tags: list[str],
        design_revision: str,
        lookup_keys: Optional[Sequence[str]],
        also_stores: Optional[Sequence[str]],
        policy: Optional[WritePolicy],
        check_publish: bool,
        schema_version: int = 1,
        payload_schema_status: PayloadSchemaStatus = PayloadSchemaStatus.AGENT_DEFINED,
        supersedes: Optional[list[str]] = None,
    ) -> MemoryRecord:
        """Shared insert path for append and write/publish.

        Args:
            project_id: Project namespace for the envelope.
            scope: Logical scope object stored on the record.
            record_type: Envelope kind selecting default placements.
            payload: Primary JSON payload.
            idempotency_key: Dedup key; existing hit returns immediately.
            agent_id: Writing agent id.
            task_id: Originating task id.
            run_id: Optional run id.
            summary: Human summary.
            validation_state: Trust ranking.
            author_kind: Human vs agent.
            evidence: Evidence ref list.
            schema_record_name: Optional schema name.
            tags: Tag list.
            design_revision: Revision string (falls back to ``scope.revision``).
            lookup_keys: Raw lookup keys cleaned by ``_clean_keys``.
            also_stores: Extra store names for compile_policy.
            policy: Optional explicit write policy.
            check_publish: When True, run ``_check_publish`` and supersede.
            schema_version: Payload schema version.
            payload_schema_status: Registration strictness.
            supersedes: Prior memory ids to mark SUPERSEDED after insert.

        Returns:
            The existing idempotent record or the newly inserted one.

        Side effects:
            Inserts, may apply copies, may update superseded records, may
            project decisions into Postgres.

        Failures:
            Raises ``MemoryPolicyError`` on policy/placement/backend issues.
        """
        # Publish path enforces authorship/evidence/baseline rules first.
        if check_publish:
            self._check_publish(
                record_type=record_type,
                author_kind=author_kind,
                evidence=evidence,
                validation_state=validation_state,
            )
        # Idempotent replay returns the original envelope unchanged.
        existing = await self.store.find_idempotency(idempotency_key)
        if existing is not None:
            return existing
        # Reject blank or whitespace-containing lookup keys.
        keys = _clean_keys(lookup_keys)
        # Compile default or explicit placements against the primary payload.
        try:
            compiled = compile_policy(
                record_type,
                payload,
                policy,
                list(also_stores or []),
                keys,
            )
        except PlacementError as exc:
            # Normalize placement errors into the service-level policy error.
            raise MemoryPolicyError(str(exc)) from exc
        # Non-Postgres copies require a plane-like apply_copies method.
        extra = [copy for copy in compiled.policy.copies if copy.store != "postgres"]
        apply = getattr(self.store, "apply_copies", None)
        if extra and apply is None:
            raise MemoryPolicyError(
                "This backend stores the Postgres envelope only. Use the memory plane to write other stores."
            )
        # Build the EDA envelope with compiled payload, keys, and placements.
        record = MemoryRecord(
            project_id=project_id,
            design_revision=design_revision or scope.revision,
            scope=scope,
            agent_id=agent_id,
            task_id=task_id,
            run_id=run_id,
            record_type=record_type,
            schema_record_name=schema_record_name,
            schema_version=schema_version,
            payload_schema_status=payload_schema_status,
            validation_state=validation_state,
            summary=summary,
            tags=list(tags),
            artifact_refs=list(evidence),
            supersedes=list(supersedes or []),
            payload=compiled.envelope_payload,
            idempotency_key=idempotency_key,
            author_kind=author_kind,
            lookup_keys=compiled.lookup_keys,
            placements=compiled.placements,
            copies=compiled.copies,
        )
        # Persist the envelope in the primary store.
        await self.store.insert(record)
        # Fan out non-envelope copies when the backend supports it.
        if apply is not None:
            await apply(record, compiled.policy.copies)
        # Decisions may also be projected into a Postgres decision table.
        if record.record_type == RecordType.DECISION:
            postgres = getattr(self.store, "postgres", None)
            record_decision = getattr(postgres, "record_decision", None)
            if record_decision is not None:
                await record_decision(record)
        # On publish, mark superseded predecessors so context can drop them.
        if check_publish:
            for old_id in record.supersedes:
                previous = await self.store.get(old_id)
                if previous is None:
                    continue
                previous.validation_state = ValidationState.SUPERSEDED
                await self.store.update(previous)
        # Return the committed envelope to the caller.
        return record

    def _check_publish(
        self,
        *,
        record_type: RecordType,
        author_kind: AuthorKind,
        evidence: list[str],
        validation_state: ValidationState,
    ) -> None:
        """Enforce publish-time envelope invariants before insert.

        Args:
            record_type: Kind being published.
            author_kind: Claimed authorship.
            evidence: Evidence refs accompanying the write.
            validation_state: Declared trust state.

        Returns:
            None when all rules pass.

        Side effects:
            None.

        Failures:
            Raises ``MemoryPolicyError`` when a rule is violated.
        """
        # Only humans may write design intent envelopes.
        if record_type == RecordType.HUMAN_INTENT and author_kind != AuthorKind.HUMAN:
            raise MemoryPolicyError("Agents cannot write human design intent")
        # Findings must cite evidence so claims are auditable.
        if record_type == RecordType.AGENT_FINDING and not evidence:
            raise MemoryPolicyError("Findings require evidence references")
        # Gates must declare a meaningful validation state.
        if record_type == RecordType.GATE_DECISION and validation_state not in {
            ValidationState.VALIDATED,
            ValidationState.PROVISIONAL,
            ValidationState.REJECTED,
        }:
            raise MemoryPolicyError("Gate decisions must declare a validation state")
        # Baselines move only through promote_candidate's CAS path.
        if record_type == RecordType.DESIGN_BASELINE:
            raise MemoryPolicyError("Baselines move only through promote_candidate")
        # Only humans may approve waivers.
        if record_type == RecordType.WAIVER and author_kind != AuthorKind.HUMAN:
            raise MemoryPolicyError("Agents may propose findings, not approve waivers")

    async def search_semantic(self, *, project: str, query: str, limit: int = 5) -> list[MemoryRecord]:
        """Vector similarity search delegated to the store backend.

        Args:
            project: Project namespace.
            query: Natural-language query to embed and compare.
            limit: Maximum number of hits to return.

        Returns:
            Ranked ``MemoryRecord`` list from the backend.

        Side effects:
            May call embedding services via the plane.

        Failures:
            Propagates backend errors (including missing semantic support).
        """
        # Plane backends implement search_semantic using embed_text.
        return await self.store.search_semantic(project=project, query=query, limit=limit)

    async def read_journal(self, *, project_id: str, task_id: str) -> list[dict[str, Any]]:
        """Read the Cassandra (or backend) journal entries for one task.

        Args:
            project_id: Project namespace.
            task_id: Task whose journal to read.

        Returns:
            A list of journal entry dicts from the backend.

        Side effects:
            Reads journal storage.

        Failures:
            Propagates backend errors.
        """
        # Task-local journal projection used for resume and audit.
        return await self.store.read_journal(project_id, task_id)

    async def read_scope_projection(self, *, project_id: str, stage: str, block: str) -> list[dict[str, Any]]:
        """Read the dictionary-style scope projection for stage/block.

        Args:
            project_id: Project namespace.
            stage: Stage segment; empty becomes ``_`` in the key.
            block: Block segment; empty becomes ``_`` in the key.

        Returns:
            Projection rows from the backend for that scope key.

        Side effects:
            Reads scope projection storage.

        Failures:
            Propagates backend errors.
        """
        # Match MemoryRecord.scope_key formatting for stage/block partitions.
        scope_key = f"stage={stage or '_'}|block={block or '_'}"
        return await self.store.read_scope(project_id, scope_key)

    async def put_artifact(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store artifact bytes and return the storage URI/key.

        Args:
            key: Object key within artifact storage.
            data: Raw bytes to store.
            content_type: MIME type for the object.

        Returns:
            URI or key string from the backend.

        Side effects:
            Writes to object storage (e.g. MinIO/S3).

        Failures:
            Propagates backend errors.
        """
        # Artifact bytes live outside the JSON envelope.
        return await self.store.put_artifact(key=key, data=data, content_type=content_type)

    async def get_artifact(self, key: str) -> bytes:
        """Fetch artifact bytes by key.

        Args:
            key: Object key previously returned by ``put_artifact``.

        Returns:
            Raw bytes from artifact storage.

        Side effects:
            Reads object storage.

        Failures:
            Propagates backend errors (including not-found).
        """
        # Symmetric read for put_artifact.
        return await self.store.get_artifact(key)

    async def put_source(self, *, path: str, data: bytes, message: str) -> str:
        """Commit source bytes into the memory-backed source repository.

        Args:
            path: Logical path within the source repo.
            data: File contents.
            message: Commit message.

        Returns:
            Revision or commit id from the backend.

        Side effects:
            Writes to the configured git/source directory.

        Failures:
            Propagates backend errors.
        """
        # Source control plane for design files tracked beside memory.
        return await self.store.put_source(path=path, data=data, message=message)

    async def get_source(self, path: str) -> bytes:
        """Read source bytes from the memory-backed source repository.

        Args:
            path: Logical path within the source repo.

        Returns:
            File contents as bytes.

        Side effects:
            Reads the source store.

        Failures:
            Propagates backend errors.
        """
        # Symmetric read for put_source.
        return await self.store.get_source(path)

    async def put_secret(self, *, name: str, value: str) -> None:
        """Store a named secret in the configured secret backend (e.g. Vault).

        Args:
            name: Secret name.
            value: Secret value.

        Returns:
            None.

        Side effects:
            Writes to the secret store.

        Failures:
            Propagates backend errors.
        """
        # Secrets never belong in MemoryRecord payloads.
        await self.store.put_secret(name=name, value=value)

    async def get_secret(self, name: str) -> str:
        """Fetch a named secret from the secret backend.

        Args:
            name: Secret name.

        Returns:
            The secret string value.

        Side effects:
            Reads the secret store.

        Failures:
            Propagates backend errors.
        """
        # Symmetric read for put_secret.
        return await self.store.get_secret(name)

    async def record_qor(
        self,
        *,
        project_id: str,
        experiment_id: str,
        metric: str,
        value: float,
        corner: str = "",
    ) -> None:
        """Record a quality-of-results measurement for an experiment.

        Args:
            project_id: Project namespace (passed as measurement namespace).
            experiment_id: Experiment id to associate the metric with.
            metric: Metric name.
            value: Numeric measurement.
            corner: Optional PVT corner dimension.

        Returns:
            None.

        Side effects:
            Writes a measurement row (e.g. ClickHouse).

        Failures:
            Propagates backend errors.
        """
        # Optional corner becomes a dimension map when provided.
        dimensions = {"corner": corner} if corner else {}
        await self.store.record_measurement(
            namespace=project_id,
            experiment_id=experiment_id,
            metric=metric,
            value=value,
            dimensions=dimensions,
        )

    async def query_qor(self, *, project_id: str, experiment_id: str) -> list[dict[str, Any]]:
        """Query QoR measurements for an experiment.

        Args:
            project_id: Project namespace.
            experiment_id: Experiment id to query.

        Returns:
            A list of measurement dicts from the backend.

        Side effects:
            Reads the measurement store.

        Failures:
            Propagates backend errors.
        """
        # Symmetric query for record_qor.
        return await self.store.query_measurements(namespace=project_id, experiment_id=experiment_id)

    async def acquire_lease(self, *, lease_id: str, task_id: str, holder: str, scope_path: str, ttl_secs: int = 60) -> bool:
        """Acquire a scoped work lease to prevent conflicting writers.

        Args:
            lease_id: Lease identity.
            task_id: Task requesting the lease.
            holder: Holder identity (usually agent id).
            scope_path: Scope path being leased.
            ttl_secs: Time-to-live in seconds.

        Returns:
            ``True`` when the lease was acquired; ``False`` otherwise.

        Side effects:
            Writes lease state in the backend.

        Failures:
            Propagates backend errors.
        """
        # Leases serialize mutations on a scope path across agents.
        return await self.store.acquire_lease(
            lease_id=lease_id, task_id=task_id, holder=holder, scope_path=scope_path, ttl_secs=ttl_secs
        )

    async def release_lease(self, *, task_id: str, holder: str) -> bool:
        """Release a previously acquired lease.

        Args:
            task_id: Task that holds the lease.
            holder: Holder identity that acquired it.

        Returns:
            ``True`` when a lease was released; ``False`` when none matched.

        Side effects:
            Clears lease state in the backend.

        Failures:
            Propagates backend errors.
        """
        # Symmetric release for acquire_lease.
        return await self.store.release_lease(task_id=task_id, holder=holder)

    async def record_approval(
        self,
        *,
        approval_id: str,
        subject_ref: str,
        approver: str,
        decision: str,
        evidence_ref: str = "",
    ) -> None:
        """Record a human or system approval decision on a subject.

        Args:
            approval_id: Stable approval id.
            subject_ref: What was approved (memory id, artifact uri, ...).
            approver: Approver identity.
            decision: Decision string (e.g. approved/rejected).
            evidence_ref: Optional evidence pointer.

        Returns:
            None.

        Side effects:
            Writes an approval row in the backend.

        Failures:
            Propagates backend errors.
        """
        # Approvals are tracked separately from MemoryRecord envelopes.
        await self.store.record_approval(
            approval_id=approval_id,
            subject_ref=subject_ref,
            approver=approver,
            decision=decision,
            evidence_ref=evidence_ref,
        )

    async def get_approval(self, approval_id: str) -> Optional[dict[str, Any]]:
        """Fetch one approval record by id.

        Args:
            approval_id: Approval id to look up.

        Returns:
            Approval dict or ``None`` when missing.

        Side effects:
            Reads approval storage.

        Failures:
            Propagates backend errors.
        """
        # Symmetric read for record_approval.
        return await self.store.get_approval(approval_id)

    async def list_decisions(self, scope_path: str) -> list[dict[str, Any]]:
        """List decision projections for a scope path.

        Args:
            scope_path: Logical ``/programs/...`` path.

        Returns:
            Decision dicts from the backend projection.

        Side effects:
            Reads decision storage.

        Failures:
            Propagates backend errors.
        """
        # Complements RecordType.DECISION envelope writes.
        return await self.store.list_decisions(scope_path)

    async def event_count(self) -> int:
        """Return the backend's count of emitted memory events.

        Returns:
            Integer event count (NATS or internal counter depending on store).

        Side effects:
            Reads backend telemetry counters.

        Failures:
            Propagates backend errors.
        """
        # Useful for tests asserting publish side effects.
        return await self.store.event_count()


def _clean_keys(lookup_keys: Optional[Sequence[str]]) -> list[str]:
    """Normalize lookup keys and reject blanks or keys containing whitespace.

    Args:
        lookup_keys: Optional sequence of raw key strings.

    Returns:
        A list of stripped keys.

    Side effects:
        None.

    Failures:
        Raises ``MemoryPolicyError`` when a key is empty after strip or
        contains any whitespace character.
    """
    # Accumulate cleaned keys in order.
    keys = []
    # Treat None as an empty sequence.
    for key in lookup_keys or []:
        # Strip leading/trailing whitespace before validation.
        cleaned = key.strip()
        # Empty or internal-whitespace keys break KV addressing.
        if not cleaned or any(character.isspace() for character in cleaned):
            raise MemoryPolicyError(f"Lookup key {key!r} must be a non-empty key without spaces")
        keys.append(cleaned)
    # Return the validated list for compile_policy.
    return keys


def open_memory(backend: str | None = None, root: str | None = None) -> EngineeringMemory:
    """Open the shared store. Default is a file directory so agent processes share it.

    Resolution order for the backend kind: explicit ``backend`` argument,
    ``MEMORY_BACKEND``, ``MEMORY_BACKEND``, then
    ``process.memory_backend`` in ``config/platform.yaml``.

    Args:
        backend: Optional override (``memory``, ``postgres``, ``plane``, ``file``).
        root: Optional file-store root. Otherwise ``MEMORY_ROOT`` or
            ``process.memory_root`` in ``config/platform.yaml``.

    Returns:
        An ``EngineeringMemory`` wrapping the selected backend.

    Side effects:
        May open database connections, plane clients, or create a directory.

    Failures:
        Propagates store construction errors for the selected backend.
    """
    # Local import keeps os dependency out of module import for pure facades.
    import os

    # Lazy imports so unused backends are not required at import time.
    from .file_store import FileStore
    from .memory_store import InMemoryStore

    from packages.platform_config import setting

    # Resolve backend kind from arg, environment, then config/platform.yaml.
    kind = (
        backend
        or os.environ.get("MEMORY_BACKEND")
        or os.environ.get("MEMORY_BACKEND")
        or setting("MEMORY_BACKEND")
    ).lower()
    # Process-local store for unit tests.
    if kind == "memory":
        return EngineeringMemory(InMemoryStore())
    # Postgres-only envelope store.
    if kind == "postgres":
        from .postgres_store import PostgresStore

        return EngineeringMemory(PostgresStore())
    # Full multi-store plane used by fleet compose.
    if kind == "plane":
        from .plane import MemoryPlane

        return EngineeringMemory(MemoryPlane())
    # Default: shared file directory so local multi-process agents can cooperate.
    path = root or os.environ.get("MEMORY_ROOT") or setting("MEMORY_ROOT")
    return EngineeringMemory(FileStore(path))
