"""
Base allocator classes and allocation strategy management.

This module contains the abstract base class for allocators and the
factory function for creating allocator instances used by
``FleetManagerService.CreatePlan`` / ``AllocatePlan``.

Allocators turn an already-planned task graph into concrete agent_id
assignments on each task row. Strategies:

  * LP — PuLP ILP minimizing maximum agent load under capability/type constraints.
  * LLM — single GPT-4o ``Allocation`` structured response.
  * COST_BASED — iterative LLM rounds over the dependency frontier.
  * NONE / MANUAL_ALLOCATION — not instantiable here; callers must skip.

``BaseAllocator`` also owns prompt loading (for LLM-backed subclasses) and
artifact/log buffers persisted onto the plan after allocation.
"""

# logging for allocator construction and prompt load failures.
import logging
# os retained for potential env-based configuration.
import os
# ABC/abstractmethod enforce allocate() on subclasses.
from abc import ABC, abstractmethod
# Dict/Optional typing for return maps and optional registry/db_url.
from typing import Dict, Optional
# Path used when resolving co-located *.prompt files.
from pathlib import Path

# Registry for listing tasks/agents and updating assignments.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# Default DB URL when registry is not injected.
from packages.config import DATABASE_URL
# Allocation schemas (imported for type symmetry / historical use).
from ..formats.formats import Allocation, AgentTask

# Module logger.
logger = logging.getLogger(__name__)


class BaseAllocator(ABC):
    """
    Abstract base class for all allocators.

    Subclasses implement ``allocate(plan_id)`` and typically mutate task rows
    via ``registry.update_task(..., agent_id=...)`` before returning an
    ``Allocation`` (or historically a mapping).
    """

    def __init__(self, db_url: Optional[str] = None, registry: Optional[AgentInstanceRegistry] = None):
        """
        Bind a registry and initialize empty prompt/artifact/log stores.

        Args:
            db_url: Used only when ``registry`` is omitted.
            registry: Preferred shared registry from FleetManagerService.
        """
        # Prefer injected registry so allocation sees the live fleet.
        self.registry = registry or AgentInstanceRegistry(db_url or DATABASE_URL)
        logger.info(f"Initialized {self.__class__.__name__}.")

        # Storage for allocation artifacts and prompts (persisted on plan rows).
        self.allocation_prompts = {}
        self.allocation_artifacts = {}
        self.server_logs = []

    def _load_prompt(self, prompt_type: str) -> str:
        """
        Load a prompt file from the allocator's directory.

        Resolves the directory from ``self.__class__.__module__`` by replacing
        dots with slashes and taking the parent — concrete allocators' prompts
        must live next to their allocator.py on that import path.

        Args:
            prompt_type: Type of prompt ('system' or 'user')

        Returns:
            The prompt content as a string

        Raises:
            FileNotFoundError: If the prompt file is missing.
            Exception: Other IO errors while reading.
        """
        # Get the directory of the concrete allocator class via its module path.
        allocator_dir = Path(self.__class__.__module__.replace('.', '/')).parent
        # Build path like .../llm/system.prompt
        prompt_file = allocator_dir / f"{prompt_type}.prompt"

        try:
            # Read the entire prompt file as UTF-8 text.
            with open(prompt_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading prompt file {prompt_file}: {e}")
            raise

    @abstractmethod
    async def allocate(self, plan_id: int) -> Dict[int, str]:
        """
        Allocate tasks from the given plan_id to agents.

        Args:
            plan_id: Plan whose tasks should receive agent_id assignments.

        Returns:
            Historically annotated as mapping task_id→agent_id; concrete
            implementations often return an ``Allocation`` Pydantic object.
        """
        pass


def get_allocator(allocation_strategy: int, db_url: str = None, registry: Optional[AgentInstanceRegistry] = None):
    """
    Return the appropriate Allocator instance based on the allocation strategy enum value.

    Args:
        allocation_strategy: Integer enum value from fleet_manager_pb2.AllocationStrategy
        db_url: Optional database URL for the allocator
        registry: Optional existing AgentInstanceRegistry to reuse

    Returns:
        An allocator instance for the given strategy

    Raises:
        ValueError: If allocation_strategy is NONE, MANUAL_ALLOCATION, or unknown
    """
    # Import protobuf enums lazily to keep module import light.
    from packages.proto import fleet_manager_pb2

    if allocation_strategy == fleet_manager_pb2.AllocationStrategy.LP:
        # Linear programming balanced load allocator.
        from .types.lp import LPAllocator
        return LPAllocator(db_url, registry=registry)
    elif allocation_strategy == fleet_manager_pb2.AllocationStrategy.LLM:
        # Single-shot LLM allocator.
        from .types.llm import LLMAllocator
        return LLMAllocator(db_url, registry=registry)
    elif allocation_strategy == fleet_manager_pb2.AllocationStrategy.COST_BASED:
        # Iterative cost-aware LLM allocator.
        from .types.cost_based import CostBasedAllocator
        return CostBasedAllocator(db_url, registry=registry)
    elif allocation_strategy == fleet_manager_pb2.AllocationStrategy.NONE:
        # Callers must skip allocation entirely for NONE.
        raise ValueError(
            "NONE strategy means no allocation. "
            "Check for NONE before calling get_allocator() and skip allocation."
        )
    elif allocation_strategy == fleet_manager_pb2.AllocationStrategy.MANUAL_ALLOCATION:
        # Manual means operators assign agents per-task in the UI/API.
        raise ValueError(
            "MANUAL_ALLOCATION strategy means agents are assigned manually per-task. "
            "Check for MANUAL_ALLOCATION before calling get_allocator() and skip allocation."
        )
    else:
        # Unknown future enum values fail loudly.
        raise ValueError(f"Unknown allocation strategy: {allocation_strategy}")
