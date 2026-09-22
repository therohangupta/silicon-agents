"""
LLM-based allocator module.

Exports ``LLMAllocator``, which serializes tasks/agents into prompts and
asks GPT-4 for an ``Allocation`` structured response, then writes agent_ids.
"""

from .allocator import LLMAllocator

__all__ = ["LLMAllocator"]
