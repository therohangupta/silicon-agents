"""
Plan management REST endpoints (``/api/plans``).

Supports automated plan creation, manual DAG authoring (temp_id remapping),
allocation, execution start, copy, and name/description updates. Automated
create/allocate/start go through ``GRPCBridge`` gRPC; copy/update also use
``bridge.registry`` for direct database plan/task operations.

HTTP status summary:

- List/get → **200** / **404**
- Create/manual/allocate/start → **400** on validation or RPC failure; **422**
  on bad bodies; **200** on success
- Copy/update → **404** missing plan; **400** missing strategies on copy;
  **500** on registry failures; **200** on success
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..dependencies import get_bridge, GRPCBridge
from ..models.requests import PlanCreate, ManualPlanCreate
from ..models.responses import PlanResponse
from ..services.yaml_scanner import get_allocation_strategy_id, scan_allocator_types

logger = logging.getLogger(__name__)

# Full paths under /api/plans.
router = APIRouter(prefix="/plans")


# =============================================================================
# Request Models (local to this router)
# =============================================================================

class AllocatePlanRequest(BaseModel):
    """
    Body for allocating agents onto an existing plan's tasks.

    Purpose:
        Carry the allocator strategy directory name (e.g. ``llm``) resolved via
        ``get_allocation_strategy_id`` before AllocatePlan RPC.

    Fields:
        allocation_strategy: Strategy name string (not the integer id).

    Side effects:
        None at validation.

    Failure behavior:
        Missing field → **422**; unknown name → **400** in the handler.
    """
    allocation_strategy: str  # lp, llm, cost_based


class PlanCopyRequest(BaseModel):
    """
    Body requiring a new name and description when copying a plan.

    Purpose:
        Force operators to label the copy distinctly before re-execution.

    Fields:
        name / description: Required non-default strings for the new plan.

    Side effects:
        None at validation.

    Failure behavior:
        Missing fields → **422**.
    """
    name: str = Field(..., description="New name for the copied plan")
    description: str = Field(..., description="New description for the copied plan")


class PlanUpdateRequest(BaseModel):
    """
    Body for updating only plan display fields.

    Purpose:
        Change name/description without altering strategies or tasks.

    Fields:
        name / description: Replacement strings.

    Side effects:
        None at validation.

    Failure behavior:
        Missing fields → **422**.
    """
    name: str = Field(..., description="Updated name for the plan")
    description: str = Field(..., description="Updated description for the plan")


# =============================================================================
# Plan CRUD
# =============================================================================

@router.get("", response_model=List[PlanResponse])
async def list_plans(bridge: GRPCBridge = Depends(get_bridge)):
    """
    List all plans with DB enrichment merged by the bridge.

    Args:
        bridge: Injected gRPC bridge.

    Returns:
        List of plan dicts.

    Side effects:
        ListPlans RPC + per-plan DB reads.

    Failure behavior:
        **200** on success.
    """
    return await bridge.list_plans()


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Get one plan including nested tasks and enrichment fields.

    Args:
        plan_id: Plan primary key.
        bridge: Injected gRPC bridge.

    Returns:
        Plan payload.

    Side effects:
        GetPlan RPC + DB enrichment.

    Failure behavior:
        **404** if missing; **200** if found.
    """
    plan = await bridge.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return plan


