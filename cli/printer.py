"""Pretty-printers and strategy enum maps for the ``agentctl`` CLI.

Centralizes human-readable stdout for agents, goals, tasks, and plans so
Click commands stay free of formatting logic. Also exposes
``PLANNING_STRATEGY_*`` and ``ALLOCATION_STRATEGY_*`` maps used by Click
``Choice`` arguments and for decoding protobuf enums back to CLI strings.

``print_plan`` renders an ASCII DAG via Kahn topological sort when verbose.
Older commented ``print_plan`` variants are retained below as historical
notes and must not be re-enabled without review.
"""

# click.echo for consistent CLI stdout/stderr.
import click
# sys.exit(1) on failed standard responses.
import sys
# List typing for print_all_goals signature.
from typing import List
# Protobuf enums and message types for Name() lookups.
from packages.proto import fleet_manager_pb2

# Map CLI planning strategy strings to protobuf enum values.
PLANNING_STRATEGY_ENUMS = {
    "monolithic": fleet_manager_pb2.PlanningStrategy.MONOLITHIC,
    "dag": fleet_manager_pb2.PlanningStrategy.DAG,
    "big_dag": fleet_manager_pb2.PlanningStrategy.BIG_DAG,
    "manual": fleet_manager_pb2.PlanningStrategy.MANUAL_PLAN,
}
# Click Choice list derived from the map keys.
PLANNING_STRATEGY_CHOICES = list(PLANNING_STRATEGY_ENUMS.keys())
# Reverse map: enum int/value -> CLI string (legacy helpers).
PLANNING_STRATEGY_STRINGS = {v: k for k, v in PLANNING_STRATEGY_ENUMS.items()}

# Map CLI allocation strategy strings to protobuf enum values.
ALLOCATION_STRATEGY_ENUMS = {
    "lp": fleet_manager_pb2.AllocationStrategy.LP,
    "llm": fleet_manager_pb2.AllocationStrategy.LLM,
    "cost_based": fleet_manager_pb2.AllocationStrategy.COST_BASED,
    "none": fleet_manager_pb2.AllocationStrategy.NONE,
    "manual": fleet_manager_pb2.AllocationStrategy.MANUAL_ALLOCATION,
}
# Click Choice list for plan create.
ALLOCATION_STRATEGY_CHOICES = list(ALLOCATION_STRATEGY_ENUMS.keys())
# Reverse map for display if needed.
ALLOCATION_STRATEGY_STRINGS = {v: k for k, v in ALLOCATION_STRATEGY_ENUMS.items()}


def print_response(response, success_prefix: str = "Success", error_prefix: str = "Failed"):
    """Print a standard response message and exit with code 1 if failed.

    Expects ``response.success`` and ``response.message``. On failure writes
    to stderr and calls ``sys.exit(1)`` so Click commands abort consistently.

    Args:
        response: Response object with success and message fields.
        success_prefix: Prefix for success message (default: "Success").
        error_prefix: Prefix for error message (default: "Failed").
    """
    # Happy path: echo success to stdout.
    if response.success:
        click.echo(f"{success_prefix}: {response.message}")
    else:
        # Failure path: stderr + non-zero exit for scripts.
        click.echo(f"{error_prefix}: {response.message}", err=True)
        sys.exit(1)


def print_task(task, verbose=False, include_newline: bool = True, tabs: int = 0):
    """Print details of a single task.

    In non-verbose mode prints only ``Task {id}``. In verbose mode prints
    description, goal/plan ids, dependencies, and agent_id when set. Indent
    output by ``tabs`` spaces for nested tree displays under goals/agents.
    """
    # Build indent string once for all lines.
    indent = ' ' * tabs
    # Optional blank line before the block (top-level listings).
    if include_newline:
        click.echo("")
    # Compact one-liner when not verbose.
    if not verbose:
        click.echo(f"{indent}Task {task.task_id}")
        return
    # Verbose: print selected proto fields.
    click.echo(f"{indent}Task {task.task_id}:")
    click.echo(f"{indent}  description: {task.description}")
    # Omit zero goal_id (unset).
    if task.goal_id != 0:
        click.echo(f"{indent}  goal_id: {task.goal_id}")
    # Omit zero plan_id (unset).
    if task.plan_id != 0:
        click.echo(f"{indent}  plan_id: {task.plan_id}")
    # Show dependency list when non-empty.
    if task.dependency_task_ids:
        click.echo(f"{indent}  dependency_task_ids: {task.dependency_task_ids}")
    # Show assignee when present.
    if task.agent_id:
        click.echo(f"{indent}  agent_id: {task.agent_id}")


