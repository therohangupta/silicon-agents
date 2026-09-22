"""
LLM-based task allocator.

Uses OpenAI's GPT-4 to intelligently allocate tasks to agents
based on their capabilities, task requirements, and current state.

Unlike LP (pure math) or cost_based (iterative frontier rounds), this
allocator makes a **single** structured ``Allocation`` call with the full
task and agent lists, then writes every ``agent_id`` onto the corresponding
task rows and records prompts/artifacts/logs for the plan.
"""

# json.loads parses the Allocation JSON content from the model.
import json
# logging for allocation stages.
import logging
# os.getenv for OPENAI_API_KEY.
import os
# OpenAI client for structured Allocation parse.
from openai import OpenAI
# Dict typing for annotated return.
from typing import Dict

# Base allocator with prompt loader + registry.
from ...base import BaseAllocator
# Allocation / AgentTask schemas.
from ....formats.formats import Allocation, AgentTask

# Module logger.
logger = logging.getLogger(__name__)


class LLMAllocator(BaseAllocator):
    """
    LLM-based allocator that uses GPT-4 for intelligent task allocation.

    Considers agent capabilities, task requirements, and agent types in one
    shot via co-located system/user prompts.
    """

    async def allocate(self, plan_id: int) -> Dict[int, str]:
        """
        Allocate tasks using LLM reasoning.

        Args:
            plan_id: ID of the plan to allocate tasks for

        Returns:
            ``Allocation`` on success, or ``{}`` if plan/agents missing or
            the LLM response cannot be parsed.
        """
        # Construct a per-call OpenAI client.
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        logger.info("Starting allocation for plan_id: %s", plan_id)
        # Ensure the plan exists before listing tasks.
        plan = await self.registry.get_plan(plan_id)
        if not plan:
            logger.error("No plan found for plan_id=%s", plan_id)
            return {}
        # Filter global task list down to this plan.
        tasks = await self.registry.list_tasks()
        tasks = [task for task in tasks if task.plan_id == plan_id]
        logger.info("Fetched %s tasks for the plan", len(tasks))
        # Require at least one agent.
        agents = await self.registry.list_agents()
        if not agents:
            logger.error("No agents found in the registry.")
            return {}
        logger.info("Fetched %s agents from the registry", len(agents))
        logger.debug("tasks: %s", tasks)
        # Serialize tasks into JSON-friendly dicts for the user prompt.
        task_descriptions = [
            {
                "task_id": str(t.task_id),
                "description": str(t.description),
                "goal_id": str(t.goal_id),
                "dependencies": [str(dep) for dep in getattr(t, "dependency_task_ids", [])],
                "agent_type": getattr(t, "agent_type", None)
            }
            for t in tasks
        ]
        # Serialize agents similarly.
        agent_descriptions = [
            {
                "agent_id": str(r.agent_id),
                "agent_type": getattr(r, "agent_type", None),
                "capabilities": str(r.capabilities),
            }
            for r in agents
        ]

        # Load prompt templates (co-located with this allocator)
        system_prompt = self._load_prompt("system")
        user_prompt_template = self._load_prompt("user")

        # Format the user prompt with context
        user_prompt = user_prompt_template.format(
            task_descriptions=json.dumps(task_descriptions),
            agent_descriptions=json.dumps(agent_descriptions)
        )

        # Store allocation prompts and artifacts for plan persistence.
        self.allocation_prompts = {
            "system": system_prompt,
            "user": user_prompt
        }

        self.allocation_artifacts = {
            "task_descriptions": task_descriptions,
            "agent_descriptions": agent_descriptions,
        }

        logger.debug("Prepared prompts for LLM")
        logger.info("Calling OpenAI API...")
        # Structured parse into Allocation schema.
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format=Allocation,
        )
        allocation_content = response.choices[0].message.content
        try:
            # Parse JSON and construct Allocation / AgentTask models.
            allocation_dict = json.loads(allocation_content)
            logger.info("Generated allocation:\n%s", allocation_dict)
            allocation_obj = Allocation(allocations=[AgentTask(**rt) for rt in allocation_dict['allocations']])
            logger.info("Successfully parsed allocation: %s", allocation_obj)
        except Exception as e:
            logger.error("Failed to parse LLM allocation response: %s\nRaw response: %s", e, allocation_content)
            return {}
        # Store allocation result in artifacts
        self.allocation_artifacts["final_allocation"] = allocation_obj.dict()

        # Add logs for dashboard / plan.server_logs persistence.
        self.server_logs = [
            f"LLM allocator started for plan {plan_id}",
            f"Processed {len(task_descriptions)} tasks and {len(agent_descriptions)} agents",
            f"Generated allocation with {len(allocation_obj.allocations)} assignments",
            f"Allocation completed successfully"
        ]

        logger.info("Updating tasks in database with assigned agents...")
        for agent_task in allocation_obj.allocations:
            try:
                # Persist each assignment onto the task row.
                await self.registry.update_task(agent_task.task_id, agent_id=agent_task.agent_id)
                logger.info("Assigned agent %s to task %s", agent_task.agent_id, agent_task.task_id)
                self.server_logs.append(f"Assigned agent {agent_task.agent_id} to task {agent_task.task_id}")
            except Exception as e:
                error_msg = f"Failed to assign agent {agent_task.agent_id} to task {agent_task.task_id}: {e}"
                logger.error("%s", error_msg)
                self.server_logs.append(error_msg)
        logger.info("Task allocation complete. Final allocation: %s", allocation_obj)
        return allocation_obj
