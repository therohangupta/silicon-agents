#!/usr/bin/env python3
"""Check that every agent directory is a complete catalog spec.

Agent directories under ``agents/`` are the source of truth. This script does
not write or rewrite them; it only calls ``validate_catalog`` and prints how
many specs ``all_specs`` returns. Use it in CI or before Compose renders to
catch missing tools/config/Dockerfile mismatches early.

Run from ``agent_fleet/`` (or any cwd) — the script inserts its parent on
``sys.path`` so ``domains.eda.registry`` imports resolve without install.
"""

from __future__ import annotations

# sys.path manipulation so domains imports work without editable install.
import sys
# Path arithmetic to locate agent_fleet root.
from pathlib import Path

# Resolve agent_fleet/ as the package root (parent of scripts/).
ROOT = Path(__file__).resolve().parents[1]
# Prepend ROOT so `domains` and `packages` import as top-level names.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Catalog validators from the EDA domain package (import after path fix).
from domains.eda.registry import all_specs, validate_catalog  # noqa: E402


def main() -> None:
    """Validate the agent catalog and print the number of agent directories.

    ``validate_catalog`` raises on structural problems; on success
    ``all_specs`` returns the full list and we print its length for operators.
    """
    # Raises if any checked-in agent package is incomplete or inconsistent.
    validate_catalog()
    # Materialize the full spec list after validation succeeded.
    specs = all_specs()
    # Human-readable count for CI logs / local smoke checks.
    print(f"{len(specs)} agent directories")


# Standard script guard.
if __name__ == "__main__":
    # Delegate to main() so tests can import without running.
    main()
