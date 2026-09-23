"""
Fleet Server service package.

This package is the top-level Python namespace for the Fleet Manager gRPC
service that orchestrates multi-agent planning, allocation, and execution
inside the agent_fleet workspace.

Responsibilities owned by this package (implemented under ``src/``):
  - Expose the FleetManager gRPC API (agents, goals, tasks, plans).
  - Select and run planners (monolithic, DAG, big DAG, replanner).
  - Select and run allocators (LP, LLM, cost-based).
  - Drive plan execution via the Executor (dependency-aware dispatch).
  - Emit fire-and-forget Gateway events when plan/task/agent state changes.

Import paths used at runtime resolve as ``services.fleet_server.*`` when the
workspace root is on ``PYTHONPATH`` / installed editable via ``pip install -e .``.
Docker entrypoint is ``python -m services.fleet_server.src``.
"""
