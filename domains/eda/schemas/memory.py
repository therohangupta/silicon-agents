"""Memory envelope, scope, context package, and write-policy re-exports.

Engineering memory separates the **system envelope** (identity, scope,
authorship, validation, evidence, placements) from the **agent-defined
payload**. ``MemoryRecord`` is that envelope. ``MemoryScope`` is the logical
``/programs/...`` path used for containment queries and baseline keys.

Context assembly returns ``ContextPackage`` (selected records, conflicts,
omitted count, token estimate) and can snapshot request parameters as a
``ContextManifest``. ``PromotionResult`` reports compare-and-swap baseline
promotion outcomes.

``StoreCopy``, ``StoredCopy``, and ``WritePolicy`` are re-exported from
``packages.memory.policy`` so EDA callers can import write-policy types from
the domain schemas package without reaching into the generic kit. Placement
defaults that choose which stores receive which record types live in
``domains.eda.memory.placements``.
"""

from __future__ import annotations

# UTC timestamps for created_at defaults.
from datetime import datetime, timezone
# Flexible payload typing and optional fields.
from typing import Any, Literal, Optional
# Short unique suffixes for memory_id generation.
from uuid import uuid4

# Pydantic models for the envelope and related documents.
from pydantic import BaseModel, Field

# Generic write-policy types re-exported for EDA callers.
from packages.memory.policy import StoreCopy, StoredCopy, WritePolicy

# Enums that type record kind, trust, authorship, and schema status.
from .enums import AuthorKind, PayloadSchemaStatus, RecordType, ValidationState


def _utcnow() -> datetime:
    """Return the current UTC time for ``MemoryRecord.created_at`` defaults.

    Returns:
        A timezone-aware ``datetime`` in UTC.

    Side effects:
        Reads the system clock.

    Failures:
        None under normal OS conditions.
    """
    # Always timezone-aware so serializers emit offset-aware ISO strings.
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    """Allocate a short unique id with a readable prefix.

    Args:
        prefix: Leading token such as ``mem`` for memory records.

    Returns:
        A string ``{prefix}-{12 hex chars}`` from a UUID4.

    Side effects:
        Draws entropy via ``uuid4``.

    Failures:
        None.
    """
    # Twelve hex chars keep ids short while remaining collision-resistant enough for demos.
    return f"{prefix}-{uuid4().hex[:12]}"


class MemoryScope(BaseModel):
    """Logical path under /programs. Storage may index the same record other ways.

    Empty optional segments mean "applies to the whole program" along that
    dimension. ``contains`` implements ancestor checks used by
    ``EngineeringMemory.query`` when a scope filter is supplied.
    ``path`` is also the key space for baseline compare-and-swap.
    """

    # Project / program id (required).
    project: str
    # Design revision segment; empty means all revisions.
    revision: str = ""
    # Subsystem segment under the revision.
    subsystem: str = ""
    # Block segment under the subsystem.
    block: str = ""
    # Flow stage leaf (rtl, place, route, ...).
    stage: str = ""

    @property
    def path(self) -> str:
        """Build the canonical ``/programs/...`` path for this scope.

        Returns:
            A slash-joined absolute-style path including only non-empty
            optional segments after the project.

        Side effects:
            None.

        Failures:
            None.
        """
        # Always start with programs/<project>.
        parts = ["programs", self.project]
        # Optional revision nest under revisions/.
        if self.revision:
            parts.extend(["revisions", self.revision])
        # Optional subsystem nest under subsystems/.
        if self.subsystem:
            parts.extend(["subsystems", self.subsystem])
        # Optional block nest under blocks/.
        if self.block:
            parts.extend(["blocks", self.block])
        # Stage is a leaf segment without an extra folder name.
        if self.stage:
            parts.append(self.stage)
        # Leading slash marks this as an absolute logical path.
        return "/" + "/".join(parts)

    def contains(self, other: "MemoryScope") -> bool:
        """Return True when ``other``'s path is this path or a descendant.

        Args:
            other: Scope to test for containment under this scope.

        Returns:
            ``False`` when projects differ. Otherwise ``True`` when paths are
            equal or ``other.path`` starts with this path plus a slash.

        Side effects:
            None.

        Failures:
            None.
        """
        # Different projects never contain each other.
        if self.project != other.project:
            return False
        # Exact match or strict descendant under this path prefix.
        return other.path == self.path or other.path.startswith(self.path.rstrip("/") + "/")


