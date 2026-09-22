"""
Cost-based iterative task allocator.

Uses iterative assignment with LLM reasoning to minimize task switching
costs while respecting dependencies and agent capabilities.

Algorithm sketch:
  1. Build a dependency map for all tasks in the plan.
  2. While unassigned tasks remain, select the frontier (tasks whose deps
     are all already assigned — treated as "satisfied" for sequencing).
  3. Ask the LLM to map each agent to at most one frontier task, given
     ``previous_task_id`` (switching-cost signal).
  4. Record assignments, update agent states, repeat.
  5. Fallback: any leftovers are assigned to the first agent.

Unlike LLMAllocator (one shot) this respects DAG order during assignment
itself, which can reduce thrash when agents specialize mid-plan.
"""

# json.loads parses each round's agent→task_id mapping.
import json
# logging for rounds and fallback warnings.
import logging
# os.getenv for OPENAI_API_KEY.
import os
# OpenAI client for per-round JSON object responses.
from openai import OpenAI
# Dict/List typing for results and annotated return.
from typing import Dict, List

# Base allocator with prompt loader + registry.
from ...base import BaseAllocator
# Allocation envelope returned at the end.
from ....formats.formats import Allocation, AgentTask

# Module logger.
logger = logging.getLogger(__name__)


class CostBasedAllocator(BaseAllocator):
    """
    Cost-based allocator that minimizes task switching costs.

    Uses iterative assignment with LLM reasoning to:
    - Respect task dependencies
    - Minimize switching costs between tasks
    - Consider agent capabilities and current state
    - Handle complex dependency graphs
    """

    async def allocate(self, plan_id: int) -> Dict[int, str]:
        """
        Allocate tasks using cost-based iterative assignment.

        Args:
            plan_id: ID of the plan to allocate tasks for

        Returns:
            ``Allocation`` with all assignments. May raise if a round's LLM
            JSON cannot be parsed. Returns ``{}`` if plan/agents missing.
        """
        # Per-call OpenAI client.
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("CostBasedAllocator: Starting cost-based allocation...")

        # 1. Fetch plan, tasks, and agents
        plan = await self.registry.get_plan(plan_id)
        if not plan:
            logger.error("No plan found for plan_id=%s", plan_id)
            return {}
        tasks = await self.registry.list_tasks()
        tasks = [task for task in tasks if task.plan_id == plan_id]
        logger.info("Fetched %s tasks for the plan", len(tasks))
        agents = await self.registry.list_agents()
        if not agents:
            logger.error("No agents found in the registry.")
            return {}
        logger.info("Fetched %s agents from the registry", len(agents))

        # 2. Build DAG structure (task_id → task, task_id → dep set)
        task_map = {t.task_id: t for t in tasks}
        dependency_map = {}
        for t in tasks:
            # Use getattr to support both 'dependencies' and 'dependency_task_ids'
            deps = set(getattr(t, "dependency_task_ids", getattr(t, "dependencies", [])))
            dependency_map[t.task_id] = set(deps)

        # 2.5. Build initial available_queue: tasks with all dependencies satisfied
        assigned_tasks = set()
        # Track last assigned task per agent for switching-cost context.
        agent_states = {r.agent_id: None for r in agents}  # agent_id -> last assigned task_id
        allocation_result: List[Dict] = []

        # 4. Iterative allocation until frontier empties or a round assigns nothing.
        while True:
            # Prune the DAG: only consider root nodes (tasks whose dependencies are all satisfied)
            available_tasks = [t for t in tasks if t.task_id not in assigned_tasks and all(dep in assigned_tasks for dep in dependency_map[t.task_id])]
            if not available_tasks:
                # No frontier left — either done or deadlock; exit loop.
                break
            # Describe agents including previous_task_id for cost awareness.
            agent_descriptions = [
                {
                    "agent_id": str(r.agent_id),
                    "capabilities": str(r.capabilities),
                    "agent_type": getattr(r, "agent_type", None),
                    "previous_task_id": str(agent_states[r.agent_id]) if agent_states[r.agent_id] else None
                }
                for r in agents
            ]
            # Describe only the current frontier tasks.
            task_descriptions = [
                {
                    "task_id": str(t.task_id),
                    "description": str(t.description),
                    "agent_type": getattr(t, "agent_type", None)
                }
                for t in available_tasks
            ]
            logger.debug("------------------------------------")
            logger.debug("Available tasks (root nodes): %s", available_tasks)
            logger.debug("Agent descriptions: %s", agent_descriptions)
            logger.debug("Task descriptions: %s", task_descriptions)

            # Load prompt templates (co-located with this allocator)
            system_prompt = self._load_prompt("system")
            user_prompt_template = self._load_prompt("user")

            # Format the user prompt with context
            user_prompt = user_prompt_template.format(
                available_tasks=json.dumps(task_descriptions),
                agent_descriptions=json.dumps(agent_descriptions)
            )

            # Ask for a JSON object mapping agent_id → task_id.
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            allocation_content = response.choices[0].message.content
            logger.debug("LLM allocation response: %s", allocation_content)
            logger.debug("------------------------------------")
            try:
                agent_to_task = json.loads(allocation_content)
            except Exception as e:
                logger.error(f"Failed to parse LLM allocation response: {allocation_content}")
                raise
            assignments_this_round = 0
            assigned_this_round = set()
            # Convert mapping to AgentTask objects and update allocation_result
            for agent_id, task_id in agent_to_task.items():
                if task_id is None:
                    logger.info(f"Agent {agent_id} not assigned a task this round. Skipping.")
                    continue
                try:
                    task_id_int = int(task_id)
                except Exception:
                    logger.error(f"LLM returned non-integer task_id: {task_id} for agent {agent_id}")
                    continue
                allocation_result.append({
                    "agent_id": str(agent_id),
                    "task_id": task_id_int
                })
                # Mark task as assigned and update agent state
                assigned_tasks.add(task_id_int)
                assigned_this_round.add(task_id_int)
                agent_states[str(agent_id)] = task_id_int
                assignments_this_round += 1
            # Infinite loop protection: break if no assignments were made in this round
            if assignments_this_round == 0:
                logger.warning("No tasks could be assigned in this round. Breaking to avoid infinite loop.")
                break
        # Final check: assign any remaining unassigned tasks (fallback)
        unassigned = [tid for tid in task_map if tid not in assigned_tasks]
        if unassigned:
            logger.warning(f"Some tasks were still unassigned after LLM allocation: {unassigned}. Assigning to first capable agent as fallback.")
            for tid in unassigned:
                # Find first capable agent
                assigned = False
                for r in agents:
                    # You may want to check actual capability here
                    allocation_result.append({"agent_id": str(r.agent_id), "task_id": tid})
                    assigned_tasks.add(tid)
                    assigned = True
                    break
                if not assigned:
                    logger.error(f"No capable agent found for fallback assignment of task {tid}")
        logger.info("CostBasedAllocator: Final allocation: %s", allocation_result)
        # Update DB: assign each task to its agent
        for a in allocation_result:
            try:
                await self.registry.update_task(a["task_id"], agent_id=a["agent_id"])
                logger.info("Assigned agent %s to task %s", a['agent_id'], a['task_id'])
            except Exception as e:
                logger.error(f"Failed to assign agent {a['agent_id']} to task {a['task_id']}: {e}")
        # Always return Allocation object
        return Allocation(allocations=[AgentTask(**a) for a in allocation_result])
