"""
Strategy options endpoint (``/api/strategies``).

Returns available planning and allocation strategies dynamically from each
method package's ``summary.yaml`` (single source of truth), so the dashboard
dropdowns stay aligned with fleet enum ids without hardcoding labels in the UI.

The synthetic allocation option ``none`` is appended using
``fleet_manager_pb2.AllocationStrategy.NONE`` for plans that defer assignment.

HTTP: ``GET ""`` → **200** ``{"planning": [...], "allocation": [...]}``.
"""

from fastapi import APIRouter
from packages.proto import fleet_manager_pb2

from ..services.yaml_scanner import scan_planner_types, scan_allocator_types

# Full path /api/strategies after api_router mount.
router = APIRouter(prefix="/strategies")


@router.get("")
async def get_strategies():
    """
    Build planning and allocation strategy option lists for the UI.

    Purpose:
        Expose ``value``/``id``/``label``/``description`` rows sorted by id,
        excluding the special ``replanner`` planner type from the planning list.

    Args:
        None.

    Returns:
        Dict with ``planning`` and ``allocation`` arrays; allocation always
        includes a trailing ``none`` option.

    Side effects:
        Filesystem scans of planner/allocator type directories.

    Failure behavior:
        **200** on success; scan/parse errors may surface as **500**.
    """
    # Discover method packages from disk.
    planners = scan_planner_types()
    allocators = scan_allocator_types()

    # Map planners into UI option rows; skip internal replanner helper type.
    planning = [
        {
            "value": p["type"],
            "id": p["id"],
            "label": p["name"],
            "description": p["description"],
        }
        for p in sorted(planners, key=lambda x: x.get("id", 0))
        if p["type"] != "replanner"
    ]

    # Map allocators into UI option rows sorted by summary id.
    allocation = [
        {
            "value": a["type"],
            "id": a["id"],
            "label": a["name"],
            "description": a["description"],
        }
        for a in sorted(allocators, key=lambda x: x.get("id", 0))
    ]

    # Always offer explicit "skip allocation" using the protobuf NONE enum.
    allocation.append({
        "value": "none",
        "id": int(fleet_manager_pb2.AllocationStrategy.NONE),
        "label": "None (Unallocated)",
        "description": "Skip allocation — assign agents later",
    })

    return {"planning": planning, "allocation": allocation}