class MemoryRecord(BaseModel):
    """System envelope around an agent-defined payload.

    The service owns identity, scope, authorship, validation, evidence,
    idempotency, lookup keys, and placement metadata. The writing agent owns
    the ``payload`` dict. Stores persist this model (or projections of it);
    copy-specific foreign payloads are referenced via ``copies`` without
    repeating them on the envelope.
    """

    # Schema discriminator for versioned memory envelopes.
    schema_name: Literal["eda.memory-record/v1"] = "eda.memory-record/v1"
    # Unique memory id allocated at construction unless overridden.
    memory_id: str = Field(default_factory=lambda: new_id("mem"))
    # Project namespace the record belongs to.
    project_id: str
    # Design revision denormalized for filters; often mirrors scope.revision.
    design_revision: str = ""
    # Logical /programs scope for containment and baselines.
    scope: MemoryScope
    # Writing agent id when author_kind is AGENT.
    agent_id: str = ""
    # Task that produced the record, when applicable.
    task_id: str = ""
    # Optional run id for multi-attempt tasks.
    run_id: str = ""
    # Envelope kind that drives placements and publish rules.
    record_type: RecordType
    # Optional registered payload schema name (e.g. eda.workflow).
    schema_record_name: str = ""
    # Integer schema version for the payload shape.
    schema_version: int = 1
    # How strictly the payload schema is registered.
    payload_schema_status: PayloadSchemaStatus = PayloadSchemaStatus.AGENT_DEFINED
    # Trust ranking for context and promotion.
    validation_state: ValidationState = ValidationState.PROVISIONAL
    # Creation timestamp in UTC.
    created_at: datetime = Field(default_factory=_utcnow)
    # Short human summary for search and logs.
    summary: str = ""
    # Free-form tags for search facets.
    tags: list[str] = Field(default_factory=list)
    # Evidence artifact URIs or memory ids.
    artifact_refs: list[str] = Field(default_factory=list)
    # Memory ids this record supersedes (marked SUPERSEDED on publish).
    supersedes: list[str] = Field(default_factory=list)
    # Agent-defined JSON payload.
    payload: dict[str, Any] = Field(default_factory=dict)
    # Dedup key; identical keys return the existing record on commit.
    idempotency_key: str = ""
    # Human vs agent authorship for publish policy.
    author_kind: AuthorKind = AuthorKind.AGENT
    # Keys for cassandra_kv copies. placements is the set of stores that received
    # a copy. copies records each destination without repeating foreign payloads.
    lookup_keys: list[str] = Field(default_factory=list)
    # Store names that received a copy of this write.
    placements: list[str] = Field(default_factory=list)
    # Per-destination copy metadata without embedding foreign payloads again.
    copies: list[StoredCopy] = Field(default_factory=list)

    @property
    def scope_path(self) -> str:
        """Return ``scope.path`` for callers that want a flat string property.

        Returns:
            The canonical ``/programs/...`` path.

        Side effects:
            None.

        Failures:
            None.
        """
        # Delegate to MemoryScope.path without reimplementing join logic.
        return self.scope.path

    @property
    def scope_segments(self) -> dict[str, str]:
        """EDA scope fields. The store persists this map and does not name the keys.

        Returns:
            A dict with revision, subsystem, block, and stage. Revision prefers
            ``design_revision`` when set, else ``scope.revision``.

        Side effects:
            None.

        Failures:
            None.
        """
        # Stores persist this map generically without hard-coding EDA key names.
        return {
            "revision": self.design_revision or self.scope.revision,
            "subsystem": self.scope.subsystem,
            "block": self.scope.block,
            "stage": self.scope.stage,
        }

    @property
    def scope_key(self) -> str:
        """Partition key for dictionary-style scope reads.

        Stage and block are this domain's choice for the projection key used
        by ``read_scope_projection``. Missing values become ``_``.

        Returns:
            A string ``stage={stage}|block={block}``.

        Side effects:
            None.

        Failures:
            None.
        """
        # Underscore stands in for "unspecified" in the projection keyspace.
        stage = self.scope.stage or "_"
        block = self.scope.block or "_"
        # Format consumed by EngineeringMemory.read_scope_projection.
        return f"stage={stage}|block={block}"


