"""Default store destinations for EDA record types.

Copy checks live in ``packages.memory.policy``. This module only decides which
stores an EDA record type is written to when the caller does not pass a
``WritePolicy``. ``compile_policy`` merges an explicit policy (or the defaults
below) with the primary payload, optional ``also_stores``, and lookup keys via
``assemble_copies``.

Three placement families are used:

* ``_SEARCHABLE`` — Postgres envelope plus OpenSearch, vector, and NATS so
  findings, requirements, experiments, and similar records are discoverable.
* ``_JOURNAL`` — Postgres plus Cassandra journal and NATS for task checkpoints
  and workflow revisions that are task-local or revisioned.
* ``_CANONICAL`` — Postgres plus NATS for decisions, gates, waivers, intent,
  baselines, and artifact refs that should stay authoritative.

Unknown record types fall back to ``_CANONICAL``. ``PlacementError`` is an
alias of the generic ``PolicyError`` so service code can catch a domain name.
"""

from __future__ import annotations

# Generic placement enum, policy error, copy models, and assembler.
from packages.memory.policy import Placement, PolicyError, StoreCopy, WritePolicy, assemble_copies

# EDA record kinds that select a default placement family.
from ..schemas.enums import RecordType

# Domain-facing alias so EngineeringMemory can raise/catch PlacementError.
PlacementError = PolicyError

# Stores for records that should be text/vector searchable and notified on NATS.
_SEARCHABLE = (
    Placement.POSTGRES,
    Placement.OPENSEARCH,
    Placement.VECTOR,
    Placement.NATS,
)
# Stores for task-local journals and workflow revisions.
_JOURNAL = (
    Placement.POSTGRES,
    Placement.CASSANDRA_JOURNAL,
    Placement.NATS,
)
# Stores for authoritative canonical records (decisions, gates, baselines).
_CANONICAL = (
    Placement.POSTGRES,
    Placement.NATS,
)

# Map each RecordType to the placement tuple used when no WritePolicy is given.
_BY_TYPE: dict[RecordType, tuple[Placement, ...]] = {
    # Task checkpoints stay in the journal path.
    RecordType.TASK_CHECKPOINT: _JOURNAL,
    # Findings need search and vector recall.
    RecordType.AGENT_FINDING: _SEARCHABLE,
    # Requirements are searchable across the program.
    RecordType.REQUIREMENT: _SEARCHABLE,
    # Interface contracts are searchable like requirements.
    RecordType.INTERFACE_CONTRACT: _SEARCHABLE,
    # Experiment results need search for prior-art queries.
    RecordType.EXPERIMENT_RESULT: _SEARCHABLE,
    # Issue links are searchable references.
    RecordType.ISSUE_LINK: _SEARCHABLE,
    # Decisions are canonical and notified.
    RecordType.DECISION: _CANONICAL,
    # Gates are canonical evidence for promotion.
    RecordType.GATE_DECISION: _CANONICAL,
    # Waivers are human-canonical.
    RecordType.WAIVER: _CANONICAL,
    # Human intent is canonical program input.
    RecordType.HUMAN_INTENT: _CANONICAL,
    # Baselines are canonical (created only via promote_candidate).
    RecordType.DESIGN_BASELINE: _CANONICAL,
    # Workflow revisions are journaled proposals.
    RecordType.WORKFLOW_REVISION: _JOURNAL,
    # Artifact refs are canonical pointers.
    RecordType.ARTIFACT_REF: _CANONICAL,
}


def compile_policy(
    record_type: RecordType,
    primary: dict,
    policy: WritePolicy | None = None,
    also_stores: list[str] | None = None,
    lookup_keys: list[str] | None = None,
):
    """Merge an explicit policy with the EDA default copies for this record type.

    When ``policy`` is provided, its ``copies`` list is used as-is. Otherwise
    ``_default_copies(record_type)`` supplies the domain defaults. The generic
    ``assemble_copies`` then attaches the primary payload, extra stores, and
    lookup keys into a compiled write plan.

    Args:
        record_type: Envelope kind selecting default placements.
        primary: Primary JSON payload shared by copies that omit their own.
        policy: Optional explicit ``WritePolicy`` from the caller.
        also_stores: Extra store names to include beyond the policy copies.
        lookup_keys: Dictionary keys for KV-style copies.

    Returns:
        The compiled copy plan from ``assemble_copies`` (envelope payload,
        placements, copies, and policy).

    Side effects:
        None.

    Failures:
        Propagates ``PlacementError`` / ``PolicyError`` when the policy is
        inconsistent (e.g. invalid store names or copy shapes).
    """
    # Prefer caller policy copies; else use EDA defaults for this record type.
    copies = list(policy.copies) if policy is not None else _default_copies(record_type)
    # Assemble primary payload, extras, and lookup keys into a write plan.
    return assemble_copies(
        copies,
        primary,
        also_stores=list(also_stores or []),
        lookup_keys=list(lookup_keys or []),
    )


def _default_copies(record_type: RecordType) -> list[StoreCopy]:
    """Build default ``StoreCopy`` rows for a record type.

    Args:
        record_type: Envelope kind to look up in ``_BY_TYPE``.

    Returns:
        A list of ``StoreCopy`` objects naming each default store. Unknown
        types receive the ``_CANONICAL`` family.

    Side effects:
        None.

    Failures:
        None.
    """
    # Fall back to canonical placements for any unlisted record type.
    chosen = _BY_TYPE.get(record_type, _CANONICAL)
    # Convert Placement enums into StoreCopy models with store name strings.
    return [StoreCopy(store=item.value) for item in chosen]
