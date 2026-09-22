"""
Monolithic planning strategy implementation.

``MonolithicPlanner`` asks the LLM for a single sequential ``Plan`` covering
all goals. Tasks may interleave across goals, but the prompts instruct the
model not to exploit broad parallelism — each task typically depends on prior
indices, forming a chronological chain.

This is the simplest planning mode and is a good default when ordering is
more important than concurrent agent utilization.
"""

# json retained for potential parsing helpers (response is already Plan JSON).
import json
# logging for generated plan dumps.
import logging
# OpenAI structured Plan parse.
from openai import OpenAI
# os.getenv for API key.
import os
# Path for co-located prompts.
from pathlib import Path
# Base planner helpers.
from ...base import BasePlanner
# Unified Plan schema used as response_format.
from ....formats.formats import Plan
# Typing for goal id lists.
from typing import List

# Module logger.
logger = logging.getLogger(__name__)

# Prompts are co-located with this planner
PROMPT_DIR = Path(__file__).parent


class MonolithicPlanner(BasePlanner):
    """
    Planner that uses a monolithic approach to generate plans.

    Produces one Plan JSON for the full goal set via a single GPT-4o call
    with ``response_format=Plan``.
    """

    def __init__(self, registry=None):
        """
        Initialize BasePlanner state and OpenAI client.

        Args:
            registry: Optional shared AgentInstanceRegistry from the service.
        """
        super().__init__(registry=registry)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _load_prompt(self, prompt_type: str) -> str:
        """
        Load a prompt file from this planner's directory.

        Args:
            prompt_type: ``system`` or ``user`` stem.

        Returns:
            Raw prompt text.
        """
        filepath = PROMPT_DIR / f"{prompt_type}.prompt"
        with open(filepath, 'r') as f:
            return f.read()

    async def plan(self, goal_ids: List[int]) -> str:
        """
        Generate a sequential plan where tasks for all goals are planned in sequence.

        Tasks can depend on previous tasks, including from different goals.
        Prompts discourage parallelism (empty deps only for the first task).

        Args:
            goal_ids: List of goal IDs to plan for

        Returns:
            JSON string representation of the plan

        Raises:
            ValueError: If goal_ids is empty or a goal cannot be loaded.
        """
        if not goal_ids:
            raise ValueError("MonolithicPlanner requires at least one goal ID")

        # Fetch all goals from the registry.
        goals = []
        for goal_id in goal_ids:
            goal = await self.registry.get_goal(goal_id)
            if not goal:
                raise ValueError(f"Goal with ID {goal_id} not found")
            goals.append(goal)

        # Capability union + agent summary for the user prompt.
        capabilities = await self._load_capabilities()
        agent_context = await self._get_agent_context_string()

        # Load prompt templates (co-located with this planner)
        system_prompt_template = self._load_prompt("system")
        user_prompt_template = self._load_prompt("user")

        # Build the goals context block for the user prompt.
        goals_context = "GOALS TO PLAN FOR:\n"
        for goal in goals:
            goals_context += f"GOAL ID: {goal.goal_id}\n"
            goals_context += f"DESCRIPTION: {goal.description}\n\n"

        # Format prompts with goals + agent context.
        system_prompt = system_prompt_template
        user_prompt = user_prompt_template.format(
            goals_context=goals_context,
            agent_context=agent_context,
        )

        # Store prompts for later retrieval on the plan row.
        self.planning_prompts = {
            "system": system_prompt,
            "user": user_prompt
        }

        # Store planning artifacts.
        # NOTE: The following block references plan_json before it is assigned
        # (historical behavior preserved exactly). At runtime this raises
        # NameError unless an outer scope already defined plan_json.
        self.planning_artifacts = {
            "goals": [goal.description for goal in goals],
            "agent_context": agent_context,
            "capabilities": capabilities,
            "dag_structure": {
                "nodes": [{"id": f"task_{i}", "description": task.get("description", "")} for i, task in enumerate(plan_json.get("tasks", []))],
                "edges": []
            }
        }

        # Call the OpenAI API with Plan as the structured response schema.
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format=Plan
        )

        # Extract the response content (Plan JSON string).
        plan_json = response.choices[0].message.content
        logger.info("Generated monolithic plan for goals %s:\n%s", goal_ids, plan_json)

        # Store the generated plan as an artifact for dashboard inspection.
        self.planning_artifacts["generated_plan"] = plan_json

        # Return Plan JSON for save_plan_to_db.
        return plan_json
