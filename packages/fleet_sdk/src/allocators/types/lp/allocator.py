"""
Linear programming-based task allocator.

Uses PuLP to solve an optimization problem for balanced task allocation
across agents, considering capabilities, agent types, and task requirements.

Objective: minimize ``max_load`` (maximum number of tasks assigned to any
single agent) subject to:
  - each task assigned to exactly one agent (binary vars)
  - agent type matching when the task specifies ``agent_type``
  - capability subset matching (task caps ⊆ agent caps)
  - special fallback rules when caps cannot be inferred from descriptions

Capability inference is heuristic (keyword scans on task descriptions) for
legacy demos; when nothing matches, the agent with the most capabilities
is used as a fallback capability set / assignment target.
"""

# logging for allocation stages and infeasible solves.
import logging
# pulp provides LpProblem / LpVariable / solvers for the ILP.
import pulp
# Dict typing for the annotated return (actual return is Allocation).
from typing import Dict

# Abstract allocator with registry + artifact stores.
from ...base import BaseAllocator
# Allocation envelope returned to CreatePlan / AllocatePlan.
from ....formats.formats import Allocation, AgentTask

# Module logger.
logger = logging.getLogger(__name__)


class LPAllocator(BaseAllocator):
    """
    Linear programming-based allocator that minimizes maximum agent load.

    Uses integer linear programming to find an optimal assignment that:
    - Assigns each task to exactly one agent
    - Respects agent capabilities and types
    - Balances workload across agents (minimizes max tasks per agent)
    """

    async def allocate(self, plan_id: int) -> Dict[int, str]:
        """
        Allocate tasks using linear programming optimization.

        Args:
            plan_id: ID of the plan to allocate tasks for

        Returns:
            ``Allocation`` object (annotated historically as Dict[int, str]).
            Returns ``{}`` when the plan/agents are missing or the ILP is infeasible.
        """
        # Linear programming-based allocation using pulp
        # (re-import preserves historical local binding behavior)
        import pulp
        logger.info("LPAllocator: Starting linear programming allocation...")

        # 1. Fetch tasks for the plan
        plan = await self.registry.get_plan(plan_id)
        if not plan:
            logger.error("No plan found for plan_id=%s", plan_id)
            return {}
        # List all tasks then filter to this plan_id (registry has no plan-only helper here).
        tasks = await self.registry.list_tasks()
        tasks = [task for task in tasks if task.plan_id == plan_id]
        logger.info("Fetched %s tasks for the plan", len(tasks))

        # 2. Fetch agents and their capabilities
        agents = await self.registry.list_agents()
        if not agents:
            logger.error("No agents found in the registry.")
            return {}
        logger.info("Fetched %s agents from the registry", len(agents))

        # 3. Build capability map and infer task capabilities
        agent_caps = {r.agent_id: set(r.capabilities) for r in agents}
        task_caps = {}

        # Find a fallback agent (one with most capabilities)
        fallback_agent = max(agents, key=lambda r: len(r.capabilities))

        logger.debug("Selected fallback agent %s with capabilities: %s", fallback_agent.agent_id, fallback_agent.capabilities)

        for t in tasks:
            # If task has no required capabilities, infer them from description
            if not getattr(t, 'required_capabilities', []):
                caps = set()
                desc = t.description.lower()
                # Only add navigate if it's explicitly about navigation
                if 'navigate' in desc or 'move' in desc or 'go' in desc:
                    caps.add('navigate')
                # Only add pick if it's explicitly about picking up
                if 'pick' in desc:
                    caps.add('pick')
                # Only add place if it's explicitly about placing
                if 'place' in desc:
                    caps.add('place')
                if 'carry' in desc:
                    caps.add('carry')
                # Only add explore if it's explicitly about exploration
                if 'explore' in desc and 'area' in desc:
                    caps.add('explore_known_locations')
                # Only add capture_image if it's explicitly about capturing images
                if 'image' in desc or 'picture' in desc:
                    caps.add('capture_image')

                # If no capabilities were inferred, use fallback agent's capabilities
                if not caps:
                    logger.debug("Task %s (%s): No specific capabilities found, using fallback agent capabilities", t.task_id, t.description)
                    caps = set(fallback_agent.capabilities)

                task_caps[t.task_id] = caps
                logger.debug("Task %s (%s): Inferred capabilities: %s", t.task_id, t.description, caps)
            else:
                # Honor explicit required_capabilities when present on the task.
                task_caps[t.task_id] = set(t.required_capabilities)
                logger.debug("Task %s (%s): Using explicit capabilities: %s", t.task_id, t.description, task_caps[t.task_id])

        # 4. Build LP problem
        prob = pulp.LpProblem("TaskAllocation", pulp.LpMinimize)
        # Decision vars: x_{t,r} = 1 if task t assigned to agent r
        x = pulp.LpVariable.dicts(
            "assign",
            ((t.task_id, r.agent_id) for t in tasks for r in agents),
            cat=pulp.LpBinary
        )
        # Objective: minimize max load (number of tasks per agent)
        # Introduce variable for max load
        max_load = pulp.LpVariable("max_load", lowBound=0, cat=pulp.LpInteger)
        # Each task assigned to exactly one agent
        for t in tasks:
            prob += pulp.lpSum([x[(t.task_id, r.agent_id)] for r in agents]) == 1, f"OneAgentPerTask_{t.task_id}"
        # Only assign if agent has all required capabilities and matches agent_type if specified
        for t in tasks:
            task_agent_type = getattr(t, "agent_type", None)
            for r in agents:
                agent_actual_type = getattr(r, "agent_type", None)
                # Constraint 1: Agent type matching (if task specifies a type)
                type_match = True # Assume match if task doesn't specify a type or agent doesn't have a type
                if task_agent_type and agent_actual_type:
                    if task_agent_type != agent_actual_type:
                        type_match = False
                elif task_agent_type and not agent_actual_type:
                    # Task specifies a type, but agent has no type defined. Consider this a mismatch for typed tasks.
                    type_match = False

                # Constraint 2: Capability matching
                capability_match = task_caps[t.task_id].issubset(agent_caps[r.agent_id])

                if not type_match or not capability_match:
                    # If task has no specific capabilities (and thus using fallback), and no specific agent_type,
                    # allow assignment only to fallback agent (original logic for this case)
                    # This condition needs to be carefully placed. If a agent_type IS specified, it should take precedence.
                    if not task_caps[t.task_id] and not task_agent_type: # Task has no specific caps AND no specific type
                        if r.agent_id != fallback_agent.agent_id:
                            prob += x[(t.task_id, r.agent_id)] == 0, f"FallbackOnly_{t.task_id}_{r.agent_id}"
                        # else: allow assignment to fallback if it got here (type_match and capability_match were true for fallback)
                    else:
                        # If type mismatch OR capability mismatch (and not the special fallback case above)
                        prob += x[(t.task_id, r.agent_id)] == 0, f"Constraint_{t.task_id}_{r.agent_id}"

        # Max load constraint: each agent's assigned count ≤ max_load
        for r in agents:
            prob += pulp.lpSum([x[(t.task_id, r.agent_id)] for t in tasks]) <= max_load, f"MaxLoad_{r.agent_id}"
        # Objective: minimize max_load
        prob += max_load


        # 5. Solve the ILP with the default CBC solver via PuLP.
        status = prob.solve()
        if pulp.LpStatus[status] != "Optimal":
            logger.error("No feasible allocation found.")
            return {}
        # 6. Build allocation result from variables set to 1.
        allocation = []
        for t in tasks:
            for r in agents:
                if pulp.value(x[(t.task_id, r.agent_id)]) == 1:
                    allocation.append({"task_id": t.task_id, "agent_id": r.agent_id})
                    break
        logger.info("LPAllocator: Allocation result: %s", allocation)
        # Update DB with each assignment.
        for a in allocation:
            try:
                await self.registry.update_task(a["task_id"], agent_id=a["agent_id"])
                logger.info("Assigned agent %s to task %s", a['agent_id'], a['task_id'])
            except Exception as e:
                logger.error("Failed to assign agent %s to task %s: %s", a['agent_id'], a['task_id'], e)
        # Return as Allocation object (for compatibility)
        allocation_obj = Allocation(allocations=[AgentTask(**a) for a in allocation])
        return allocation_obj
