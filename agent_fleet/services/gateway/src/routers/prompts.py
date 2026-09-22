"""
Legacy / alternate method prompt viewer keyed by directory name.

This module historically exposed ``/methods`` routes that look up planners and
allocators by filesystem directory name (e.g. ``monolithic``, ``lp``) rather
than by ``summary.yaml`` id. The primary, currently mounted implementation is
``methods.py`` (id-based). This file is retained for compatibility and as a
name-based lookup reference; it is **not** included on ``api_router`` today.

Behavior mirrors reading ``summary.yaml`` plus ``system.prompt`` / ``user.prompt``
and extracting ``{variable}`` placeholders from the user prompt.

HTTP (if mounted): list **200**; detail **200** / **404** when type or summary missing.
"""

import re
from typing import List
from fastapi import APIRouter, HTTPException

from ..config import PLANNER_TYPES_DIR, ALLOCATOR_TYPES_DIR
from ..services import scan_all_method_types, load_planner_summary

# Same prefix as methods.py; only one should be mounted at a time.
router = APIRouter(prefix="/methods")


@router.get("")
async def list_methods() -> List[dict]:
    """
    List all planning and allocation methods with metadata.

    Args:
        None.

    Returns:
        Combined method metadata from disk scans.

    Side effects:
        Filesystem scans.

    Failure behavior:
        **200** on success when this router is mounted.
    """
    return scan_all_method_types()


@router.get("/{method_type}")
async def get_method(method_type: str) -> dict:
    """
    Get method details by directory name under planners or allocators.

    Purpose:
        Resolve ``method_type`` first under ``PLANNER_TYPES_DIR``, then
        ``ALLOCATOR_TYPES_DIR``, and return prompts plus summary fields.

    Args:
        method_type: Method directory name (e.g. ``monolithic``, ``lp``).

    Returns:
        Detail dict including category inferred from which root matched.

    Side effects:
        Reads summary and prompt files from disk.

    Failure behavior:
        **404** if directory or summary.yaml missing; **200** on success.
    """
    # First try planners directory
    method_dir = PLANNER_TYPES_DIR / method_type
    if not method_dir.exists():
        # Try allocators directory
        method_dir = ALLOCATOR_TYPES_DIR / method_type
        if not method_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Method type not found: {method_type}"
            )

    summary = load_planner_summary(method_dir)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No summary.yaml found for: {method_type}"
        )

    # Read prompt files if they exist
    system_content = ""
    user_content = ""

    system_file = method_dir / "system.prompt"
    user_file = method_dir / "user.prompt"

    if system_file.exists():
        system_content = system_file.read_text()
    if user_file.exists():
        user_content = user_file.read_text()

    # Extract template variables from user prompt (e.g., {goal_id}, {agent_context})
    variables = list(set(re.findall(r'\{(\w+)\}', user_content)))

    return {
        "category": "planner" if method_dir.parent == PLANNER_TYPES_DIR else "allocator",
        "type": method_type,
        "name": summary.get("name", method_type),
        "description": summary.get("description", "").strip(),
        "method_type": summary.get("method_type", "unknown"),
        "output_format": summary.get("output_format", "").strip(),
        "example_output": summary.get("example_output", "").strip(),
        "example_behavior": summary.get("example_behavior", "").strip(),
        "prompts": summary.get("prompts", []),
        "system_prompt": system_content,
        "user_prompt": user_content,
        "variables": sorted(variables),
    }
