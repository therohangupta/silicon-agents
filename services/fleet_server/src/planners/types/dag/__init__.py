"""
DAG planner module — parallel task planning per goal.

Exports ``DAGPlanner``, which asks the LLM for a separate DAGPlan per goal
(with goal-prefixed node ids), concatenates nodes, then converts to the
unified ``Plan`` schema via ``BasePlanner._convert_dag_to_plan``.
"""

from .planner import DAGPlanner

__all__ = ["DAGPlanner"]
