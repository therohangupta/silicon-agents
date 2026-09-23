"""Agent directory scan matches the checked-in agent packages.

Locks in ``services.gateway.src.services.yaml_scanner.scan_agent_templates``:
silicon registered agents appear, legacy physical/digital demo names do not,
and every entry points at a real ``config.yaml`` with a non-demo category.
"""

from __future__ import annotations

from pathlib import Path

# Gateway scanner under contract.
from services.gateway.src.services.yaml_scanner import scan_agent_templates

# agent_fleet root (tests/contract -> parents[2]).
REPO = Path(__file__).resolve().parents[2]


def test_scan_lists_agent_directories():
    """scan_agent_templates lists silicon agents with valid config paths/categories."""
    # Perform a full tree scan of agent packages.
    found = scan_agent_templates()
    # Index by embodiment name for membership checks.
    names = {entry["name"] for entry in found}
    # Known silicon agents must be discoverable.
    assert "requirements" in names
    assert "chip_flow_lead" in names
    # Legacy demo names must stay gone.
    assert "moma" not in names
    assert "nav" not in names
    for entry in found:
        # Every hit ends with config.yaml.
        assert entry["config_path"].endswith("config.yaml")
        # Path is real relative to the repo root.
        assert (REPO / entry["config_path"]).is_file()
        # Categories are silicon tracks, not removed physical/digital demos.
        assert entry["category"] not in ("physical", "digital")
