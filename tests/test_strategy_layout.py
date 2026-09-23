"""Guardrails for SDK-owned hierarchical planner/allocator layout."""

from packages.fleet_sdk.src.allocators.base import BaseAllocator
from packages.fleet_sdk.src.allocators.types.lp.allocator import LPAllocator
from packages.fleet_sdk.src.planners.base import BasePlanner
from packages.fleet_sdk.src.planners.types.dag.planner import DAGPlanner


def test_active_strategies_subclass_sdk_bases():
    assert issubclass(LPAllocator, BaseAllocator)
    assert issubclass(DAGPlanner, BasePlanner)


def test_sdk_execution_modules_import():
    from packages.fleet_sdk.src.execution_context import ExecutionContext
    from packages.fleet_sdk.src.executor import Executor

    assert ExecutionContext is not None
    assert Executor is not None


def test_strategy_prompts_live_next_to_implementations():
    from pathlib import Path

    lp_dir = Path("packages/fleet_sdk/src/allocators/types/llm")
    dag_dir = Path("packages/fleet_sdk/src/planners/types/dag")
    assert (lp_dir / "system.prompt").is_file()
    assert (dag_dir / "system.prompt").is_file()
