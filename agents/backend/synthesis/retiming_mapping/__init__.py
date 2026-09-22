"""Public package exports for the Retiming and Mapping agent.

This ``__init__`` exists so importers can ``from agent import RetimingMappingAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: State-preserving retiming (moving registers without changing observable latency), logic restructuring, resource sharing, and technology mapping against dont-use lists. Architectural latency contracts and equivalence jobs must still hold after transforms.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``RetimingMappingAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import RetimingMappingAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['RetimingMappingAgent']
