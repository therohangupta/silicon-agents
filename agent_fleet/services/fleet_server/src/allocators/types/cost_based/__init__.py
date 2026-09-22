"""
Cost-based iterative allocator module.

Exports ``CostBasedAllocator``, which repeatedly assigns the current DAG
frontier (tasks whose deps are done) via LLM rounds that minimize switching
cost given each agent's previous_task_id, until all tasks are assigned.
"""

from .allocator import CostBasedAllocator

__all__ = ["CostBasedAllocator"]
