"""Public package exports for the Macro-Placement Experiment Worker agent.

This ``__init__`` exists so importers can ``from agent import MacroPlacementAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Hard-macro placement under halo, channel, orientation, and keepout constraints. Adapter targets OpenROAD initialize_floorplan and macro placement. Scores flyline connectivity and writes a floorplan DEF for one isolated candidate.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``MacroPlacementAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import MacroPlacementAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['MacroPlacementAgent']
