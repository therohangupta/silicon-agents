"""Choose which agents a fleet file starts and render their compose services.

A fleet file lists agent directories:

    agents:
      - agents/frontend/architecture/requirements
      - agents/frontend/rtl/rtl_implementation

Each entry is a path to an agent directory, or to that directory's
``config.yaml``. The path may be relative to ``agents/`` or include the
``agents/`` prefix. An empty list starts no agent containers.

``select_agents`` returns ``SelectedAgent`` rows ordered by port. A container
port that ``config/platform.yaml`` publishes on the host is shifted by that
file's ``host_port_collision_offset``. ``render_compose`` reads the agent
image, network, and environment from the same file.

``FleetError`` is raised for unknown fields, bad path lists, unknown
directories, and host-port collisions.
"""

from __future__ import annotations

# Frozen dataclass for selected agent rows used by compose rendering.
from dataclasses import dataclass

# Catalog of all AgentSpec objects when the caller does not pass an override.
from .registry import all_specs
# Typed agent identity including path and port.
from .spec import AgentSpec
# Platform ports, image, network, and agent environment. No local copies.
from packages.platform_config import agent_environment, load_platform, published_host_ports


class FleetError(ValueError):
    """Raised when a fleet document is malformed or selects an impossible set.

    Covers unknown fields, invalid path lists, unknown agent directories,
    and duplicate published host ports after reservation shifting.
    """


@dataclass(frozen=True)
class SelectedAgent:
    """One agent chosen by a fleet file, with container and host port mapping.

    Attributes:
        agent_id: Catalog id used as the compose service name.
        path: Slash-joined relative path under ``agents/``.
        port: Container listen port from the agent spec.
        host_port: Published host port (possibly shifted off reserved ports).
    """

    # Compose service name and catalog key.
    agent_id: str
    # Relative directory path used to build working_dir.
    path: str
    # In-container listen port from config.yaml connection.port.
    port: int
    # Host-side published port after reservation collision handling.
    host_port: int

    @property
    def working_dir(self) -> str:
        """Return the container working directory for this agent's sources.

        Returns:
            ``agent_compose.working_dir_prefix`` from ``config/platform.yaml``
            plus this agent's directory.

        Side effects:
            None.

        Failures:
            None.
        """
        # Prefix comes from config/platform.yaml agent_compose.working_dir_prefix.
        prefix = str(load_platform()["agent_compose"]["working_dir_prefix"]).rstrip("/")
        return f"{prefix}/{self.path}"


def select_agents(document: object, specs: list[AgentSpec] | None = None) -> list[SelectedAgent]:
    """Return the agents a fleet document includes, ordered by port.

    The document has one key, ``agents``. Each entry names one agent
    directory. Validates host-port uniqueness after applying reservation shifts.

    Args:
        document: Parsed fleet YAML; must be a mapping whose only key is
            ``agents``.
        specs: Optional catalog override (useful in tests). Defaults to
            ``all_specs()``.

    Returns:
        A list of ``SelectedAgent`` sorted by ``(port, agent_id)``.

    Side effects:
        May load and validate the full agent catalog when ``specs`` is None.

    Failures:
        Raises ``FleetError`` for malformed documents, unknown directories,
        or host-port collisions.
    """
    # Fleet files must be mappings (YAML objects), not lists or scalars.
    if not isinstance(document, dict):
        raise FleetError("Fleet file must be a mapping")
    # The only accepted field is agents; reject every other selector or typo.
    if set(document) != {"agents"}:
        unknown = sorted(set(document) - {"agents"})
        if unknown:
            raise FleetError(f"Unknown fleet field {unknown[0]}. The only field is agents.")
        raise FleetError("Fleet file needs an agents list of directory paths")

    # Use the injected catalog or the process-wide validated catalog.
    catalog = list(specs) if specs is not None else all_specs()
    # Index by directory path relative to agents/.
    by_path = {spec.path: spec for spec in catalog}
    # Chosen set keyed by agent_id so a repeated path dedupes.
    chosen: dict[str, AgentSpec] = {}
    for raw in _as_list(document.get("agents"), "agents"):
        spec = _spec_for_path(raw, by_path)
        chosen[spec.agent_id] = spec

    # Materialize SelectedAgent rows with host-port shifting applied.
    selected = [
        SelectedAgent(spec.agent_id, spec.path, spec.port, _host_port(spec.port))
        for spec in chosen.values()
    ]
    # Stable order by container port then id for readable compose diffs.
    selected.sort(key=lambda item: (item.port, item.agent_id))
    # Detect two agents publishing the same host port after shifting.
    published = [item.host_port for item in selected]
    if len(published) != len(set(published)):
        raise FleetError("Selected agents publish the same host port")
    # Hand the ordered selection to compose rendering or startup scripts.
    return selected