def print_goal(goal, plans=None, tasks=None, verbose=False, include_newline: bool = True):
    """Print a goal, optionally with nested plans and their tasks when verbose.

    Always prints goal id and description. When ``verbose`` and ``plans`` are
    provided, lists each plan's strategy and filters ``tasks`` by ``plan_id``
    for a nested tree via ``print_task``.
    """
    # Optional leading blank line.
    if include_newline:
        click.echo("")
    # Header + identity fields.
    click.echo(f"Goal {goal.goal_id}:")
    click.echo(f"  Goal ID: {goal.goal_id}")
    click.echo(f"  Description: {goal.description}")

    # Nested plan/task tree only in verbose mode with plan data.
    if plans and verbose:
        click.echo("  Plans:")
        for plan in plans:
            click.echo(f"    Plan: {plan.plan_id}")
            # Decode planning strategy enum to a name string.
            strategy_value = getattr(plan, 'planning_strategy', None)
            strategy_str = fleet_manager_pb2.PlanningStrategy.Name(strategy_value)
            click.echo(f"      Strategy: {strategy_str}")
            # Attach tasks belonging to this plan when provided.
            if tasks:
                plan_tasks = [task for task in tasks if task.plan_id == plan.plan_id]
                if plan_tasks:
                    click.echo("      Tasks:")
                    for task in plan_tasks:
                        # Nested indent under the plan block.
                        print_task(task, verbose=verbose, include_newline=False, tabs=8)


# def print_plan(plan, goals=None, tasks=None, verbose=False, include_newline: bool = True):
#     """Print details of a single plan, optionally with associated goals and tasks (tree style)"""
#     if include_newline:
#         click.echo("")
#     click.echo(f"Plan: {plan.plan_id}")
#     strategy_value = getattr(plan, 'planning_strategy', None)
#     strategy_str = PLANNING_STRATEGY_STRINGS.get(strategy_value, str(strategy_value))
#     click.echo(f"  Strategy: {strategy_str}")
#     if verbose and hasattr(plan, 'goal_ids') and plan.goal_ids:
#         click.echo(f"  Goals:")
#         for gid in plan.goal_ids:
#             if goals:
#                 goal = next((g for g in goals if g.goal_id == gid), None)
#                 if goal:
#                     click.echo(f"    Goal ID: {goal.goal_id}")
#                     click.echo(f"    Description: {goal.description}")
#                     if verbose and tasks:
#                         plan_tasks = [task for task in tasks if task.goal_id == goal.goal_id and task.plan_id == plan.plan_id]
#                         if plan_tasks:
#                             click.echo("        Tasks:")
#                             for task in plan_tasks:
#                                 print_task(task, verbose=verbose, include_newline=False, tabs=10)

# Re-import click for the active print_plan section (historical duplicate import).
import click
# defaultdict/deque power the DAG adjacency + Kahn queue.
from collections import defaultdict, deque
# Ensure pb2 is bound in this section's scope (historical duplicate import).
from packages.proto import fleet_manager_pb2


def print_plan(plan, goals=None, tasks=None, verbose=False, include_newline: bool = True):
    """Print details of a single plan as an ASCII DAG per goal when verbose.

    Always prints plan id, planning strategy name, and allocation strategy
    name. When verbose and the plan has ``goal_ids``, builds a dependency
    graph of plan tasks, topologically sorts with Kahn's algorithm, and
    prints tree bullets with goal/task/agent and dependency annotations.
    ``goals`` is accepted for API symmetry with callers but unused in the
    current DAG view.
    """
    # Optional leading blank line.
    if include_newline:
        click.echo("")
    # Plan header.
    click.echo(f"Plan: {plan.plan_id}")
    # Decode planning strategy enum.
    strategy_value = getattr(plan, 'planning_strategy', None)
    strategy_str = fleet_manager_pb2.PlanningStrategy.Name(strategy_value)
    # Decode allocation strategy when present.
    allocation_value = getattr(plan, 'allocation_strategy', None)
    allocation_str = fleet_manager_pb2.AllocationStrategy.Name(allocation_value) if allocation_value is not None else "UNSPECIFIED"
    click.echo(f"  Strategy: {strategy_str}")
    click.echo(f"  Allocation: {allocation_str}")

    # Non-verbose or plans without goals: stop after header.
    if not verbose or not hasattr(plan, 'goal_ids') or not plan.goal_ids:
        return

    click.echo("  Tasks (DAG View):")
    # Collect all tasks for this plan (regardless of goal).
    plan_tasks = [t for t in (tasks or []) if t.plan_id == plan.plan_id]
    # Nothing to render.
    if not plan_tasks:
        return

    # Map task_id -> set of prerequisite task ids.
    deps = {t.task_id: set(t.dependency_task_ids) for t in plan_tasks}
    # Adjacency: prerequisite -> dependents.
    graph = defaultdict(set)
    for tid, prereqs in deps.items():
        for d in prereqs:
            graph[d].add(tid)
    # Kahn indegrees start at zero for every plan task.
    indegree = {t.task_id: 0 for t in plan_tasks}
    # Count incoming edges from the adjacency list.
    for src, targets in graph.items():
        for tgt in targets:
            indegree[tgt] += 1

    # Kahn's algorithm for topological sort.
    queue = deque([tid for tid, deg in indegree.items() if deg == 0])
    topo = []
    while queue:
        nid = queue.popleft()
        topo.append(nid)
        for m in graph[nid]:
            indegree[m] -= 1
            if indegree[m] == 0:
                queue.append(m)

    # Render each task in topo order with ASCII bullets.
    for idx, tid in enumerate(topo):
        task = next(t for t in plan_tasks if t.task_id == tid)
        # Last item gets a corner bullet; others get a tee.
        bullet = "└─" if idx == len(topo) - 1 else "├─"
        dep_list = deps[tid]
        dep_str = ""
        if dep_list:
            dep_str = " (depends on " + ", ".join(f"T{d}" for d in sorted(dep_list)) + ")"
        click.echo(f"    {bullet} (G{task.goal_id}, T{task.task_id}, {task.agent_id}): {task.description}{dep_str}")


