"""
Agent fleet allocator package.

Allocators assign concrete agent instance ids to tasks inside an existing
plan after a planner has created the task graph. ``FleetManagerService``
calls ``get_allocator`` from CreatePlan (when strategy != NONE) and from
AllocatePlan.

Strategies:
  - LPAllocator — integer linear program (PuLP) minimizing max load.
  - LLMAllocator — single-shot GPT-4 Allocation structured output.
  - CostBasedAllocator — iterative frontier assignment with switching-cost bias.

``BaseAllocator`` stores allocation_prompts / allocation_artifacts /
server_logs for persistence onto the plan row for dashboard inspection.
"""

from .base import BaseAllocator, get_allocator
from .types import LPAllocator, LLMAllocator, CostBasedAllocator

__all__ = [
    'BaseAllocator',
    'get_allocator',
    'LPAllocator',
    'LLMAllocator',
    'CostBasedAllocator',
]
