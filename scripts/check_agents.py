#!/usr/bin/env python3
"""Check that every agent directory is a complete registry entry.

Agent directories under ``agents/`` are the source of truth. This script does
not write or rewrite them; it only calls ``validate_eda_registry`` and prints how
many configs ``all_configs`` returns. Use it in CI or before Compose renders to
catch missing tools/config/Dockerfile mismatches early.

Run from ```` (or any cwd) — the script inserts its parent on
``sys.path`` so ``domains.eda.fleet`` imports resolve without install.
"""

from __future__ import annotations

# sys.path manipulation so domains imports work without editable install.
import sys
# Path arithmetic to locate agent_fleet root.
from pathlib import Path

# Resolve  as the package root (parent of scripts/).
ROOT = Path(__file__).resolve().parents[1]
# Prepend ROOT so `domains` and `packages` import as top-level names.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Registry validators from the EDA domain package (import after path fix).
from domains.eda.fleet import all_configs, validate_eda_registry  # noqa: E402


def main() -> None:
    """Validate the agent registry and print the number of agent directories.

    ``validate_eda_registry`` raises on structural problems; on success
    ``all_configs`` returns the full list and we print its length for operators.
    """
    # Raises if any checked-in agent package is incomplete or inconsistent.
    validate_eda_registry()
    configs = all_configs()
    print(f"{len(configs)} agent directories")


# Standard script guard.
if __name__ == "__main__":
    # Delegate to main() so tests can import without running.
    main()
