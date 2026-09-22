"""
Big DAG planner module — unified cross-goal task planning.

Exports ``BigDAGPlanner``, which sends all goals in one prompt and receives
a single DAGPlan where ``depends_on`` edges may cross goal boundaries.
"""

from .planner import BigDAGPlanner

__all__ = ["BigDAGPlanner"]
