"""
Pydantic models package for gateway request and response validation.

This package centralizes OpenAPI-facing schemas so routers stay thin:

- ``requests`` — bodies for POST/PUT/PATCH (registration, goals, plans, tasks).
- ``responses`` — shapes returned to the dashboard (agents, goals, plans, tasks,
  agent templates).

Re-exports below are the public surface used by routers and tests. Importing
this package does not perform I/O; models are pure validation/documentation
helpers. Invalid payloads raise FastAPI 422 validation errors before handlers run.
"""

# Request bodies for mutating endpoints.
from .requests import (
    AgentRegistration,
    AgentInstanceCreate,
    GoalCreate,
    PlanCreate,
    ManualPlanCreate,
    ManualTaskDefinition,
    TaskCreate,
)

# Response models used as response_model= on many routes.
from .responses import (
    AgentResponse,
    GoalResponse,
    PlanResponse,
    TaskResponse,
    AgentTemplateResponse,
)

# Explicit public API for star-imports and documentation tooling.
__all__ = [
    # Requests
    "AgentRegistration",
    "AgentInstanceCreate",
    "GoalCreate",
    "PlanCreate",
    "ManualPlanCreate",
    "ManualTaskDefinition",
    "TaskCreate",
    # Responses
    "AgentResponse",
    "GoalResponse",
    "PlanResponse",
    "TaskResponse",
    "AgentTemplateResponse",
]