class PromotionResult(BaseModel):
    """Outcome of a compare-and-swap design baseline promotion attempt.

    ``promoted`` is True only when all required gates validated the candidate
    and the baseline CAS succeeded. ``reason`` explains failures such as
    ``stale_baseline``, ``missing_gate``, ``unvalidated_gate``, or
    ``gate_rejected``.
    """

    # Schema discriminator for versioned promotion results.
    schema_name: Literal["eda.promotion-result/v1"] = "eda.promotion-result/v1"
    # Whether the candidate is now the current baseline.
    promoted: bool
    # Candidate id that was offered for promotion.
    candidate: str
    # Machine-readable reason for success or failure.
    reason: str = ""
    # Baseline observed after the attempt (candidate on success).
    current_baseline: str = ""
    # Scope path whose baseline was targeted.
    scope_path: str = ""


class ContextConflict(BaseModel):
    """Two or more records that disagree about the same subject.

    Produced by the generic assembler when conflicting claims share a subject
    key. Surfaced inside ``ContextPackage.conflicts`` for the agent to notice.
    """

    # Subject string extracted from payload.subject.
    subject: str
    # Memory ids of the conflicting records.
    memory_ids: list[str]
    # Human-readable conflict summary from the assembler.
    summary: str


class ContextPackage(BaseModel):
    """Budgeted set of memory records assembled for one task.

    Returned by ``ContextService.assemble`` and journaled (by id) when an
    agent starts work. Conflicts are surfaced rather than silently dropped
    under the default conflict policy.
    """

    # Schema discriminator for versioned context packages.
    schema_name: Literal["eda.context-package/v1"] = "eda.context-package/v1"
    # Task the package was assembled for.
    task_id: str
    # Records that fit the budget after precedence ranking.
    records: list[MemoryRecord] = Field(default_factory=list)
    # Subjects with conflicting claims among selected/considered records.
    conflicts: list[ContextConflict] = Field(default_factory=list)
    # Count of records omitted due to budget pressure.
    omitted: int = 0
    # Precedence list that was applied.
    precedence: list[str] = Field(default_factory=list)
    # Approximate token estimate of the included records.
    token_estimate: int = 0


class ContextManifest(BaseModel):
    """Durable snapshot of how a context package was requested.

    Records include/exclude lists, precedence, budget, and selected memory
    ids without embedding full payloads. Useful for audits and reproducibility.
    """

    # Schema discriminator for versioned context manifests.
    schema_name: Literal["eda.context-manifest/v1"] = "eda.context-manifest/v1"
    # Task the manifest describes.
    task_id: str
    # Include vocabulary that was requested.
    include: list[str] = Field(default_factory=list)
    # Exclude vocabulary that was applied.
    exclude: list[str] = Field(default_factory=list)
    # Precedence list applied during assembly.
    precedence: list[str] = Field(default_factory=list)
    # Token budget that constrained inclusion.
    token_budget: int = 80_000
    # Memory ids that made it into the package.
    record_ids: list[str] = Field(default_factory=list)