def render_compose(agents: list[SelectedAgent]) -> str:
    """Render a Docker Compose document for the selected agents.

    Image, command, network, project name, and environment come from
    ``config/platform.yaml``. Each service publishes ``host_port:port``.

    Args:
        agents: Output of ``select_agents`` (may be empty).

    Returns:
        A YAML string prefixed with a generated-by comment.

    Side effects:
        Imports ``yaml`` locally to avoid a hard dependency at module import
        when only selection is needed.

    Failures:
        Propagates YAML serialization errors (unlikely for this structure).
    """
    # Local import keeps yaml optional for callers that only select agents.
    import yaml

    platform = load_platform()["agent_compose"]
    from domains.eda.platform_config import merge_agent_environment

    environment = merge_agent_environment()
    # Build the services mapping keyed by agent_id.
    services = {}
    # One compose service per selected agent.
    for agent in agents:
        services[agent.agent_id] = {
            "image": platform["image"],
            "build": {
                "context": platform["build_context"],
                "dockerfile": platform["dockerfile"],
            },
            "working_dir": agent.working_dir,
            "command": list(platform["command"]),
            "ports": [f"{agent.host_port}:{agent.port}"],
            "restart": platform["restart"],
            "environment": dict(environment),
            "networks": [platform["network"]],
        }
    # Top-level compose project attached to the existing platform network.
    document = {
        "name": platform["project"],
        "services": services,
        "networks": {
            platform["network"]: {
                "external": True,
                "name": platform["external_network"],
            },
        },
    }
    # Emit YAML without sorting keys so service insertion order is preserved.
    body = yaml.safe_dump(document, sort_keys=False)
    # Prefix with a comment so operators know not to hand-edit the file.
    return (
        "# Generated by scripts/startup.sh. The fleet YAML selects these agents.\n"
        + body
    )


def _host_port(port: int) -> int:
    """Map a container port to a host port, avoiding reserved platform ports.

    Args:
        port: Container listen port from the agent spec.

    Returns:
        ``port`` unchanged when it is not a published platform port; otherwise
        ``port`` plus ``agent_compose.host_port_collision_offset`` from
        ``config/platform.yaml``.

    Side effects:
        None.

    Failures:
        Raises ``FleetError`` when both the native and shifted ports are
        reserved.
    """
    platform = load_platform()
    reserved = published_host_ports(platform)
    # Most agents publish the same number on the host.
    if port not in reserved:
        return port
    # Shift when the platform already publishes this host port.
    offset = int(platform["agent_compose"]["host_port_collision_offset"])
    shifted = port + offset
    # If the shifted port is also reserved, there is no automatic mapping.
    if shifted in reserved:
        raise FleetError(f"No free host port for agent port {port}")
    # Publish on the shifted host port; container still listens on `port`.
    return shifted


def _as_list(value: object, field: str) -> list[str]:
    """Normalize the agents field into a list of non-empty path strings.

    Args:
        value: Raw YAML value; ``None`` means the field was omitted.
        field: Field name used in error messages.

    Returns:
        A list of stripped strings, or an empty list when ``value`` is None.

    Side effects:
        None.

    Failures:
        Raises ``FleetError`` when the value is not a list of non-empty strings.
    """
    # Omitted fields contribute no selections.
    if value is None:
        return []
    # Reject scalars, maps, and lists containing blank or non-string items.
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise FleetError(f"{field} must be a list of directory paths")
    # Strip whitespace so YAML quoting quirks do not create unknown paths.
    return [item.strip() for item in value]


def _spec_for_path(raw: str, by_path: dict[str, AgentSpec]) -> AgentSpec:
    """Match a fleet entry to the agent directory it names.

    Args:
        raw: A path such as ``agents/frontend/architecture/requirements`` or
            that directory's ``config.yaml``.
        by_path: Catalog indexed by the directory relative to ``agents/``.

    Returns:
        The ``AgentSpec`` for that directory.

    Side effects:
        None.

    Failures:
        Raises ``FleetError`` when the path does not name a cataloged agent.
    """
    # Accept a trailing slash and either the directory or its config file.
    text = raw.strip().strip("/")
    if text.endswith("config.yaml"):
        text = text[: -len("config.yaml")].strip("/")
    if text.startswith("agents/"):
        text = text[len("agents/"):]
    spec = by_path.get(text)
    if spec is None:
        raise FleetError(
            f"Unknown agent path {raw}. "
            "Use a directory such as agents/frontend/architecture/requirements."
        )
    return spec