@router.post("", response_model=PlanResponse)
async def create_plan(
    plan: PlanCreate,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Create a plan using automated planning and allocation strategies.

    Purpose:
        Forward enum ints, goal ids, and labels to CreatePlan on the fleet server.

    Args:
        plan: Validated create body.
        bridge: Injected gRPC bridge.

    Returns:
        Created plan dict including tasks when returned by the bridge.

    Side effects:
        CreatePlan RPC (may run LLM planners server-side).

    Failure behavior:
        **422** bad body; **400** if bridge returns None; unexpected exceptions
        are logged and re-raised (typically **500**).
    """
    logger.debug("Creating plan with data: %s", plan.dict())
    try:
        result = bridge.create_plan(
            planning_strategy=plan.planning_strategy,
            allocation_strategy=plan.allocation_strategy,
            goal_ids=plan.goal_ids,
            name=plan.name,
            description=plan.description
        )
        logger.debug("Bridge result: %s", result)
        if not result:
            logger.debug("Bridge returned None")
            raise HTTPException(status_code=400, detail="Failed to create plan")
        logger.debug("Returning plan: %s", result)
        return result
    except Exception as e:
        logger.error("Exception in create_plan: %s", e, exc_info=True)
        raise


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Delete a plan and its associated server-side state.

    Args:
        plan_id: Plan to delete.
        bridge: Injected gRPC bridge.

    Returns:
        Success confirmation message.

    Side effects:
        DeletePlan RPC.

    Failure behavior:
        **400** if bridge reports failure; **200** on success.
    """
    result = bridge.delete_plan(plan_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Deletion failed")
        )
    return {"success": True, "message": f"Plan {plan_id} deleted"}


# =============================================================================
# Manual Plan Creation
# =============================================================================

@router.post("/manual", response_model=PlanResponse)
async def create_manual_plan(
    plan_data: ManualPlanCreate,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Create a plan by explicitly defining tasks and temp_id dependencies.

    Purpose:
        Bypass automated planners: validate the DAG, create a MANUAL plan shell,
        then CreateTask in topological order while remapping temp_ids to real ids.
        Infers ``agent_type`` from GetAgent when ``agent_id`` is set without type.

    Args:
        plan_data: Manual plan body with tasks and labels.
        bridge: Injected gRPC bridge.

    Returns:
        Full plan from ``get_plan`` after tasks are created.

    Side effects:
        Multiple gRPC mutations (plan shell + tasks).

    Failure behavior:
        **400** for empty tasks, missing goal_ids, unknown deps, cycles, missing
        agents when type inference required, or shell creation failure;
        **422** on schema validation; **200** on success.
    """
    logger.debug("Creating manual plan with data: %s", plan_data.dict())
    if not plan_data.tasks:
        raise HTTPException(status_code=400, detail="At least one task is required")
    
    # Validate all tasks have goal_id
    tasks_without_goals = [t.temp_id for t in plan_data.tasks if not t.goal_id]
    if tasks_without_goals:
        raise HTTPException(
            status_code=400, 
            detail=f"All tasks must have a goal_id. Missing: {', '.join(tasks_without_goals)}"
        )
    
    # Validate dependencies reference valid temp_ids
    temp_ids = {t.temp_id for t in plan_data.tasks}
    for task in plan_data.tasks:
        for dep in task.depends_on:
            if dep not in temp_ids:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Task '{task.temp_id}' depends on unknown task '{dep}'"
                )
    
    # Check for circular dependencies
    if _has_cycle(plan_data.tasks):
        raise HTTPException(
            status_code=400, 
            detail="Circular dependency detected in tasks"
        )
    
    # Derive goal_ids from tasks
    derived_goal_ids = list(set(t.goal_id for t in plan_data.tasks if t.goal_id))
    
    # Create the plan shell (manual strategy)
    result = bridge.create_manual_plan(goal_ids=derived_goal_ids, name=plan_data.name, description=plan_data.description)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create plan")
    
    plan_id = result["plan_id"]
    
    # Create tasks in dependency order
    sorted_tasks = _topo_sort(plan_data.tasks)
    temp_to_real: dict[str, int] = {}
    agent_type_cache: dict[str, str] = {}
    
    for task_def in sorted_tasks:
        # Convert temp dependency IDs to real task IDs
        real_deps = [temp_to_real[dep] for dep in task_def.depends_on]

        # If a agent is assigned but agent_type is missing, infer it from agent_id via GetAgent
        inferred_agent_type = task_def.agent_type
        if task_def.agent_id and not inferred_agent_type:
            if task_def.agent_id in agent_type_cache:
                inferred_agent_type = agent_type_cache[task_def.agent_id]
            else:
                agent = bridge.get_agent(task_def.agent_id)
                if not agent:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent '{task_def.agent_id}' not found (required to infer agent_type)"
                    )
                inferred_agent_type = agent.get("agent_type")
                if inferred_agent_type:
                    agent_type_cache[task_def.agent_id] = inferred_agent_type
        
        task_result = bridge.create_task(
            description=task_def.description,
            goal_id=task_def.goal_id,
            plan_id=plan_id,
            agent_id=task_def.agent_id,
            agent_type=inferred_agent_type,
            dependency_task_ids=real_deps
        )
        
        if task_result:
            temp_to_real[task_def.temp_id] = task_result["task_id"]
    
    # Return the complete plan with tasks
    return await bridge.get_plan(plan_id)


def _has_cycle(tasks) -> bool:
    """
    Detect circular dependencies among manual tasks using DFS coloring.

    Args:
        tasks: Iterable of objects with ``temp_id`` and ``depends_on``.

    Returns:
        True if a cycle exists, else False.

    Side effects:
        None (local sets only).

    Failure behavior:
        Assumes depends_on entries exist in the adjacency built from tasks;
        unknown deps should already be rejected by the caller.
    """
    visited = set()
    rec_stack = set()
    adj = {t.temp_id: t.depends_on for t in tasks}
    
    def dfs(node):
        """
        Depth-first search helper returning True when a back-edge is found.

        Args:
            node: Current temp_id.

        Returns:
            True if a cycle is detected in this recursion stack.

        Side effects:
            Mutates outer ``visited`` and ``rec_stack``.

        Failure behavior:
            None for well-formed graphs.
        """
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False
    
    for t in tasks:
        if t.temp_id not in visited:
            if dfs(t.temp_id):
                return True
    return False


def _topo_sort(tasks) -> list:
    """
    Kahn topological sort so dependencies are created before dependents.

    Args:
        tasks: Manual task definitions with temp_id / depends_on.

    Returns:
        List of task objects in a valid creation order.

    Side effects:
        None.

    Failure behavior:
        If a cycle slipped through, some nodes may be omitted from ``order``;
        callers should run ``_has_cycle`` first.
    """
    in_degree = {t.temp_id: 0 for t in tasks}
    adj = {t.temp_id: [] for t in tasks}
    task_map = {t.temp_id: t for t in tasks}
    
    for t in tasks:
        for dep in t.depends_on:
            # Edge dep → dependent (dep must be created first).
            adj[dep].append(t.temp_id)
            in_degree[t.temp_id] += 1
    
    queue = [tid for tid, deg in in_degree.items() if deg == 0]
    order = []
    
    while queue:
        node = queue.pop(0)
        order.append(task_map[node])
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order


# =============================================================================
# Plan Allocation
# =============================================================================

@router.post("/{plan_id}/allocate")
async def allocate_plan(
    plan_id: int,
    request: AllocatePlanRequest,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Allocate agents to tasks in an existing plan.

    Purpose:
        Resolve the strategy name from allocator ``summary.yaml`` ids, then call
        AllocatePlan on the fleet server.

    Args:
        plan_id: Plan to allocate.
        request: Body with allocation_strategy name.
        bridge: Injected gRPC bridge.

    Returns:
        Updated plan dict from the bridge success envelope.

    Side effects:
        AllocatePlan RPC; filesystem scan for strategy id resolution.

    Failure behavior:
        **400** for unknown strategy or RPC failure; **422** bad body; **200** ok.
    """
    strategy_int = get_allocation_strategy_id(request.allocation_strategy)
    if strategy_int is None:
        available = [m["type"] for m in scan_allocator_types()]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid allocation strategy '{request.allocation_strategy}'. Must be one of: {available}"
        )
    
    result = bridge.allocate_plan(plan_id, strategy_int)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Allocation failed")
        )
    return result.get("plan")


