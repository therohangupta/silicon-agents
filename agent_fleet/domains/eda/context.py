"""EDA context assembly: turn an agent's include policy into a memory package.

Generic ordering, token budgeting, and conflict detection live in
``packages.memory.context.assemble``. This module supplies the EDA vocabulary
that sits in front of that assembler:

* Include names such as ``requirements`` or ``gates`` map onto one or more
  ``RecordType`` values via ``INCLUDE_TYPES``.
* Scope filtering keeps records whose revision/subsystem/block/stage are
  empty (whole-program) or equal to the task's fields.
* Exclude names such as ``stale_candidates`` and ``unverified_agent_claims``
  drop superseded, provisional, or out-of-block records before budgeting.
* Rejected records are always dropped regardless of exclude lists.

``ContextService.assemble`` queries engineering memory by project and record
types, filters to the task scope, then hands the survivors to the generic
assembler with lambdas that read validation state, subject, claim, and an
approximate token size from each ``MemoryRecord``. The result is wrapped as
a ``ContextPackage`` the agent journals and (eventually) reasons over.

Only ``conflict_policy='surface_conflict'`` is supported. Other policies
raise ``ValueError`` so callers cannot silently change conflict semantics.
"""

from __future__ import annotations

# Optional unused elsewhere; Sequence types the include/exclude iterables.
from typing import Optional, Sequence

# Generic policy object and assembler that rank, budget, and surface conflicts.
from packages.memory.context import ContextPolicy, assemble
# Shared store facade used to query candidate records for a project.
from .memory.service import EngineeringMemory
# Record kinds and validation states used in include maps and exclude filters.
from .schemas.enums import RecordType, ValidationState
# Conflict, manifest, package, and record models returned to the agent.
from .schemas.memory import ContextConflict, ContextManifest, ContextPackage, MemoryRecord
# Task fields that define project and scope for filtering.
from .schemas.task import TaskSpec
# Per-agent include/exclude/precedence/protect/budget from config.yaml.
from .spec import AgentContext

# Names a task asks for, mapped onto record types.
# Each include token from AgentContext.include expands to zero or more
# RecordType values. Unknown names expand to an empty tuple and contribute
# nothing to the query filter (they are silently ignored at type resolution).
INCLUDE_TYPES: dict[str, tuple[RecordType, ...]] = {
    # Human-authored design intent statements.
    "human_intent": (RecordType.HUMAN_INTENT,),
    # Formal or informal requirements records.
    "requirements": (RecordType.REQUIREMENT,),
    # Block specs pull both requirements and interface contracts.
    "block_specification": (RecordType.REQUIREMENT, RecordType.INTERFACE_CONTRACT),
    # Explicit interface contracts between blocks or IPs.
    "interface_contracts": (RecordType.INTERFACE_CONTRACT,),
    # Open agent findings that still need attention.
    "open_findings": (RecordType.AGENT_FINDING,),
    # Experiment result envelopes for the current investigation.
    "experiments": (RecordType.EXPERIMENT_RESULT,),
    # Alias used by agents that want prior experiments specifically.
    "relevant_prior_experiments": (RecordType.EXPERIMENT_RESULT,),
    # Recorded engineering decisions.
    "decisions": (RecordType.DECISION,),
    # Canonical design baseline pointers for the scope.
    "canonical_source": (RecordType.DESIGN_BASELINE,),
    # Gate decisions from validators.
    "gates": (RecordType.GATE_DECISION,),
    # Proposed or accepted workflow revisions from leads.
    "workflows": (RecordType.WORKFLOW_REVISION,),
}


