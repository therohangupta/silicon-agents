"""Package export for the Antenna and Manufacturability Agent.

This ``__init__`` re-exports ``AntennaManufacturabilityAgent`` so fleet scanners and tests can import the
agent class from the package root of ``antenna_manufacturability/``. Importing this
module loads ``agent.py``, which reads ``config.yaml`` into an ``AgentSpec`` via
``EdaAgent.read_spec``. It does not open sockets; ``server.py`` is what serves HTTP.
"""

# Import the concrete EDA agent class defined beside this package marker.
from agent import AntennaManufacturabilityAgent

# Public export list used by ``from ... import *`` and documentation scanners.
__all__ = ['AntennaManufacturabilityAgent']
