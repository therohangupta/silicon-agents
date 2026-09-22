"""
DAG-based planning strategy implementation.

``DAGPlanner`` generates an independent Directed Acyclic Graph for each goal,
using goal-prefixed node ids (e.g. ``goal3_node0``) so that concatenating all
nodes into one ``DAGPlan`` cannot collide. Cross-goal dependencies are
intentionally forbidden by the prompts; goals remain isolated subgraphs that
the Executor may still run in parallel when agents are free.

After all per-goal LLM calls complete, nodes are merged and converted to the
unified ``Plan`` schema via ``BasePlanner._convert_dag_to_plan`` so
``save_plan_to_db`` can remap indices to database task ids.
"""

# json.loads parses the LLM DAGPlan JSON content.
import json
# logging for per-goal generation progress and parse errors.
import logging
# OpenAI client for structured DAGPlan responses.
from openai import OpenAI
# os.getenv reads OPENAI_API_KEY.
import os
# Path locates co-located system.prompt / user.prompt files.
from pathlib import Path
# Typing for goal id lists and intermediate structures.
from typing import List, Dict, Any
# Shared planner base with capability helpers and DAG conversion.
from ...base import BasePlanner
# Pydantic models for DAG nodes and Plan conversion targets.
from ....formats.formats import Plan, DAGPlan, DAGNode, TaskPlanItem

# Module logger for DAGPlanner diagnostics.
logger = logging.getLogger(__name__)

# Prompts are co-located with this planner (system.prompt / user.prompt).
PROMPT_DIR = Path(__file__).parent


class DAGPlanner(BasePlanner):
    """
    Planner that uses a DAG-based approach to generate plans.

    Calls the LLM once per goal with a goal-specific user prompt, validates
    each response as ``DAGNode`` list items, extends a cumulative node list,
    records dag_structure artifacts for the dashboard, and returns Plan JSON.
    """

    def __init__(self, registry=None):
        """
        Initialize BasePlanner state and a dedicated OpenAI client.

        Args:
            registry: Optional shared AgentInstanceRegistry from the service.
        """
        # Initialize artifact/prompt stores and registry binding.
        super().__init__(registry=registry)
        # Per-instance OpenAI client using the process API key.
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _load_prompt(self, prompt_type: str) -> str:
        """
        Load a prompt file from this planner's directory.

        Args:
            prompt_type: Stem name without extension (``system`` or ``user``).

        Returns:
            Raw prompt file contents as a string.
        """
        # Resolve e.g. system.prompt next to this module.
        filepath = PROMPT_DIR / f"{prompt_type}.prompt"
        # Read entire file; callers are responsible for .format() on templates.
        with open(filepath, 'r') as f:
            return f.read()

    async def plan(self, goal_ids: List[int]) -> str:
        """
        Generate separate DAG-based plans for each goal, then combine them.

        Each goal gets its own isolated DAG with no cross-goal dependencies.
        Node ids are prefixed with ``goal{id}_`` for global uniqueness.

        Args:
            goal_ids: List of goal IDs to generate plans for

        Returns:
            JSON string representation of the combined plan in Plan format

        Raises:
            ValueError: If goal_ids is empty, a goal is missing, or LLM JSON
                cannot be parsed into DAGNode models.
        """
        # Require at least one goal — empty input is a caller bug.
        if not goal_ids:
            raise ValueError("DAGPlanner requires at least one goal ID")

        # Initialize planning artifacts skeleton for dashboard transparency.
        self.planning_artifacts = {
            "goals": [],
            "dag_structure": {
                "nodes": [],
                "edges": []
            }
        }

        # Get all the goals from the registry up front.
        goals = []
        for goal_id in goal_ids:
            goal = await self.registry.get_goal(goal_id)
            if not goal:
                raise ValueError(f"Goal with ID {goal_id} not found")
            goals.append(goal)

        # Update goals in planning artifacts with id + description pairs.
        self.planning_artifacts["goals"] = [{"goal_id": goal.goal_id, "description": goal.description} for goal in goals]

        # Load fleet capabilities (raises if no agents) — used for feasibility.
        capabilities = await self._load_capabilities()
        # Human-readable agent summary injected into each user prompt.
        agent_context = await self._get_agent_context_string()

        # Load prompt templates (co-located with this planner)
        system_prompt_template = self._load_prompt("system")
        user_prompt_template = self._load_prompt("user")

        # System prompt is the same for all goals in this planner
        system_prompt = system_prompt_template

        # Store prompts for later retrieval (user is a template — varies per goal)
        self.planning_prompts = {
            "system": system_prompt,
            "user_template": user_prompt_template  # Store template since it varies per goal
        }

        # Generate separate DAGs for each goal into one cumulative list.
        all_nodes = []

        for goal in goals:
            # Current goal primary key.
            goal_id = goal.goal_id

            # Create a unique prefix for this goal's nodes
            goal_prefix = f"goal{goal_id}_"

            # Format the user prompt for this specific goal
            user_prompt = user_prompt_template.format(
                goal_id=goal_id,
                goal_description=goal.description,
                agent_context=agent_context,
                goal_prefix=goal_prefix
            )

            # Call the OpenAI API for this goal with DAGPlan response schema.
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

            # Parse the response as a DAGPlan (content is JSON text).
            goal_dag_plan = response.choices[0].message.content
            try:
                # Parse the JSON response into a Python dict first.
                goal_dag_plan = json.loads(goal_dag_plan)
                logger.debug("Generated DAG plan for goal %s:\n%s", goal_id, goal_dag_plan)
                # Convert to Pydantic models for validation
                goal_dag_nodes = [DAGNode(**node) for node in goal_dag_plan['nodes']]

                # Add to our cumulative list of nodes
                all_nodes.extend(goal_dag_nodes)
                logger.info("Generated DAG plan for goal %s with %s nodes", goal_id, len(goal_dag_nodes))
            except Exception as e:
                # Surface parse failures with the goal id for debugging.
                logger.error("Error parsing response for goal %s: %s", goal_id, e)
                raise ValueError(f"Failed to parse LLM response: {e}")

        # Create a DAGPlan from all nodes across all goals.
        combined_dag = DAGPlan(nodes=all_nodes)

        # Store DAG structure in artifacts (include agent_type for transparency)
        self.planning_artifacts["dag_structure"] = {
            "nodes": [{"id": node.id, "description": node.description, "goal_id": node.goal_id, "agent_type": node.agent_type} for node in all_nodes],
            "edges": [{"from": node.id, "to": dep} for node in all_nodes for dep in (node.depends_on or [])]
        }

        # Convert DAG format to Plan format using the parent class method
        return super()._convert_dag_to_plan(combined_dag)
