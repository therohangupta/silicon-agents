"""
Agent embodiment (type template) catalog and port helper endpoints.

``GET /api/embodiments`` lists agent packages discovered by
``scan_embodiments()`` (each ``agents/**/config.yaml``). Clients pick a
template, then ``POST /api/agents/register`` with host/port to create an
instance.

Also defines ``ports_router`` (prefix ``/ports``) which ``app.py`` mounts at
``/api/ports`` for backwards-compatible suggest/used port APIs. Duplicate
handlers under ``/embodiments/ports/*`` exist but are ``include_in_schema=False``.

HTTP behavior:

- List/get embodiments → **200** / **404** for unknown name
- Port suggest/used → **200** JSON (requires initialized gRPC bridge for used ports)
"""

from typing import List
from fastapi import APIRouter, HTTPException

from ..services import scan_embodiments, get_used_ports, suggest_next_port
from ..models.responses import EmbodimentResponse
from ..config import DEFAULT_AGENT_BASE_PORT

# Primary catalog router under /api/embodiments.
router = APIRouter(prefix="/embodiments")


@router.get("", response_model=List[EmbodimentResponse])
async def list_embodiments():
    """
    List all available agent embodiments from the repo YAML scan.

    Args:
        None.

    Returns:
        List of embodiment dicts for the dashboard catalog.

    Side effects:
        Filesystem scan via ``scan_embodiments``.

    Failure behavior:
        **200** with possibly empty list; individual YAML errors skipped in scanner.
    """
    return scan_embodiments()


@router.get("/{name}")
async def get_embodiment(name: str):
    """
    Return one embodiment by case-insensitive name match.

    Args:
        name: Embodiment ``metadata.name`` (or path fallback name).

    Returns:
        Matching embodiment dict.

    Side effects:
        Full catalog scan then linear search.

    Failure behavior:
        **404** if no name matches; **200** when found.
    """
    embodiments = scan_embodiments()
    for emb in embodiments:
        if emb["name"].lower() == name.lower():
            return emb
    raise HTTPException(status_code=404, detail=f"Embodiment {name} not found")


# =============================================================================
# Port Management (for local agent instances)
# =============================================================================

@router.get("/ports/suggest", include_in_schema=False)
async def suggest_port_endpoint(base_port: int = DEFAULT_AGENT_BASE_PORT):
    """
    Suggest the next free localhost-oriented port (hidden from OpenAPI).

    Args:
        base_port: Search start (query param, default config base).

    Returns:
        ``{"suggested_port": int}``.

    Side effects:
        Lists agents via bridge to compute used ports.

    Failure behavior:
        May **500** if bridge uninitialized; **200** on success.
    """
    return {"suggested_port": suggest_next_port(base_port)}


@router.get("/ports/used", include_in_schema=False)
async def get_used_ports_endpoint():
    """
    List ports currently claimed by registered agents (hidden from OpenAPI).

    Args:
        None.

    Returns:
        ``{"used_ports": [...]}`` (list form of the set).

    Side effects:
        gRPC list_agents via ``get_used_ports``.

    Failure behavior:
        May **500** if bridge missing; **200** on success.
    """
    return {"used_ports": list(get_used_ports())}


# Also expose at /api/ports/* for backwards compatibility
from fastapi import APIRouter as _APIRouter
# Separate router object mounted by app.py with prefix="/api".
ports_router = _APIRouter(prefix="/ports")


@ports_router.get("/suggest")
async def suggest_port_compat(base_port: int = DEFAULT_AGENT_BASE_PORT):
    """
    Compatibility alias for next available port suggestion.

    Args:
        base_port: Inclusive search start.

    Returns:
        ``{"suggested_port": int}``.

    Side effects:
        Same as ``suggest_next_port``.

    Failure behavior:
        Same as suggest_port_endpoint (**200** / possible **500**).
    """
    return {"suggested_port": suggest_next_port(base_port)}


@ports_router.get("/used")
async def get_used_ports_compat():
    """
    Compatibility alias for listing used agent ports.

    Args:
        None.

    Returns:
        ``{"used_ports": [...]}``.

    Side effects:
        Same as ``get_used_ports``.

    Failure behavior:
        **200** on success; **500** if bridge not ready.
    """
    return {"used_ports": list(get_used_ports())}
