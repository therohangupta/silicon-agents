"""
Replanning strategy implementation.

``Replanner`` is invoked by ``Executor._handle_task_failure`` when a task
signals ``replan`` (or reliability policy ``on_failure == "replan"``). It does
**not** implement standard ``plan(goal_ids)`` — that method raises
``NotImplementedError``.

``replan(...)`` gathers:
  - original plan goals / strategies / ordered tasks
  - completed vs failed vs pending task summaries
  - agent assignment snapshot at failure time
  - agent capability context

Then it asks GPT-4o for a recovery ``Plan``, validates it, saves a **new**
plan via ``save_plan_to_db``, and immediately runs ``LLMAllocator`` on the
new plan so execution can resume with assigned agents. Returns the new
plan_id (Executor replaces ``self.plan_id`` with it).
"""

# json used when validating LLM output / catching JSONDecodeError.
import json
# OpenAI client for structured Plan parse.
from openai import OpenAI
# os for API key and __main__ guard.
import os
# Path for co-located prompts.
from pathlib import Path
# Base planner with save_plan_to_db + agent context helpers.
from ...base import BasePlanner
# Plan schema for response_format and validation.
from ....formats.formats import DAGPlan
# Typing for goal lists, assignment maps, optional registry.
from typing import List, Dict, Any, Optional
# logging throughout the multi-step replan pipeline.
import logging
# asyncio.run for the standalone __main__ test harness.
import asyncio
# Protobuf Plan type for type hints when reading the original plan.
from packages.proto import fleet_manager_pb2
# Registry type for constructor annotation.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# Default DB URL for the standalone test harness.
from packages.config import DATABASE_URL

# Module logger.
logger = logging.getLogger(__name__)

# Prompts are co-located with this planner
PROMPT_DIR = Path(__file__).parent