class ContextService:
    """Turn an agent's context policy into a package from shared memory.

    Include names, scope fields, and exclude names are EDA vocabulary owned
    by this class. Ordering, token budget enforcement, and conflict detection
    are delegated to the generic assembler in ``packages.memory.context``.
    Agents never call the generic assembler directly; they go through this
    service so record-type mapping and scope rules stay consistent.

    The service holds a reference to ``EngineeringMemory`` and performs async
    queries. It does not mutate memory; assembly is read-only aside from the
    store's own scan semantics.
    """

    def __init__(self, memory: EngineeringMemory) -> None:
        """Bind this assembler to a shared engineering-memory service.

        Args:
            memory: The ``EngineeringMemory`` instance used for ``query``.
                Typically the same object the agent uses for journaling.

        Returns:
            None. Stores ``memory`` on ``self.memory``.

        Side effects:
            None beyond retaining the reference.

        Failures:
            None at construction time.
        """
        # All assemble/query calls go through this shared facade.
        self.memory = memory

    async def assemble(
        self,
        task: TaskSpec,
        policy: AgentContext,
        *,
        conflict_policy: str = "surface_conflict",
    ) -> ContextPackage:
        """Query, filter, budget, and package context for one task.

        Steps:

        1. Refuse unsupported conflict policies.
        2. Expand ``policy.include`` names into ``RecordType`` values.
        3. Query memory for the task's project (optionally filtered by types).
        4. Keep records in scope and not excluded by ``policy.exclude``.
        5. Run the generic assembler with precedence, protect, drop, and budget.
        6. Wrap selected records, conflicts, and omitted count as a package.

        Args:
            task: Task whose project and scope fields drive query and filter.
            policy: Agent context policy from ``AgentSpec.context``.
            conflict_policy: Must be ``"surface_conflict"``. Other values
                raise ``ValueError`` because no alternate policy is wired.

        Returns:
            A ``ContextPackage`` with records, conflicts, omitted count,
            precedence list, and token estimate.

        Side effects:
            Reads from engineering memory via ``query``. Does not write.

        Failures:
            Raises ``ValueError`` for unsupported conflict policies.
            Propagates store errors from ``memory.query``.
        """
        # Only the surface-conflict strategy is implemented for EDA agents.
        if conflict_policy != "surface_conflict":
            raise ValueError("Only conflict_policy='surface_conflict' is supported")
        # Map include vocabulary onto concrete RecordType enums.
        record_types = self._types_for(policy.include)
        # Fetch candidates; None types means "all types for this project".
        records = await self.memory.query(
            project=task.project_id,
            record_types=record_types or None,
        )
        # Apply design-scope and exclude filters before budgeting.
        selected = [
            record for record in records
            if self._in_scope(record, task) and self._keep(record, task, policy.exclude)
        ]
        # Generic assembler ranks by validation-state precedence and budget.
        assembled = assemble(
            selected,
            policy=ContextPolicy(
                precedence=tuple(policy.precedence),
                protect=tuple(policy.protect),
                drop_states=tuple(policy.drop),
            ),
            token_budget=policy.token_budget,
            # Validation state string drives precedence and drop matching.
            state_of=lambda record: record.validation_state.value,
            # Subject key used when detecting conflicting claims.
            subject_of=lambda record: _text(record.payload.get("subject")),
            # Claim text paired with subject for conflict summaries.
            claim_of=lambda record: _text(record.payload.get("claim")),
            # Rough token estimate: JSON length in characters divided by four.
            size_of=lambda record: max(1, len(record.model_dump_json()) // 4),
        )
        # Re-wrap generic conflict objects into EDA ContextConflict models.
        return ContextPackage(
            task_id=task.task_id,
            records=list(assembled.records),
            conflicts=[
                ContextConflict(subject=item.subject, memory_ids=item.memory_ids, summary=item.summary)
                for item in assembled.conflicts
            ],
            omitted=assembled.omitted,
            precedence=list(policy.precedence),
            token_estimate=assembled.token_estimate,
        )

    def manifest(self, package: ContextPackage, *, include: Sequence[str], exclude: Sequence[str], token_budget: int) -> ContextManifest:
        """Build a durable manifest describing how a package was requested.

        The manifest records include/exclude lists, precedence, budget, and
        the memory ids that made it into the package. Agents or auditors can
        persist it without storing full record payloads.

        Args:
            package: The assembled ``ContextPackage`` to summarize.
            include: Include names that were requested for this assembly.
            exclude: Exclude names that were applied during filtering.
            token_budget: Budget that constrained the assembler.

        Returns:
            A ``ContextManifest`` suitable for logging or memory publication.

        Side effects:
            None.

        Failures:
            None beyond Pydantic validation on the model fields.
        """
        # Snapshot request parameters and selected record ids only.
        return ContextManifest(
            task_id=package.task_id,
            include=list(include),
            exclude=list(exclude),
            precedence=package.precedence,
            token_budget=token_budget,
            record_ids=[record.memory_id for record in package.records],
        )

    def _types_for(self, include: Sequence[str]) -> list[RecordType]:
        """Expand include vocabulary names into a flat list of record types.

        Args:
            include: Include tokens from ``AgentContext.include``.

        Returns:
            A list of ``RecordType`` values, possibly with duplicates when
            multiple include names map to the same type. An empty list means
            the caller should query without a type filter.

        Side effects:
            None.

        Failures:
            None; unknown names contribute nothing.
        """
        # Accumulate types in include order for stable query hints.
        types: list[RecordType] = []
        # Each name may expand to zero, one, or several RecordType values.
        for name in include:
            types.extend(INCLUDE_TYPES.get(name, ()))
        # Return the flat list (may be empty when nothing matched).
        return types

    def _in_scope(self, record: MemoryRecord, task: TaskSpec) -> bool:
        """Return True when a record applies to the task's design scope.

        An empty scope field on a record means it applies to the whole program
        along that dimension. A non-empty task field requires the record's
        corresponding field to be empty or equal.

        Args:
            record: Candidate memory record with ``design_revision`` and scope.
            task: Task carrying revision, subsystem, block, and stage filters.

        Returns:
            ``True`` when the record is in scope; ``False`` otherwise.

        Side effects:
            None.

        Failures:
            None.
        """
        # An empty scope field on a record means it applies to the whole program.
        # Reject records pinned to a different design revision than the task.
        if task.design_revision and record.design_revision not in ("", task.design_revision):
            return False
        # Reject records pinned to a different subsystem.
        if task.subsystem and record.scope.subsystem not in ("", task.subsystem):
            return False
        # Reject records pinned to a different block.
        if task.block and record.scope.block not in ("", task.block):
            return False
        # Reject records pinned to a different flow stage.
        if task.stage and record.scope.stage not in ("", task.stage):
            return False
        # All specified dimensions matched (or were wildcards on the record).
        return True

    def _keep(self, record: MemoryRecord, task: TaskSpec, exclude: Sequence[str]) -> bool:
        """Return True when exclude rules and hard rejects allow the record.

        Always drops ``REJECTED`` records. Optionally drops superseded/stale
        candidates, provisional claims, and records from unrelated blocks
        when the corresponding exclude names are present.

        Args:
            record: Candidate after scope filtering.
            task: Task used when comparing block identity.
            exclude: Exclude vocabulary from the agent context policy.

        Returns:
            ``True`` when the record should enter the assembler; ``False``
            when an exclude rule or rejection state drops it.

        Side effects:
            None.

        Failures:
            None.
        """
        # Drop superseded or explicitly stale records when asked.
        if "stale_candidates" in exclude and (
            record.validation_state == ValidationState.SUPERSEDED or record.payload.get("stale") is True
        ):
            return False
        # Drop provisional agent claims when the policy wants only verified data.
        if "unverified_agent_claims" in exclude and record.validation_state == ValidationState.PROVISIONAL:
            return False
        # Drop records from other blocks when the task is block-scoped.
        if "unrelated_blocks" in exclude and task.block and record.scope.block and record.scope.block != task.block:
            return False
        # Rejected records never enter context regardless of exclude list.
        if record.validation_state == ValidationState.REJECTED:
            return False
        # Survived all exclude and hard-reject checks.
        return True


def _text(value: object) -> str:
    """Coerce a payload field to a string for subject/claim extraction.

    Args:
        value: Arbitrary payload value, often from ``payload.get(...)``.

    Returns:
        The value when it is already a ``str``; otherwise an empty string
        so the generic assembler never sees ``None`` or non-text claims.

    Side effects:
        None.

    Failures:
        None.
    """
    # Only genuine strings participate in conflict subject/claim matching.
    return value if isinstance(value, str) else ""
