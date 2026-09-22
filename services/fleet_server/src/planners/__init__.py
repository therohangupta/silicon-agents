"""
Agent fleet planning system package.

This package exposes the planner abstraction used by ``FleetManagerService``
when ``CreatePlan`` runs with an automatic planning strategy:

  * ``BasePlanner`` — shared capability loading, agent context strings,
    ``save_plan_to_db``, and DAG→Plan conversion.
  * ``get_planner`` — factory mapping protobuf ``PlanningStrategy`` enums to
    concrete planners (Monolithic, DAG, BigDAG). MANUAL_PLAN is rejected here
    because the service creates an empty shell directly.
  * Concrete types re-exported from ``types``: MonolithicPlanner, DAGPlanner,
    BigDAGPlanner, and Replanner (recovery path used by the Executor).

Planning strategies explained briefly:
  - Monolithic: one sequential task list for all goals (no parallelism).
  - DAG: independent per-goal DAGs merged into one Plan.
  - Big DAG: single cross-goal DAG allowing inter-goal dependencies.
  - Replanner: not selected via get_planner; builds recovery Plans after failure.
"""

from .base import (
    BasePlanner,
    PlanningStrategy,
    get_planner,
)
from .types import MonolithicPlanner, DAGPlanner, BigDAGPlanner, Replanner

__all__ = [
    'BasePlanner',
    'PlanningStrategy',
    'get_planner',
    'MonolithicPlanner',
    'DAGPlanner',
    'BigDAGPlanner',
    'Replanner',
]
