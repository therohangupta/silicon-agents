"""
Replanner module — recovery planning after task failures.

Exports ``Replanner``, used by ``Executor._handle_task_failure`` when a task
result requests replan (or reliability policy says so). It does not implement
standard ``plan()``; only ``replan()`` is supported.
"""

from .planner import Replanner

__all__ = ["Replanner"]
