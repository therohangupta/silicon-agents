"""
Task management REST endpoints (``/api/tasks``).

Tasks are the atomic executable units inside plans. This router supports listing
with optional filters, get/create/patch/delete, all delegated to ``GRPCBridge``.

HTTP behavior summary:

- ``GET ""`` → **200** filtered list
- ``GET /{task_id}`` → **200** or **404**
- ``POST ""`` → **200** or **400** if create failed (**422** on bad body)
- ``PATCH /{task_id}`` → **200** or **400**
- ``DELETE /{task_id}`` → **200** ``TaskDeleteResponse`` or **400**
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..dependencies import get_bridge, GRPCBridge
from ..models.requests import TaskCreate, TaskUpdate
from ..models.responses import TaskResponse, TaskDeleteResponse

# Full paths are /api/tasks after api_router prefixing.
router = APIRouter(prefix="/tasks")


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    plan_id: Optional[int] = None,
    goal_id: Optional[int] = None,
    agent_id: Optional[str] = None,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    List tasks with optional plan/goal/agent query filters.

    Args:
        plan_id: When set, restrict to this plan.
        goal_id: When set, restrict to this goal.
        agent_id: When set, restrict to this assigned agent.
        bridge: Injected gRPC bridge.

    Returns:
        List of task dicts.

    Side effects:
        ListTasks gRPC call with list-wrapped filter ids.

    Failure behavior:
        **200** on success; client errors may surface as 500.
    """
    # Bridge expects list filters; wrap single query params when provided.
    return bridge.list_tasks(
        plan_ids=[plan_id] if plan_id else None,
        goal_ids=[goal_id] if goal_id else None,
        agent_ids=[agent_id] if agent_id else None
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Fetch one task by id.

    Args:
        task_id: Task primary key.
        bridge: Injected gRPC bridge.

    Returns:
        Task payload.

    Side effects:
        GetTask RPC.

    Failure behavior:
        **404** if missing; **200** if found.
    """
    task = bridge.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Create a standalone task (testing or incremental plan editing).

    Args:
        task: Validated create body.
        bridge: Injected gRPC bridge.

    Returns:
        Created task dict.

    Side effects:
        CreateTask gRPC mutation.

    Failure behavior:
        **422** invalid body; **400** if bridge returns None; **200** on success.
    """
    result = bridge.create_task(
        description=task.description,
        goal_id=task.goal_id,
        plan_id=task.plan_id,
        agent_id=task.agent_id,
        agent_type=task.agent_type,
        dependency_task_ids=task.dependency_task_ids
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create task")
    return result


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    bridge: GRPCBridge = Depends(get_bridge),
):
    """
    Partially update description, goal, deps, and/or agent assignment.

    Args:
        task_id: Task to patch.
        task: Fields to change (see ``TaskUpdate`` agent_id semantics).
        bridge: Injected gRPC bridge.

    Returns:
        Updated task dict.

    Side effects:
        UpdateTask gRPC mutation.

    Failure behavior:
        **400** if bridge returns None; **422** on bad body; **200** on success.
    """
    updated = bridge.update_task(
        task_id=task_id,
        description=task.description,
        goal_id=task.goal_id,
        agent_id=task.agent_id,
        dependency_task_ids=task.dependency_task_ids,
        update_dependency_task_ids=task.update_dependency_task_ids,
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update task")
    return updated


@router.delete("/{task_id}", response_model=TaskDeleteResponse)
async def delete_task(
    task_id: int,
    bridge: GRPCBridge = Depends(get_bridge),
):
    """
    Delete a task; fleet server unlinks dependents' dependency edges.

    Args:
        task_id: Task to delete.
        bridge: Injected gRPC bridge.

    Returns:
        ``TaskDeleteResponse`` including updated dependent task ids.

    Side effects:
        DeleteTask gRPC mutation.

    Failure behavior:
        **400** when success is false; **200** with delete envelope on success.
    """
    result = bridge.delete_task(task_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Failed to delete task")
    return result
