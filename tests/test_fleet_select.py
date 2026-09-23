"""Fleet YAML selects agents by directory path."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.eda.fleet import FleetSelectionError, render_compose, select_agents
from packages.platform_config import load_platform

FLEETS = ROOT / "fleets"
REQUIREMENTS = "agents/eda/frontend/architecture/requirements"
RTL = "agents/eda/frontend/rtl/rtl_implementation"


def _ids(document: dict) -> list[str]:
    return [agent.agent_id for agent in select_agents(document)]


def _prefix() -> str:
    return str(load_platform()["agent_compose"]["working_dir_prefix"]).rstrip("/")


def test_paths_select_those_agents():
    selected = select_agents({"agents": [REQUIREMENTS, RTL + "/"]})
    assert [agent.agent_id for agent in selected] == ["requirements", "rtl_implementation"]
    assert selected[0].path == "eda/frontend/architecture/requirements"
    assert selected[1].working_dir == f"{_prefix()}/eda/frontend/rtl/rtl_implementation"


def test_config_yaml_suffix_matches_the_directory():
    by_yaml = select_agents({"agents": [REQUIREMENTS + "/config.yaml"]})
    by_dir = select_agents({"agents": ["eda/frontend/architecture/requirements"]})
    assert by_yaml[0].agent_id == by_dir[0].agent_id == "requirements"


def test_bare_agent_id_is_rejected():
    try:
        select_agents({"agents": ["requirements"]})
    except FleetSelectionError as exc:
        assert "path" in str(exc).lower()
    else:
        raise AssertionError("a bare agent id is not a directory path")


def test_explicit_empty_fleet_selects_nobody():
    assert select_agents({"agents": []}) == []


def test_checked_in_fleet_files_match_their_comments():
    frontend = _ids(yaml.safe_load((FLEETS / "frontend.yaml").read_text()))
    architecture = _ids(yaml.safe_load((FLEETS / "architecture.yaml").read_text()))
    pair = _ids(yaml.safe_load((FLEETS / "requirements-and-rtl.yaml").read_text()))
    assert len(frontend) > len(architecture)
    assert set(architecture) < set(frontend)
    assert pair == ["requirements", "rtl_implementation"]
    assert select_agents(yaml.safe_load((FLEETS / "platform-only.yaml").read_text())) == []


def test_bad_fleet_files_are_rejected():
    for document in (
        {},
        {"tracks": ["frontend"]},
        {"domains": ["architecture"]},
        {"all": True},
        {"agents": ["agents/not/a/real/agent"]},
        {"agents": [1]},
        [],
    ):
        try:
            select_agents(document)
        except FleetSelectionError:
            continue
        raise AssertionError(f"expected rejection for {document!r}")


def test_render_names_one_service_per_agent_on_the_shared_network():
    agents = select_agents({"agents": [REQUIREMENTS, RTL]})
    requirements_agent, rtl_agent = agents
    document = yaml.safe_load(render_compose(agents))
    compose = load_platform()["agent_compose"]
    prefix = _prefix()
    assert document["name"] == compose["project"]
    assert set(document["services"]) == {"requirements", "rtl_implementation"}
    requirements = document["services"]["requirements"]
    assert requirements["working_dir"] == f"{prefix}/eda/frontend/architecture/requirements"
    assert requirements["ports"] == [f"{requirements_agent.port}:{requirements_agent.port}"]
    assert requirements["environment"]["MEMORY_BACKEND"] == compose["memory_backend"]
    assert requirements["networks"] == [compose["network"]]
    network = document["networks"][compose["network"]]
    assert network["name"] == compose["external_network"]
    assert network["external"] is True
    rtl = document["services"]["rtl_implementation"]
    assert rtl["working_dir"] == f"{prefix}/eda/frontend/rtl/rtl_implementation"
    assert rtl["ports"] == [f"{rtl_agent.port}:{rtl_agent.port}"]


def test_published_platform_port_is_shifted_on_the_host():
    triage = select_agents({"agents": ["agents/eda/frontend/verification/failure_triage"]})[0]
    offset = int(load_platform()["agent_compose"]["host_port_collision_offset"])
    assert triage.host_port == triage.port + offset
    document = yaml.safe_load(render_compose([triage]))
    assert document["services"]["failure_triage"]["ports"] == [f"{triage.host_port}:{triage.port}"]
