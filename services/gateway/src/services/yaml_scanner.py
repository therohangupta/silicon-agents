"""
YAML configuration scanning for agent templates and planner/allocator methods.

This service walks configured filesystem roots to discover:

1. **Agent packages** — every ``config.yaml`` under ``AGENT_PACKAGE_DIRS``
   becomes a catalog entry for ``GET /api/agent-templates``.
2. **Planner / allocator methods** — each subdirectory under
   ``PLANNER_TYPES_DIR`` / ``ALLOCATOR_TYPES_DIR`` that contains ``summary.yaml``
   becomes a method entry for strategies and methods routers.

Helpers also resolve a registered agent's ``agent_type`` back to its YAML path
(``find_yaml_for_agent``) and map strategy directory names to ``summary.yaml``
integer ids used by allocate/create plan RPCs.

Scanning is synchronous and read-only aside from opening files. Parse errors
for individual YAMLs are logged and skipped so one bad file does not break the
catalog. Duplicate agent template names (case-insensitive) keep the first seen.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import yaml

# Logger for per-file load failures during scans.
logger = logging.getLogger(__name__)

# Roots and defaults from gateway config re-exports.
from ..config import (
    AGENT_PACKAGE_DIRS,
    PLANNER_TYPES_DIR,
    ALLOCATOR_TYPES_DIR,
    DEFAULT_AGENT_BASE_PORT,
    REPO_ROOT,
)


def _category_from_path(yaml_path: Path) -> str:
    """
    Return the agent's stable full directory path under ``agents/``.

    Purpose:
        Populate ``AgentTemplateResponse.category`` with the directory path
        under ``agents/``.

    Args:
        yaml_path: Absolute path to a ``config.yaml`` file.

    Returns:
        The complete slash-joined agent directory path, or the parent name if
        the YAML lives outside the configured agents root.

    Side effects:
        None.

    Failure behavior:
        ``ValueError`` from ``relative_to`` is caught; falls back to parent name.
    """
    try:
        relative = yaml_path.parent.relative_to(REPO_ROOT / "agents")
    except ValueError:
        return yaml_path.parent.name
    return relative.as_posix()


def _capability_ids(config: dict) -> list[str]:
    """
    Flatten YAML capability entries into string ids for API responses.

    Args:
        config: Loaded agent config mapping.

    Returns:
        List of capability id strings (empty if none).

    Side effects:
        None.

    Failure behavior:
        Skips dict entries without ``id``; stringifies non-dict truthy values.
    """
    # Raw list from YAML (may be missing).
    caps = config.get("capabilities") or []
    ids: list[str] = []
    for cap in caps:
        if isinstance(cap, dict):
            # Structured capability objects expose a stable id field.
            cid = cap.get("id")
            if cid:
                ids.append(str(cid))
        elif cap:
            # Legacy plain-string capability.
            ids.append(str(cap))
    return ids


def _parse_agent_config_yaml(yaml_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load one agent ``config.yaml`` into an agent template dict for the catalog API.

    Args:
        yaml_path: Path to the YAML file.

    Returns:
        AgentTemplate field dict, or ``None`` if the file cannot be loaded.

    Side effects:
        Reads the file from disk; logs errors on failure.

    Failure behavior:
        Returns ``None`` after logging; does not raise to the scanner loop.
    """
    try:
        # Parse YAML; treat empty documents as {}.
        with open(yaml_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Error loading %s: %s", yaml_path, e)
        return None

    # metadata holds name/description/labels for the package.
    metadata = config.get("metadata") or {}
    labels = metadata.get("labels") or {}
    # Prefer modern connection; fall back to legacy taskServer.
    connection = config.get("connection") or config.get("taskServer") or {}
    deployment = config.get("deployment") or {}
    container = config.get("container") or {}
    # Optional taxonomy labels for EDA fleet UIs.
    track = labels.get("track") or ""
    eda = labels.get("eda") or ""
    # Path-derived category for grouping in the catalog.
    category = _category_from_path(yaml_path)

    return {
        "name": metadata.get("name", yaml_path.parent.name),
        "description": metadata.get("description", ""),
        "capabilities": _capability_ids(config),
        "default_port": int(connection.get("port", DEFAULT_AGENT_BASE_PORT)),
        # Store path relative to repo root for portable registration requests.
        "config_path": str(yaml_path.relative_to(REPO_ROOT)),
        "container_image": deployment.get("image") or container.get("image", ""),
        "category": category,
        "track": track,
        "eda": eda,
    }


# =============================================================================
# Agent package scanning (gateway GET /api/agent-templates)
# =============================================================================

def scan_agent_templates() -> List[Dict[str, Any]]:
    """
    Discover installable agent type templates from the repository tree.

    Purpose:
        Power ``GET /api/agent-templates`` and helpers that need the full catalog.

    Args:
        None (uses ``AGENT_PACKAGE_DIRS`` from config).

    Returns:
        Deduplicated list of agent template dicts (first name wins, case-insensitive).

    Side effects:
        Walks the filesystem with ``rglob("config.yaml")`` and reads each file.

    Failure behavior:
        Skips missing roots, underscored/__pycache__ paths, and unparsable YAML.
        Never raises for individual file failures.
    """
    templates: list[dict[str, Any]] = []
    # Track lowercased names to avoid duplicate catalog entries.
    seen_names: set[str] = set()

    for root in AGENT_PACKAGE_DIRS:
        # Skip configured roots that are not present in this checkout.
        if not root.is_dir():
            continue
        # Stable ordering for deterministic API responses.
        for config_path in sorted(root.rglob("config.yaml")):
            # Ignore private/cache directories in the walk.
            if any(part.startswith("_") or part == "__pycache__" for part in config_path.parts):
                continue
            parsed = _parse_agent_config_yaml(config_path)
            if not parsed:
                continue
            name = parsed["name"].lower()
            # Keep the first occurrence of each agent type name.
            if name in seen_names:
                continue
            seen_names.add(name)
            templates.append(parsed)

    return templates


def find_yaml_for_agent(agent: Dict) -> Optional[str]:
    """
    Resolve the filesystem path of ``config.yaml`` for a registered agent.

    Purpose:
        Support YAML detail and refresh endpoints that need the source file
        matching ``agent_type``.

    Args:
        agent: Agent dict containing ``agent_type``.

    Returns:
        Absolute path string if a matching agent template file exists, else None.

    Side effects:
        Calls ``scan_agent_templates()`` (full catalog scan).

    Failure behavior:
        Returns None when type missing or file absent; does not raise.
    """
    # Normalize type for case-insensitive match against agent template names.
    agent_type = (agent.get("agent_type") or "").lower()
    if not agent_type:
        return None

    for emb in scan_agent_templates():
        if emb["name"].lower() == agent_type:
            # Rehydrate absolute path from repo-relative config_path.
            path = REPO_ROOT / emb["config_path"]
            if path.is_file():
                return str(path)
    return None


# =============================================================================
# Planner Type Scanning (LLM Prompts)
# =============================================================================

def load_planner_summary(planner_dir: Path) -> Dict[str, Any]:
    """
    Load ``summary.yaml`` metadata from a planner or allocator method directory.

    Args:
        planner_dir: Path to a method package directory.

    Returns:
        Parsed mapping, or ``{}`` if ``summary.yaml`` is missing.

    Side effects:
        Reads ``summary.yaml`` when present.

    Failure behavior:
        Propagates YAML parse errors from ``safe_load`` if the file exists but
        is invalid (callers typically assume well-formed summaries).
    """
    summary_file = planner_dir / "summary.yaml"
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}


