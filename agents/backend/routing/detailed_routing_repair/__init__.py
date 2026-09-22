"""Package export for the Detailed-Routing Repair Agent.

This ``__init__`` re-exports ``DetailedRoutingRepairAgent`` so fleet scanners and tests can import the
agent class from the package root of ``detailed_routing_repair/``. Importing this
module loads ``agent.py``, which reads ``config.yaml`` into an ``AgentSpec`` via
``EdaAgent.read_spec``. It does not open sockets; ``server.py`` is what serves HTTP.
"""

# Import the concrete EDA agent class defined beside this package marker.
from agent import DetailedRoutingRepairAgent

# Public export list used by ``from ... import *`` and documentation scanners.
__all__ = ['DetailedRoutingRepairAgent']
