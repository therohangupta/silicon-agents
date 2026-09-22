"""Generic context assembly does not assume a domain's knowledge types.

Locks in ``packages.memory.context.assemble`` + ``ContextPolicy``: caller-supplied
precedence, protect, and drop_states drive inclusion; conflicts surface when
the same subject has disagreeing claims under the retained states.
"""

# Lightweight stand-ins for memory records without importing domain schemas.
from types import SimpleNamespace

# Unit under test.
from packages.memory.context import ContextPolicy, assemble


def _record(state: str, subject: str, claim: str, size: int = 10):
    """Build a SimpleNamespace shaped like a memory row for assemble()."""
    # memory_id is unique enough for debugging omitted counts.
    return SimpleNamespace(
        memory_id=f"{state}-{claim}",
        validation=state,
        subject=subject,
        claim=claim,
        weight=size,
        created_at="t",
    )


def test_assemble_uses_caller_precedence_without_a_human_state():
    """Precedence prefers observed over estimated; drop_states remove discarded; budget omits."""
    records = [
        _record("estimated", "latency", "high", size=50),
        _record("observed", "latency", "low", size=50),
        _record("discarded", "latency", "ignore", size=10),
    ]
    assembled = assemble(
        records,
        policy=ContextPolicy(
            # observed wins over estimated when both present.
            precedence=("observed", "estimated"),
            # protected states are never dropped for budget (here: observed).
            protect=("observed",),
            # discarded never enters the package.
            drop_states=("discarded",),
        ),
        # Budget 60 fits one size=50 record; the other is omitted.
        token_budget=60,
        state_of=lambda record: record.validation,
        subject_of=lambda record: record.subject,
        claim_of=lambda record: record.claim,
        size_of=lambda record: record.weight,
    )
    # Only the observed row survives precedence + budget.
    assert [record.validation for record in assembled.records] == ["observed"]
    # The estimated row was omitted due to budget (discarded never counted).
    assert assembled.omitted == 1
    # Single-claim subject => no conflict entries.
    assert assembled.conflicts == []


def test_assemble_surfaces_conflicting_claims():
    """Two observed claims on the same subject produce one conflict entry."""
    records = [
        _record("observed", "latency", "high"),
        _record("observed", "latency", "low"),
    ]
    assembled = assemble(
        records,
        policy=ContextPolicy(precedence=("observed",), protect=("observed",)),
        # Large budget retains both rows so conflict detection can fire.
        token_budget=100,
        state_of=lambda record: record.validation,
        subject_of=lambda record: record.subject,
        claim_of=lambda record: record.claim,
        size_of=lambda record: record.weight,
    )
    # Exactly one conflict object for subject latency.
    assert len(assembled.conflicts) == 1
    # Conflict is keyed by the shared subject.
    assert assembled.conflicts[0].subject == "latency"