def _scan_method_types(base_dir: Path, method_category: str) -> List[Dict[str, Any]]:
    """
    Scan planner or allocator type directories into API metadata rows.

    Args:
        base_dir: Root containing one subdirectory per method.
        method_category: ``\"planner\"`` or ``\"allocator\"`` (affects prompt blurbs).

    Returns:
        List of method dicts including id/name/description/prompts metadata.
        Directories without ``summary.yaml`` are omitted.

    Side effects:
        Directory listing and optional summary/prompt existence checks (no
        prompt file contents read here).

    Failure behavior:
        Missing ``base_dir`` → empty list. Invalid summaries may raise from
        ``load_planner_summary``.
    """
    methods = []

    # Nothing to scan if the types root is absent in this environment.
    if not base_dir.exists():
        return methods

    for item in base_dir.iterdir():
        # Skip __pycache__ and non-directories
        if not item.is_dir() or item.name.startswith('__'):
            continue

        summary = load_planner_summary(item)

        # Only include if summary.yaml exists
        if not summary:
            continue

        # Check for prompt files
        prompts = []
        if method_category == "planner":
            system_file = item / "system.prompt"
            user_file = item / "user.prompt"
            if system_file.exists():
                prompts.append({"type": "system", "description": "System prompt defining planning role"})
            if user_file.exists():
                prompts.append({"type": "user", "description": "Template with goals and agent context"})
        else:  # allocator
            # Allocators may have different prompt structures
            system_file = item / "system.prompt"
            user_file = item / "user.prompt"
            if system_file.exists():
                prompts.append({"type": "system", "description": "System prompt defining allocation role"})
            if user_file.exists():
                prompts.append({"type": "user", "description": "Template with agent/task context and allocation instructions"})

        methods.append({
            "category": method_category,
            "type": item.name,
            "id": summary.get("id"),
            "name": summary.get("name", item.name),
            "description": summary.get("description", "").strip(),
            "method_type": summary.get("method_type", "unknown"),
            "output_format": summary.get("output_format", "").strip(),
            "example_output": summary.get("example_output", "").strip(),
            "example_behavior": summary.get("example_behavior", "").strip(),
            # Prefer explicit prompts list from summary when authors provide it.
            "prompts": summary.get("prompts", prompts),  # Use summary prompts or detected ones
        })

    return methods


