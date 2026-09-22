"""
Allocator type implementations package.

Each allocator type directory typically contains:
  - ``allocator.py``: Concrete ``BaseAllocator`` subclass.
  - ``summary.yaml``: Catalog metadata (id, name, method_type, examples).
  - Optional ``system.prompt`` / ``user.prompt`` for LLM-backed allocators
    (LP has no prompts — it is purely algorithmic).
"""

from .lp import LPAllocator
from .llm import LLMAllocator
from .cost_based import CostBasedAllocator

__all__ = ["LPAllocator", "LLMAllocator", "CostBasedAllocator"]
