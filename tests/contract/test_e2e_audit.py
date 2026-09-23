"""Repo-wide audit checks (no live Postgres/NATS/Docker required).

Locks in: flat agent package layout, embodiment registry == config.yaml set,
``find_yaml_for_agent`` path resolution, and schema validation for every
checked-in agent config.
"""

from __future__ import annotations

from pathlib import Path

# Schema validator for agentfleet/v1 YAML.
from packages.agent_sdk.src.config.load import load_agent_config
# Gateway helpers that map registry names to on-disk YAML.
from services.gateway.src.services.yaml_scanner import find_yaml_for_agent, scan_agent_templates

# agent_fleet root.
REPO = Path(__file__).resolve().parents[2]
# All config.yaml paths under agents/, skipping caches and private dirs.
AGENT_CONFIGS = sorted(
    path for path in (REPO / "agents").rglob("config.yaml")
    if "__pycache__" not in path.parts and not any(part.startswith("_") for part in path.parts)
)


def test_agents_are_flat_packages():
    """Agent packages are named directories; digital/physical trees are gone."""
    # Parent directory name is the agent id.
    names = {path.parent.name for path in AGENT_CONFIGS}
    # Spot-check known silicon agents exist.
    assert "chip_flow_lead" in names
    assert "rtl_implementation" in names
    assert "signoff_validator" in names
    # Removed demo trees must not reappear.
    assert not (REPO / "agents" / "digital").exists()
    assert not (REPO / "agents" / "physical").exists()
    # registry size floor (matches ~70 silicon agents).
    assert len(names) >= 70


def test_agent_template_registry_matches_packages():
    """Gateway scan name set equals on-disk config.yaml parent names."""
    assert {entry["name"] for entry in scan_agent_templates()} == {path.parent.name for path in AGENT_CONFIGS}


def test_find_yaml_for_registered_type():
    """find_yaml_for_agent resolves rtl_implementation to its config path."""
    path = find_yaml_for_agent({"agent_type": "rtl_implementation"})
    # Must find a real file.
    assert path and Path(path).is_file()
    # Path ends with the expected package location.
    assert path.endswith("agents/eda/frontend/rtl/rtl_implementation/config.yaml")


def test_agent_configs_validate():
    """Every config.yaml validates and metadata.name matches directory name."""
    for config_path in AGENT_CONFIGS:
        # Schema validation must succeed for checked-in YAML.
        config = load_agent_config(config_path)
        # Directory name is the agent id / metadata.name.
        assert config.metadata.name == config_path.parent.name
        # Every agent declares at least one skill.
        assert config.skills
