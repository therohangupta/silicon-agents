"""
Goal management REST endpoints (``/api/goals``).

Goals are high-level natural-language objectives. Plans reference goal ids when
the fleet planner/allocator decomposes work into tasks. This router is a thin
CRUD facade over ``GRPCBridge`` goal methods.

HTTP behavior summary:

- ``GET ""`` → 200 list
- ``GET /{goal_id}`` → 200 or **404** if missing
- ``POST ""`` → 200 created goal or **400** if bridge returns None;
  **422** on invalid body
- ``DELETE /{goal_id}`` → 200 success envelope or **400** if delete failed
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends

# Injected fleet bridge for all goal RPCs.
from ..dependencies import get_bridge, GRPCBridge
from ..models.requests import GoalCreate
from ..models.responses import GoalResponse

# Mounted under /api via api_router → full path /api/goals.
router = APIRouter(prefix="/goals")


@router.get("", response_model=List[GoalResponse])
async def list_goals(bridge: GRPCBridge = Depends(get_bridge)):
    """
    List all goals known to the fleet manager.

    Args:
        bridge: Injected ``GRPCBridge`` singleton.

    Returns:
        List of goal dicts coerced through ``GoalResponse``.

    Side effects:
        ListGoals gRPC call.

    Failure behavior:
        Propagates bridge/client errors as 500 unless caught upstream.
        HTTP status **200** on success.
    """
    # Delegate entirely to the bridge adapter.
    return bridge.list_goals()


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Fetch a single goal by numeric id.

    Args:
        goal_id: Path parameter goal primary key.
        bridge: Injected gRPC bridge.

    Returns:
        Goal payload.

    Side effects:
        GetGoal gRPC call.

    Failure behavior:
        **404** when bridge returns None; **200** when found.
    """
    # Soft-fail from bridge becomes an HTTP not-found for the client.
    goal = bridge.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return goal


@router.post("", response_model=GoalResponse)
async def create_goal(
    goal: GoalCreate,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Create a new goal from a natural-language description.

    Args:
        goal: Validated request body with ``description``.
        bridge: Injected gRPC bridge.

    Returns:
        Newly created goal dict.

    Side effects:
        CreateGoal gRPC mutation on the fleet server.

    Failure behavior:
        **422** if body invalid; **400** if bridge returns None; **200** on success.
    """
    # Pass only the description field into the RPC wrapper.
    result = bridge.create_goal(goal.description)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create goal")
    return result


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Delete a goal by id.

    Args:
        goal_id: Goal to remove.
        bridge: Injected gRPC bridge.

    Returns:
        ``{"success": True, "message": ...}`` confirmation.

    Side effects:
        DeleteGoal gRPC mutation.

    Failure behavior:
        **400** when bridge reports unsuccessful delete; **200** on success.
    """
    result = bridge.delete_goal(goal_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Deletion failed")
        )
    return {"success": True, "message": f"Goal {goal_id} deleted"}
