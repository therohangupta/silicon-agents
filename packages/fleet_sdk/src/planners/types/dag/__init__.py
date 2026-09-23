"""
DAG planner module — parallel task planning per goal.

Exports ``DAGPlanner``, which asks the LLM for a separate DAGPlan per goal
(with goal-prefixed node ids) and returns one combined ``DAGPlan``.
"""

from .planner import DAGPlanner

__all__ = ["DAGPlanner"]
