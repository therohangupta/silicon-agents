"""EDA domain: design scope, record types, action policy, and the agent base.

This package specializes the generic agent SDK and memory kits for chip-design
workflows. It owns the vocabulary that every silicon agent shares:

* ``EdaAgent`` — task lifecycle (context, journal, plan or execute, journal).
* ``ContextService`` — include/exclude/precedence assembly from memory.
* ``EngineeringMemory`` / ``open_memory`` — envelope writes and store backends.
* Specs and registry — ``config.yaml`` loading, catalog validation, planner view.
* Schemas — tasks, artifacts, messages, memory records, and enums.
* Fleet selection — which agent containers a fleet YAML starts.
* EDA adapters — framework binding points (default no-op).

Generic memory and context assembly live in ``packages.memory``. Agent
directories under ``agents/`` declare which EDA sources each agent loads via
their ``context:`` policy and subclass ``EdaAgent`` for runtime behavior.

Public re-exports below are the symbols most importers need. Deeper modules
(``fleet``, ``planning``, ``spec``, ``schemas.*``, ``memory.*``, ``eda.*``)
remain available for specialized callers.
"""

# Permission error and the shared agent base plus workflow helper.
from .agent import AgentPermissionError, EdaAgent, workflow_from_result
# Context assembler bound to engineering memory.
from .context import ContextService
# Memory facade and backend factory re-exported from the memory subpackage.
from .memory import EngineeringMemory, open_memory
# Catalog accessors used by planners and fleet selection.
from .registry import all_specs, get_spec, planner_catalog
# HTTP service that binds AgentServer to an EdaAgent subclass.
from .server import AgentService

# Explicit public surface for ``from domains.eda import ...``.
__all__ = [
    "AgentPermissionError",
    "AgentService",
    "EdaAgent",
    "ContextService",
    "EngineeringMemory",
    "all_specs",
    "get_spec",
    "open_memory",
    "planner_catalog",
    "workflow_from_result",
]
