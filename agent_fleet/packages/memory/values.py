"""Turn a record field into the string a store column holds.

Enum fields (``record_type``, ``validation_state``, etc.) expose a
``.value`` attribute; plain strings do not. Store adapters call ``label``
so both shapes land in the same TEXT column without each adapter repeating
``getattr(value, "value", value)`` logic. ``None`` becomes an empty string
so NOT NULL columns never receive SQL NULL from an unset enum.
"""

from __future__ import annotations

# Any accepts enums, strings, and other printable field values.
from typing import Any


def label(value: Any) -> str:
    """Return ``value.value`` when the object has one, otherwise ``str(value)``.

    Enum fields and plain strings both reach the same column this way. ``None``
    is stored as an empty string so adapters can pass the result straight into
    parameterized SQL without a separate null check.
    """
    # Prefer the enum's .value; fall back to the object itself.
    raw = getattr(value, "value", value)
    # Normalize None to empty; stringify everything else.
    return "" if raw is None else str(raw)