@router.get("/{plan_id}/status")
async def get_plan_allocation_status(
    plan_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Return allocation completeness for a plan.

    Returns include status string, task counts, unallocated ids, and
    ``is_executable`` (true only when fully allocated with tasks).

    Args:
        plan_id: Plan to inspect.
        bridge: Injected gRPC bridge.

    Returns:
        Allocation status dict from the bridge.

    Side effects:
        Loads plan/tasks via bridge.

    Failure behavior:
        **404** when bridge returns an error key; **200** on success.
    """
    result = await bridge.get_plan_allocation_status(plan_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =============================================================================
# Plan Execution
# =============================================================================

@router.post("/{plan_id}/start")
async def start_plan(
    plan_id: int,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Start executing a fully allocated plan.

    Args:
        plan_id: Plan to start.
        bridge: Injected gRPC bridge.

    Returns:
        Success confirmation message.

    Side effects:
        StartPlan RPC; begins task dispatch on the fleet server.

    Failure behavior:
        **400** if the fleet returns an error (e.g. not fully allocated);
        **200** on success.
    """
    result = bridge.start_plan(plan_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return {"success": True, "message": f"Plan {plan_id} started"}


@router.post("/{plan_id}/copy")
async def copy_plan(
    plan_id: int,
    request: PlanCopyRequest,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Deep-copy a plan for re-execution with a new name/description.

    Purpose:
        Clone strategies, goals, prompts/artifacts, and tasks via the registry,
        then reset ``execution_status`` to not_executed (0).

    Args:
        plan_id: Source plan id.
        request: New name and description.
        bridge: Bridge + registry access.

    Returns:
        The newly copied plan from ``get_plan``.

    Side effects:
        Registry create_plan, copy_plan_tasks, update_plan mutations.

    Failure behavior:
        **404** if source missing; **400** if strategies missing; **500** on
        registry failures; **200** on success. HTTPExceptions are re-raised.
    """
    try:
        # Get the original plan with full details
        original_plan = await bridge.get_plan(plan_id)
        if not original_plan:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

        # Validate that we have all required plan configuration
        planning_strategy = original_plan.get("planning_strategy")
        allocation_strategy = original_plan.get("allocation_strategy")
        goal_ids = original_plan.get("goal_ids", [])

        if not planning_strategy:
            raise HTTPException(status_code=400, detail=f"Original plan {plan_id} missing planning_strategy")
        if not allocation_strategy:
            raise HTTPException(status_code=400, detail=f"Original plan {plan_id} missing allocation_strategy")

        # Use the provided name and description
        copy_name = request.name
        copy_description = request.description

        # Create the new plan directly in the database (bypass planner)
        try:
            new_plan_proto = await bridge.registry.create_plan(
                planning_strategy=planning_strategy,
                allocation_strategy=allocation_strategy,
                goal_ids=goal_ids,
                task_ids=[],  # We'll add tasks separately
                planning_prompts=original_plan.get("planning_prompts"),
                allocation_prompts=original_plan.get("allocation_prompts"),
                planning_artifacts=original_plan.get("planning_artifacts"),
                allocation_artifacts=original_plan.get("allocation_artifacts"),
                server_logs=original_plan.get("server_logs") or None,
                name=copy_name,
                description=copy_description
            )

            if not new_plan_proto:
                raise HTTPException(status_code=500, detail="Failed to create plan copy")

            new_plan_id = new_plan_proto.plan_id

            # Copy all tasks from the original plan to the new plan
            if original_plan.get("tasks"):
                await bridge.registry.copy_plan_tasks(original_plan["plan_id"], new_plan_id)

            # Reset execution status to not_executed
            await bridge.registry.update_plan(
                plan_id=new_plan_id,
                execution_status=0
            )

            # Get the final plan with copied tasks
            copied_plan = await bridge.get_plan(new_plan_id)
            return copied_plan

        except Exception as e:
            logger.error(f"Failed to copy plan {plan_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to copy plan: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to copy plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to copy plan: {str(e)}")


@router.put("/{plan_id}")
async def update_plan(
    plan_id: int,
    request: PlanUpdateRequest,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Update a plan's name and description only.

    Args:
        plan_id: Plan to update.
        request: New name/description.
        bridge: Bridge + registry.

    Returns:
        Updated plan from ``get_plan``.

    Side effects:
        ``registry.update_plan`` then re-fetch.

    Failure behavior:
        **404** if missing; **500** if update returns nothing or errors;
        **200** on success.
    """
    try:
        # Get the current plan to ensure it exists
        current_plan = await bridge.get_plan(plan_id)
        if not current_plan:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

        # Update the plan name and description
        updated_plan_proto = await bridge.registry.update_plan(
            plan_id=plan_id,
            name=request.name,
            description=request.description
        )

        if not updated_plan_proto:
            raise HTTPException(status_code=500, detail="Failed to update plan")

        # Get the updated plan data
        updated_plan = await bridge.get_plan(plan_id)
        return updated_plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update plan: {str(e)}")
