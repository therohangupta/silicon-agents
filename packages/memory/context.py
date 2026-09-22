"""Rank, trim, and conflict-check a list of records the caller already chose.

``assemble`` is the context-assembly half of the memory plane. It does not
fetch records and does not interpret domain state names. The caller passes:

* the records already selected for a prompt package,
* callables that read state / subject / claim / size off each record, and
* a ``ContextPolicy`` of plain strings controlling precedence, protection,
  and drop lists.

The function returns an ``AssembledContext``: ordered records that fit the
token budget, any subject-level claim conflicts among kept records, how many
records were omitted to fit, and a token estimate. Conflicts are reported
but do not remove records — the LLM (or human) still sees both sides.
"""

from __future__ import annotations

# dataclass builds the immutable policy / result carriers.
from dataclasses import dataclass, field
# Any for opaque record objects; Callable/Sequence for assemble's hooks.
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class ContextPolicy:
    """Strings that control ordering and which records may leave the package.

    ``precedence`` is most-preferred first. A state missing from this tuple
    sorts after every listed state. ``protect`` states are kept even when the
    package is over ``token_budget``. ``drop_states`` are removed before
    ranking so they never consume budget.
    """

    # Most-preferred validation/state label first; used as sort key index.
    precedence: tuple[str, ...]
    # States that must survive budget trimming (e.g. golden baselines).
    protect: tuple[str, ...] = ()
    # States excluded before ranking (e.g. superseded / archived).
    drop_states: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssembledConflict:
    """Two or more kept records share a subject and disagree on the claim."""

    # Subject string extracted by the caller's ``subject_of`` hook.
    subject: str
    # memory_id values of every record in the conflicting group.
    memory_ids: list[str]
    # Human-readable summary listing the distinct claims.
    summary: str


@dataclass(frozen=True)
class AssembledContext:
    """Records that survived policy and budget, plus conflicts among those records.

    ``omitted`` counts records removed to fit ``token_budget``. ``token_estimate``
    is the sum of ``size_of`` over ``records``.
    """

    # Ordered list of records still in the package after trimming.
    records: list[Any] = field(default_factory=list)
    # Subject-level claim disagreements among kept records.
    conflicts: list[AssembledConflict] = field(default_factory=list)
    # How many eligible records were dropped for budget.
    omitted: int = 0
    # Sum of size_of(record) for the kept set.
    token_estimate: int = 0


def assemble(
    records: Sequence[Any],
    *,
    policy: ContextPolicy,
    token_budget: int,
    state_of: Callable[[Any], str],
    subject_of: Callable[[Any], str],
    claim_of: Callable[[Any], str],
    size_of: Callable[[Any], int],
) -> AssembledContext:
    """Return records ordered by ``policy.precedence``, trimmed to ``token_budget``.

    ``state_of``, ``subject_of``, ``claim_of``, and ``size_of`` are the only
    way this function reads a record — keeping domain types out of this
    package. Records whose state is in ``policy.drop_states`` are excluded
    before ranking. A subject with more than one distinct claim among the
    kept records becomes a conflict. The conflict is reported; the records
    stay in the package so the consumer can reconcile them.
    """
    # Drop states the policy says must never enter the package.
    eligible = [record for record in records if state_of(record) not in policy.drop_states]
    # Rank by precedence index, then by created_at string for a stable tie-break.
    ranked = sorted(eligible, key=lambda record: (_rank(state_of(record), policy), _tie(record)))
    # Trim lowest-ranked non-protected records until under budget.
    kept, omitted, token_estimate = _fit(ranked, policy, token_budget, state_of, size_of)
    # Package the kept set with any subject/claim conflicts detected among them.
    return AssembledContext(
        # Local ``records`` ← kept,.
        records=kept,
        # Local ``conflicts`` ← _conflicts(kept, subject_of, claim_of),.
        conflicts=_conflicts(kept, subject_of, claim_of),
        # Local ``omitted`` ← omitted,.
        omitted=omitted,
        # Local ``token_estimate`` ← token_estimate,.
        token_estimate=token_estimate,
    )