def scan_planner_types() -> List[Dict[str, Any]]:
    """
    Scan the planner types directory for method metadata.

    Args:
        None.

    Returns:
        List of planner method dicts from ``_scan_method_types``.

    Side effects:
        Filesystem scan under ``PLANNER_TYPES_DIR``.

    Failure behavior:
        Same as ``_scan_method_types``.
    """
    return _scan_method_types(PLANNER_TYPES_DIR, "planner")


def scan_allocator_types() -> List[Dict[str, Any]]:
    """
    Scan the allocator types directory for method metadata.

    Args:
        None.

    Returns:
        List of allocator method dicts from ``_scan_method_types``.

    Side effects:
        Filesystem scan under ``ALLOCATOR_TYPES_DIR``.

    Failure behavior:
        Same as ``_scan_method_types``.
    """
    return _scan_method_types(ALLOCATOR_TYPES_DIR, "allocator")


def scan_all_method_types() -> List[Dict[str, Any]]:
    """
    Combine planner and allocator method metadata into one list.

    Purpose:
        Power ``GET /api/methods`` and method detail lookups by id.

    Args:
        None.

    Returns:
        Concatenation of planner then allocator scan results.

    Side effects:
        Two filesystem scans.

    Failure behavior:
        Propagates errors from the underlying scanners.
    """
    methods = []
    methods.extend(scan_planner_types())
    methods.extend(scan_allocator_types())
    return methods


def _build_strategy_lookup(base_dir: Path) -> Dict[str, int]:
    """
    Map method directory names to their ``summary.yaml`` integer ids.

    Args:
        base_dir: Planner or allocator types root.

    Returns:
        Dict ``{dirname: id}`` for directories that declare an id.

    Side effects:
        Reads each subdirectory's summary.yaml.

    Failure behavior:
        Missing base_dir → empty dict. Skips dirs without id in summary.
    """
    lookup = {}
    if not base_dir.exists():
        return lookup
    for item in base_dir.iterdir():
        if not item.is_dir() or item.name.startswith('__'):
            continue
        summary = load_planner_summary(item)
        if summary and "id" in summary:
            lookup[item.name] = summary["id"]
    return lookup


def get_allocation_strategy_id(name: str) -> Optional[int]:
    """
    Resolve an allocator directory name (e.g. ``llm``) to its enum/id integer.

    Purpose:
        Convert UI strategy strings on ``POST /api/plans/{id}/allocate`` into
        the integer expected by AllocatePlan RPC.

    Args:
        name: Allocator package directory name.

    Returns:
        Integer id or ``None`` if unknown.

    Side effects:
        Rebuilds the lookup via filesystem scan each call.

    Failure behavior:
        Returns None for unknown names (router maps to HTTP 400).
    """
    return _build_strategy_lookup(ALLOCATOR_TYPES_DIR).get(name)


def get_planning_strategy_id(name: str) -> Optional[int]:
    """
    Resolve a planner directory name (e.g. ``big_dag``) to its summary id.

    Args:
        name: Planner package directory name.

    Returns:
        Integer id or ``None`` if unknown.

    Side effects:
        Filesystem scan of planner types.

    Failure behavior:
        Returns None for unknown names.
    """
    return _build_strategy_lookup(PLANNER_TYPES_DIR).get(name)
