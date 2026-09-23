"""Stable capability/type-aware task allocator."""

from __future__ import annotations

import logging
from typing import Any, Dict

from ...base import BaseAllocator
from ....formats.formats import AgentTask, Allocation

logger = logging.getLogger(__name__)


def _eligible(task: Any, agent: Any) -> bool:
    agent_type = getattr(task, "agent_type", None)
    required = set(getattr(task, "required_capabilities", []) or [])
    return (
        (not agent_type or agent.agent_type == agent_type)
        and required.issubset(set(agent.capabilities))
    )


class DeterministicAllocator(BaseAllocator):
    async def allocate(self, plan_id: int) -> Dict[int, str]:
        plan = await self.registry.get_plan(plan_id)
        if not plan:
            logger.error("No plan found for plan_id=%s", plan_id)
            return {}
        tasks = [
            task for task in await self.registry.list_tasks()
            if int(task.plan_id) == plan_id
        ]
        agents = list(await self.registry.list_agents())
        if not agents:
            logger.error("No agents found in the registry.")
            return {}
        assigned_counts = {agent.agent_id: 0 for agent in agents}
        allocations: list[AgentTask] = []
        for task in sorted(tasks, key=lambda item: int(item.task_id)):
            eligible = [agent for agent in agents if _eligible(task, agent)]
            if not eligible:
                raise ValueError(f"no eligible agent for task {task.task_id}")
            winner = min(
                eligible,
                key=lambda agent: (assigned_counts[agent.agent_id], agent.agent_id),
            )
            assigned_counts[winner.agent_id] += 1
            allocations.append(AgentTask(task_id=int(task.task_id), agent_id=winner.agent_id))
        for assignment in allocations:
            await self.registry.update_task(assignment.task_id, agent_id=assignment.agent_id)
        self.allocation_artifacts = {"allocations": [a.model_dump() for a in allocations]}
        return Allocation(allocations=allocations)
