"""
BigDAG planner that creates a single DAG for all goals in the system.

Unlike ``DAGPlanner`` (isolated per-goal graphs), ``BigDAGPlanner`` sends
every goal description in one user prompt and asks the LLM for one unified
``DAGPlan``. Edges in ``depends_on`` may reference nodes belonging to other
goals, enabling cross-goal optimization (shared setup tasks, ordering
constraints, divide-and-conquer across agent types).

The resulting DAG is still converted to the unified ``Plan`` schema before
persistence so the rest of the pipeline (allocators, Executor) stays agnostic
to which planner produced the graph.
"""

# json.loads parses the single LLM DAGPlan response.
import json
# logging for node counts and parse errors.
import logging
# Typing for goal id lists.
from typing import List, Dict, Any
# os.getenv for OPENAI_API_KEY.
import os
# Path for co-located prompt files.
from pathlib import Path
# OpenAI structured parse client.
from openai import OpenAI
# Shared planner base.
from ...base import BasePlanner
# DAG/Plan Pydantic models.
from ....formats.formats import Plan, DAGPlan, DAGNode, TaskPlanItem

# Module logger.
logger = logging.getLogger(__name__)

# Prompts are co-located with this planner
PROMPT_DIR = Path(__file__).parent


class BigDAGPlanner(BasePlanner):
    """
    Planner that creates a single DAG for all goals in the system.

    This allows for coordinated planning across multiple goals, including
    cross-goal dependency edges that the per-goal DAG planner cannot express.
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
            prompt_type: ``system`` or ``user`` stem name.

        Returns:
            Raw prompt file text.
        """
        filepath = PROMPT_DIR / f"{prompt_type}.prompt"
        with open(filepath, 'r') as f:
            return f.read()

    async def plan(self, goal_ids: List[int]) -> str:
        """
        Generate a comprehensive DAG-based plan that addresses multiple goals
        with potential interdependencies between goals.

        Args:
            goal_ids: List of goal IDs to include in the plan

        Returns:
            JSON string representation of the plan in Plan format

        Raises:
            ValueError: Empty goal list, missing goals, or unparsable LLM JSON.
        """
        if not goal_ids:
            raise ValueError("BigDAGPlanner requires at least one goal ID")

        # Get all goals first so we can build a multi-goal context block.
        goals = []
        for goal_id in goal_ids:
            goal = await self.registry.get_goal(goal_id)
            if not goal:
                raise ValueError(f"Goal with ID {goal_id} not found")
            goals.append(goal)

        # Initialize planning artifacts with goals data
        self.planning_artifacts = {
            "goals": [{"goal_id": goal.goal_id, "description": goal.description} for goal in goals],
            "dag_structure": {
                "nodes": [],
                "edges": []
            }
        }

        # Ensure agents exist and build LLM-facing agent summary.
        capabilities = await self._load_capabilities()
        agent_context = await self._get_agent_context_string()

        # Load prompt templates (co-located with this planner)
        system_prompt_template = self._load_prompt("system")
        user_prompt_template = self._load_prompt("user")

        # Build the goals context block listing every goal id + description.
        goals_context = "GOALS TO PLAN FOR:\n"
        for goal in goals:
            goals_context += f"GOAL ID: {goal.goal_id}\n"
            goals_context += f"DESCRIPTION: {goal.description}\n\n"

        # Format prompts (system is static; user gets goals + agents).
        system_prompt = system_prompt_template
        user_prompt = user_prompt_template.format(
            goals_context=goals_context,
            agent_context=agent_context,
        )

        # Store prompts for later retrieval / plan row persistence.
        self.planning_prompts = {
            "system": system_prompt,
            "user": user_prompt
        }

        # Call the OpenAI API once for the unified DAG.
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format=DAGPlan
        )

        # Parse the response content JSON into DAGNode models.
        big_dag_json = response.choices[0].message.content
        try:
            # Parse the JSON response into a DAGPlan model
            big_dag_dict = json.loads(big_dag_json)
            nodes_data = big_dag_dict.get("nodes", [])

            # Convert to Pydantic model for validation
            dag_nodes = [DAGNode(**node) for node in nodes_data]
            big_dag_plan = DAGPlan(nodes=dag_nodes)

            logger.info("Generated BigDAG plan with %s nodes for %s goals", len(dag_nodes), len(goals))

            # Store DAG structure in artifacts (include agent_type for transparency)
            self.planning_artifacts["dag_structure"] = {
                "nodes": [{"id": node.id, "description": node.description, "goal_id": node.goal_id, "agent_type": node.agent_type} for node in dag_nodes],
                "edges": [{"from": node.id, "to": dep} for node in dag_nodes for dep in (node.depends_on or [])]
            }
        except Exception as e:
            logger.error("Error parsing BigDAG response: %s", e)
            raise ValueError(f"Failed to parse LLM response: {e}")

        # Convert DAG format to Plan format using the parent class method
        return super()._convert_dag_to_plan(big_dag_plan)