class Replanner(BasePlanner):
    """
    Planner that generates a recovery plan after a task failure.

    Standard ``plan()`` is intentionally unsupported. Use ``replan()`` only.
    """

    def __init__(self, db_url: Optional[str] = None, registry: Optional[AgentInstanceRegistry] = None):
        """
        Initialize BasePlanner, stash db_url, and create an OpenAI client.

        Args:
            db_url: Optional DB URL when constructing without a shared registry.
            registry: Preferred shared registry from Executor / service.
        """
        # Pass db_url through to BasePlanner for registry construction if needed.
        super().__init__(db_url, registry=registry)
        # Keep db_url for debugging / harness symmetry.
        self.db_url = db_url
        # Dedicated OpenAI client for replan LLM calls.
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _load_prompt(self, prompt_type: str) -> str:
        """
        Load a prompt file from this planner's directory.

        Args:
            prompt_type: ``system`` or ``user`` stem.

        Returns:
            Raw prompt file text.
        """
        filepath = PROMPT_DIR / f"{prompt_type}.prompt"
        with open(filepath, 'r') as f:
            return f.read()

    async def plan(self, goal_ids: List[int]) -> DAGPlan:
        """
        Replanner does not implement standard planning.

        Args:
            goal_ids: Ignored; present only to satisfy BasePlanner's signature.

        Raises:
            NotImplementedError: Always — use ``replan`` instead.
        """
        raise NotImplementedError("Replanner only supports the 'replan' method.")

    async def replan(self, plan_id: int, failed_task_id: int, failure_message: str, agent_task_assignments: Dict[str, List]) -> int:
        """
        Generate a new plan segment to recover from a failure and save it.

        Builds rich LLM context from the original plan, calls GPT-4o for a
        sequential recovery Plan, validates/saves it, then allocates with
        ``LLMAllocator``.

        Args:
            plan_id: Original plan that encountered the failure.
            failed_task_id: Task id that failed or surfaced new information.
            failure_message: Agent-provided failure / discovery message.
            agent_task_assignments: Map of agent_id → list of task ids (Executor
                passes per-agent remaining queues; first id is treated as the
                active assignment for status text).

        Returns:
            The ID of the newly created (and allocated) recovery plan.

        Raises:
            ValueError: Missing plan/tasks, invalid LLM JSON, or save failures.
            Exception: Propagates unexpected errors after logging.
        """
        logger.info("Starting replan for Plan ID: %s, Failed Task ID: %s", plan_id, failed_task_id)

        try:
            # 1. Fetch Original Plan Data
            original_plan_obj: Optional[fleet_manager_pb2.Plan] = await self.registry.get_plan(plan_id)
            if not original_plan_obj:
                raise ValueError(f"Original plan with ID {plan_id} not found.")

            # Preserve original strategies/goals when saving the recovery plan.
            original_goal_ids = list(original_plan_obj.goal_ids)
            original_planning_strategy = original_plan_obj.planning_strategy
            original_allocation_strategy = original_plan_obj.allocation_strategy

            # Ordered task ids define completed/failed/pending slices.
            ordered_task_ids_for_context = original_plan_obj.task_ids
            if not ordered_task_ids_for_context:
                logger.warning(f"Plan {plan_id} from registry does not directly list ordered task_ids. Context generation might be limited.")

            # Materialize task protos in plan order for context summaries.
            original_tasks_in_order = []
            for task_id_for_context in ordered_task_ids_for_context:
                task = await self.registry.get_task(task_id_for_context)
                if task:
                    original_tasks_in_order.append(task)
                else:
                    logger.warning(f"Task ID {task_id_for_context} listed in plan {plan_id} not found in registry for context.")

            if not original_tasks_in_order and ordered_task_ids_for_context:
                logger.warning(f"Could not retrieve detailed task objects for plan {plan_id} context, though task IDs were listed.")

            # Build goals context lines for the user prompt.
            goal_ids_for_context = original_plan_obj.goal_ids
            goals = []
            goals_context_lines = []
            for gid in goal_ids_for_context:
                goal = await self.registry.get_goal(gid)
                if goal:
                    goals.append(goal)
                    goals_context_lines.append(f"- GOAL ID: {goal.goal_id}, DESCRIPTION: {goal.description}")
                else:
                    logger.warning(f"Goal ID {gid} for plan {plan_id} not found.")
            goals_context = "\n".join(goals_context_lines) if goals_context_lines else "No goal details found."

            # 2. Determine Task States based on ordered list and failed_task_id
            failed_task_index = -1
            for i, task in enumerate(original_tasks_in_order):
                if task.task_id == failed_task_id:
                    failed_task_index = i
                    break

            # Validate that the failed task is actually part of the plan order.
            if failed_task_index == -1 and ordered_task_ids_for_context:
                if failed_task_id not in ordered_task_ids_for_context:
                    raise ValueError(f"Failed task ID {failed_task_id} not part of plan {plan_id}'s task list: {ordered_task_ids_for_context}")
                logger.error(f"Failed task ID {failed_task_id} was in plan's task list but corresponding task object not retrieved for context.")
                raise ValueError(f"Failed task ID {failed_task_id} could not be processed from plan {plan_id}.")
            elif not ordered_task_ids_for_context and failed_task_id:
                raise ValueError(f"Plan {plan_id} has no tasks, so cannot find failed_task_id {failed_task_id}")

            # Slice the ordered tasks into completed / failed / pending groups.
            completed_tasks_objects = original_tasks_in_order[:failed_task_index]
            failed_task_object = original_tasks_in_order[failed_task_index]
            pending_tasks_objects_original = original_tasks_in_order[failed_task_index+1:]

            # Human-readable summaries for the user prompt.
            completed_tasks_summary = "\n".join([f"- Task ID {t.task_id}: '{t.description}' (Goal {t.goal_id})" for t in completed_tasks_objects]) or "None"
            pending_tasks_summary = "\n".join([f"- Task ID {t.task_id}: '{t.description}' (Goal {t.goal_id})" for t in pending_tasks_objects_original]) or "None"

            # 3. Format Agent Task Status Context
            agent_task_status_lines = []
            for agent_id, task_ids in agent_task_assignments.items():
                try:
                    if len(task_ids) == 0:
                        # Agent had an empty queue at failure time.
                        agent_details = await self.registry.get_agent(agent_id)
                        agent_name = agent_details.agent_id
                        agent_task_status_lines.append(f"- {agent_name} (ID: {agent_id}) had no tasks assigned.")
                    else:
                        # First task id is treated as the active assignment.
                        agent_details = await self.registry.get_agent(agent_id)
                        current_task_id = task_ids[0]
                        task_details = await self.registry.get_task(current_task_id)
                        status = "FAILED OR NEW INFORMATION FOUND" if current_task_id == failed_task_id else "ACTIVE (at time of failure)"
                        agent_name = agent_details.agent_id if agent_details else f"Agent {agent_id}"
                        task_desc = task_details.description if task_details else f"Task {current_task_id}"
                        agent_task_status_lines.append(f"- {agent_name} (ID: {agent_id}) was assigned Task ID {current_task_id}: '{task_desc}'. Status: {status}")
                except Exception as e:
                    # Soft-fail individual agent lines so one bad lookup continues.
                    current_task_id = task_ids[0]
                    logger.warning(f"Could not get details for agent {agent_id} or task {current_task_id}: {e}")
                    agent_task_status_lines.append(f"- Agent ID {agent_id} was assigned Task ID {current_task_id} (Details unavailable). Status: UNKNOWN")
            agent_task_status_context = "\n".join(agent_task_status_lines) if agent_task_status_lines else "No agent assignments provided or details unavailable."

            # Capability summary for the recovery planner LLM.
            agent_capabilities_context = await self._get_agent_context_string()

            # 5. Load and Format Prompts (co-located with this planner)
            system_prompt = self._load_prompt("system")
            user_prompt_template = self._load_prompt("user")

            user_prompt = user_prompt_template.format(
                plan_id=plan_id,
                failed_task_id=failed_task_id,
                goals_context=goals_context,
                failure_message=failure_message,
                agent_task_status_context=agent_task_status_context,
                completed_tasks_summary=completed_tasks_summary,
                pending_tasks_summary=pending_tasks_summary,
                agent_capabilities_context=agent_capabilities_context,
            )

            logger.debug(f"Replanning System Prompt:\n{system_prompt}")
            logger.debug(f"Replanning User Prompt:\n{user_prompt}")

            # 6. Call LLM for a sequential recovery Plan.
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

            # Extract and validate the content string.
            llm_response_content = response.choices[0].message.content
            if not llm_response_content or not isinstance(llm_response_content, str):
                logger.error(f"LLM response content is not a valid string: {llm_response_content}")
                raise ValueError("LLM generated empty or invalid content for the replan.")

            replan_json_str = llm_response_content
            logger.info(f"Generated replan JSON for Plan ID {plan_id}:\n{replan_json_str}")

            # 7. Validate and Save Replanning LLM response
            try:
                # Pydantic validation against Plan schema before DB write.
                graph = DAGPlan.model_validate_json(replan_json_str)
                logger.info("Replanning LLM response successfully validated against DAGPlan schema.")

                new_plan_id = await self.persist_dag(
                    graph,
                    planning_strategy=original_planning_strategy,
                    allocation_strategy=original_allocation_strategy,
                    goal_ids=original_goal_ids,
                )
                logger.info(f"Successfully saved new replan with ID: {new_plan_id} to the database.")

                # Call the allocator to assign agents to the new tasks
                from ....allocators.types.llm.allocator import LLMAllocator
                allocator = LLMAllocator(registry=self.registry)
                await allocator.registry.initialize()
                allocation_result = await allocator.allocate(new_plan_id)
                logger.info(f"Allocation result for new plan: {allocation_result}")

                # Return new plan id so Executor can switch execution targets.
                return new_plan_id

            except json.JSONDecodeError as e:
                logger.error(f"Replanning LLM response is not valid JSON: {e}\nContent: {replan_json_str}")
                raise ValueError(f"Replanning failed: LLM response was not valid JSON. Error: {e}")
            except Exception as e:
                logger.error(f"Failed to validate or save replan: {e}\nContent: {replan_json_str}")
                raise ValueError(f"Replanning failed: Could not validate or save the plan. Error: {e}")

        except Exception as e:
            # Outer catch logs and re-raises for Executor handling.
            logger.error(f"Error during replanning for plan {plan_id}: {e}")
            raise


