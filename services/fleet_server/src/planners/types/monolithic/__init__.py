"""
Monolithic planner module — sequential task planning.

Exports ``MonolithicPlanner``, which produces a single ``Plan`` where tasks
are ordered chronologically and dependency indices form a chain (no broad
parallelism). Suitable for linear workflows.
"""

from .planner import MonolithicPlanner

__all__ = ["MonolithicPlanner"]
