"""
Agent type template catalog and port helper endpoints.

``GET /api/agent-templates`` lists agent packages discovered by
``scan_agent_templates()`` (each ``agents/**/config.yaml``). Clients pick a
template, then ``POST /api/agents/register`` with host/port to create an
instance.

``ports_router`` (prefix ``/ports``) is mounted at ``/api/ports`` in ``app.py``.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from ..config import DEFAULT_AGENT_BASE_PORT
from ..models.responses import AgentTemplateResponse
from ..services import get_used_ports, scan_agent_templates, suggest_next_port

router = APIRouter(prefix="/agent-templates")


@router.get("", response_model=List[AgentTemplateResponse])
async def list_agent_templates():
    """List agent type templates from the repo YAML scan."""
    return scan_agent_templates()


@router.get("/{name}")
async def get_agent_template(name: str):
    """Return one template by case-insensitive name match."""
    for entry in scan_agent_templates():
        if entry["name"].lower() == name.lower():
            return entry
    raise HTTPException(status_code=404, detail=f"Agent template {name} not found")


ports_router = APIRouter(prefix="/ports")


@ports_router.get("/suggest")
async def suggest_port(base_port: int = DEFAULT_AGENT_BASE_PORT):
    """Suggest the next free localhost-oriented port."""
    return {"suggested_port": suggest_next_port(base_port)}


@ports_router.get("/used")
async def get_used_ports_endpoint():
    """List ports currently claimed by registered agents."""
    return {"used_ports": list(get_used_ports())}