async def main():
    """
    Standalone harness that exercises ``replan`` with hardcoded sample ids.

    Intended for manual developer testing against a live DB + OpenAI key.
    Not used by the Fleet Manager gRPC service.
    """
    # Hardcoded values for testing
    replanner = Replanner(db_url=DATABASE_URL)

    sample_plan_id = 1
    sample_failed_task_id = 3
    sample_failure_message = "Navigation sensor malfunctioned on approach to trash bin."
    sample_agent_task_assignments = {
        "nav-1": sample_failed_task_id,
        "pick-place-1": 4
    }

    logger.info(f"Attempting to replan with hardcoded values: plan_id={sample_plan_id}, failed_task_id={sample_failed_task_id}")

    try:
        new_plan_id = await replanner.replan(
            plan_id=sample_plan_id,
            failed_task_id=sample_failed_task_id,
            failure_message=sample_failure_message,
            agent_task_assignments=sample_agent_task_assignments
        )
        logger.info("Replanning successful. New plan segment created with ID: %s", new_plan_id)
    except ValueError as ve:
        logger.error("Replanning validation error: %s", ve)
    except NotImplementedError as nie:
        logger.error("Replanning not implemented error: %s", nie)
    except Exception as e:
        logger.exception("An unexpected error occurred during replanning: %s", e)
    finally:
        # Close registry resources if the implementation exposes close().
        if hasattr(replanner.registry, 'close'):
            await replanner.registry.close()


if __name__ == "__main__":
    # Configure logging for the standalone harness.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Require an API key before attempting an LLM call.
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set.")
        exit(1)
    # Drive the async harness.
    asyncio.run(main())
