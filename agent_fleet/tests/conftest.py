"""Test-only secrets required by the platform configuration schema."""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Prefer this checkout's import roots over similarly named editable installs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


for _name in (
    "AGENT_FLEET_POSTGRES_PASSWORD",
    "AGENT_FLEET_MINIO_ROOT_PASSWORD",
    "AGENT_FLEET_CLICKHOUSE_PASSWORD",
    "AGENT_FLEET_VAULT_DEV_ROOT_TOKEN",
):
    os.environ.setdefault(_name, f"test-{_name.lower()}")
