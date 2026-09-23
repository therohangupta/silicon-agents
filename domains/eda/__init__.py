"""EDA domain: schemas, memory, config, runtime, fleet, and toolchain adapters.

Layout:

* ``config/`` — ``EDAAgentConfig`` and YAML loading
* ``schemas/`` — tasks, messages, memory envelopes, enums
* ``memory/`` — engineering memory stores and policy
* ``runtime/`` — ``EDAAgent``, ``AgentService``, context assembly, lead planning
* ``fleet/`` — agent registry, compose selection, workflow intake
* ``adapters/`` — EDA framework bindings (default no-op)

Import from this package for the stable public surface, or from subpackages
when you need a narrower dependency.
"""

from .config import EDAAgentConfig, load_eda_agent_config
from .fleet import (
    all_configs,
    fleet_capability_index,
    get_config,
)
from .memory import EngineeringMemory, open_memory
from .runtime import (
    AgentPermissionError,
    AgentService,
    ContextService,
    EDAAgent,
    workflow_from_result,
)

__all__ = [
    "AgentPermissionError",
    "AgentService",
    "ContextService",
    "EDAAgent",
    "EDAAgentConfig",
    "EngineeringMemory",
    "all_configs",
    "fleet_capability_index",
    "get_config",
    "load_eda_agent_config",
    "open_memory",
    "workflow_from_result",
]