def print_agent(agent, verbose=False, tasks=None, include_newline: bool = True):
    """Print details of a single agent, with optional verbose task info.

    Always prints id, type, description, and task-server host/port. When
    status is present, prints state name and message. Lists capabilities when
    non-empty. In verbose mode with ``tasks``, nests ``print_task`` under the
    agent.
    """
    # Optional leading blank line.
    if include_newline:
        click.echo("")
    # Core identity fields.
    click.echo(f"Agent: {agent.agent_id}")
    click.echo(f"Type: {agent.agent_type}")
    click.echo(f"Description: {agent.description}")
    click.echo(f"Host: {agent.task_server_info.host}")
    click.echo(f"Port: {agent.task_server_info.port}")

    # Optional nested status message from the fleet manager.
    status = getattr(agent, 'status', None)
    if status:
        state = getattr(status, 'state', None)
        if state is not None:
            # Local import preserves historical structure.
            from packages.proto import fleet_manager_pb2
            state_name = fleet_manager_pb2.AgentStatus.State.Name(state)
            click.echo(f"Status: {state_name}")
        if getattr(status, 'message', None):
            click.echo(f"Status Message: {status.message}")
    # Capability bullets when the repeated field is non-empty.
    if getattr(agent, 'capabilities', []):
        click.echo(f"Capabilities:")
        for cap in agent.capabilities:
            click.echo(f"  - {cap}")

    # Verbose: list assigned tasks if provided by the caller.
    if verbose:
        if getattr(agent, 'task_ids', []) and tasks:
            click.echo(f"Tasks:")
            for task in tasks:
                print_task(task, verbose=verbose, include_newline=False, tabs=4)


def print_all_agents(agents, tasks_by_agent=None, verbose=False):
    """Print a list of agents, optionally with their tasks (tree style).

    Prints ``No agents found`` when the list is empty. When verbose, looks up
    each agent's tasks in ``tasks_by_agent`` if provided.
    """
    # Empty fleet message for operators.
    if not agents:
        click.echo("No agents found")
        return
    # One block per agent.
    for agent in agents:
        assigned_tasks = tasks_by_agent[agent.agent_id] if (verbose and tasks_by_agent and agent.agent_id in tasks_by_agent) else None
        print_agent(agent, verbose=verbose, tasks=assigned_tasks)


def print_all_tasks(tasks, verbose=False):
    """Print a list of tasks, optionally with details.

    Uses ``include_newline=False`` so consecutive tasks do not double-space.
    """
    if not tasks:
        click.echo("No tasks found")
        return
    for task in tasks:
        print_task(task, verbose=verbose, include_newline=False)


def print_all_goals(goals: List[fleet_manager_pb2.Goal], tasks_by_goal=None, verbose=False):
    """Print a list of goals.

    Passes ``tasks_by_goal`` through as the ``tasks`` argument to ``print_goal``
    (historical parameter name). Empty list prints ``No goals found``.
    """
    if not goals:
        click.echo("No goals found")
        return
    for goal in goals:
        print_goal(goal, tasks=tasks_by_goal, verbose=verbose, include_newline=False)


def print_all_plans(plans, goals=None, tasks_by_plan=None, verbose=False):
    """Print a list of plans, optionally with associated goals and tasks.

    Delegates each plan to ``print_plan``. Empty list prints ``No plans found``.
    """
    if not plans:
        click.echo("No plans found")
        return
    for plan in plans:
        print_plan(plan, goals, tasks_by_plan, verbose=verbose, include_newline=False)
