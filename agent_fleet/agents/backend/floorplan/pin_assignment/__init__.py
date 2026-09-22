"""Public package exports for the Pin-Assignment agent.

This ``__init__`` exists so importers can ``from agent import PinAssignmentAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Block pin locations, metal layers, bus ordering, and legal feedthroughs against package/bump contracts and edge track capacity. Adapter target: OpenROAD place_pins. Pin density violations create unroutable boundaries and package mismatches.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``PinAssignmentAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import PinAssignmentAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['PinAssignmentAgent']
