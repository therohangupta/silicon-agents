"""
Linear programming-based allocator module.

Exports ``LPAllocator``, which formulates task→agent assignment as a PuLP
binary ILP with capability/type constraints and a min-max-load objective.
"""

from .allocator import LPAllocator

__all__ = ["LPAllocator"]