def _rank(state: str, policy: ContextPolicy) -> int:
    """Return the precedence index for ``state``, or len(precedence) if unknown."""
    try:
        # Listed states sort by their position in the policy tuple.
        return policy.precedence.index(state)
    # On except ValueError: recover or re-raise as appropriate.
    except ValueError:
        # Unknown states sort after every explicitly listed one.
        return len(policy.precedence)


def _tie(record: Any) -> str:
    """Stable secondary sort key from ``created_at`` when present."""
    # Prefer the record's created_at attribute when the envelope has one.
    created = getattr(record, "created_at", None)
    # Empty string when missing so sorting never compares None.
    return "" if created is None else str(created)


def _fit(
    records: list[Any],
    policy: ContextPolicy,
    token_budget: int,
    state_of: Callable[[Any], str],
    size_of: Callable[[Any], int],
) -> tuple[list[Any], int, int]:
    """Drop lowest-ranked unprotected records until the package fits the budget.

    Returns ``(kept_records, omitted_count, token_estimate)``.
    """
    # Drop the lowest-ranked records first. Protected states stay.
    # Reverse rank so we consider worst (highest index) victims first.
    victims = sorted(records, key=lambda record: _rank(state_of(record), policy), reverse=True)
    # Identity map preserves insertion order of the ranked list while allowing pops.
    kept = {id(record): record for record in records}
    # Count how many records we remove for the omitted field.
    dropped = 0
    # Loop: for victim in victims.
    for victim in victims:
        # Stop as soon as the remaining set is within budget.
        if _tokens(list(kept.values()), size_of) <= token_budget:
            break
        # Never drop protected states even if over budget.
        if state_of(victim) in policy.protect:
            continue
        # Remove this victim if it is still in the kept map.
        if kept.pop(id(victim), None) is not None:
            dropped += 1
    # Materialize kept values and recompute the final token sum.
    return list(kept.values()), dropped, _tokens(list(kept.values()), size_of)


def _tokens(records: Sequence[Any], size_of: Callable[[Any], int]) -> int:
    """Sum ``size_of`` across every record in the sequence."""
    return sum(size_of(record) for record in records)


def _conflicts(
    records: Sequence[Any],
    subject_of: Callable[[Any], str],
    claim_of: Callable[[Any], str],
) -> list[AssembledConflict]:
    """Group kept records by subject and flag groups with disagreeing claims."""
    # Bucket records that share a non-empty subject string.
    groups: dict[str, list[Any]] = {}
    # Loop: for record in records.
    for record in records:
        # Extract the subject via the caller-supplied hook.
        subject = subject_of(record)
        # Only when (subject).
        if subject:
            # Append into the subject's group list.
            groups.setdefault(subject, []).append(record)
    # Collect one AssembledConflict per subject with multiple distinct claims.
    conflicts: list[AssembledConflict] = []
    # Loop: for subject, grouped in groups.items().
    for subject, grouped in groups.items():
        # Distinct non-empty claims for this subject.
        claims = {claim_of(record) for record in grouped if claim_of(record)}
        # Only when (len(claims) > 1).
        if len(claims) > 1:
            # Report the conflict without removing either side from the package.
            conflicts.append(AssembledConflict(
                # Local ``subject`` ← subject,.
                subject=subject,
                # Local ``memory_ids`` ← [str(getattr(record, "memory_id", "")) for record in grouped],.
                memory_ids=[str(getattr(record, "memory_id", "")) for record in grouped],
                # Local ``summary`` ← f"Conflicting claims for {subject}: {sorted(claims)}",.
                summary=f"Conflicting claims for {subject}: {sorted(claims)}",
            ))
    # Hand ``conflicts`` back to the caller.
    return conflicts
