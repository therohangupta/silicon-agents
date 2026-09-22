"""
Method details viewing endpoints (``/api/methods``).

Provides read-only access to planner and allocator method metadata discovered
from ``PLANNER_TYPES_DIR`` and ``ALLOCATOR_TYPES_DIR``. Detail responses include
``summary.yaml`` fields plus on-disk ``system.prompt`` / ``user.prompt`` contents
and template variables extracted from ``{word}`` placeholders in the user prompt.

HTTP behavior:

- ``GET ""`` / ``/planners`` / ``/allocators`` → **200** lists
- ``GET /{method_id}`` → **200** detail, **404** if id (and optional category)
  not found or directory/summary missing
"""

import re
from typing import List
from fastapi import APIRouter, HTTPException

from ..config import PLANNER_TYPES_DIR, ALLOCATOR_TYPES_DIR
from ..services import scan_all_method_types, scan_planner_types, scan_allocator_types, load_planner_summary

# Mounted at /api/methods via api_router.
router = APIRouter(prefix="/methods")


@router.get("")
async def list_methods() -> List[dict]:
    """
    List all planning and allocation methods with summary metadata.

    Args:
        None.

    Returns:
        Combined list from ``scan_all_method_types``.

    Side effects:
        Filesystem scans of planner and allocator directories.

    Failure behavior:
        **200** on success; scan errors may become **500**.
    """
    return scan_all_method_types()


@router.get("/planners")
async def list_planners() -> List[dict]:
    """
    List only planner methods.

    Args:
        None.

    Returns:
        Planner metadata list.

    Side effects:
        Filesystem scan of ``PLANNER_TYPES_DIR``.

    Failure behavior:
        **200** on success.
    """
    return scan_planner_types()


@router.get("/allocators")
async def list_allocators() -> List[dict]:
    """
    List only allocator methods.

    Args:
        None.

    Returns:
        Allocator metadata list.

    Side effects:
        Filesystem scan of ``ALLOCATOR_TYPES_DIR``.

    Failure behavior:
        **200** on success.
    """
    return scan_allocator_types()


@router.get("/{method_id}")
async def get_method(method_id: int, category: str = None) -> dict:
    """
    Get details for a method identified by ``summary.yaml`` integer id.

    Purpose:
        Return metadata, prompt file contents, and extracted template variables
        for the methods UI.

    Args:
        method_id: Method id from summary.yaml (path param).
        category: Optional query filter (``planner`` or ``allocator``) when ids
            could collide across categories.

    Returns:
        Detail dict with prompts, variables, and summary fields.

    Side effects:
        Scans all methods; reads summary and prompt files from disk.

    Failure behavior:
        **404** if method id not found, directory missing, or summary missing;
        **200** on success.
    """
    # Scan all methods to find the one with matching ID.
    all_methods = scan_all_method_types()
    method_info = None

    for method in all_methods:
        if method.get("id") == method_id:
            # If category is specified, ensure it matches.
            if category and method.get("category") != category:
                continue
            method_info = method
            break

    if not method_info:
        raise HTTPException(
            status_code=404,
            detail=f"Method with ID {method_id} not found"
        )

    method_type = method_info["type"]
    category = method_info["category"]

    # Find the method directory under the correct types root.
    base_dir = PLANNER_TYPES_DIR if category == "planner" else ALLOCATOR_TYPES_DIR
    method_dir = base_dir / method_type

    if not method_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Method directory not found: {method_type}"
        )

    summary = load_planner_summary(method_dir)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No summary.yaml found for: {method_type}"
        )

    # Read prompt files if they exist.
    system_content = ""
    user_content = ""

    system_file = method_dir / "system.prompt"
    user_file = method_dir / "user.prompt"

    if system_file.exists():
        system_content = system_file.read_text()
    if user_file.exists():
        user_content = user_file.read_text()

    # Extract template variables from user prompt (e.g., {goal_id}, {agent_context}).
    variables = list(set(re.findall(r'\{(\w+)\}', user_content)))

    return {
        "category": category,
        "type": method_type,
        "id": method_id,
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
