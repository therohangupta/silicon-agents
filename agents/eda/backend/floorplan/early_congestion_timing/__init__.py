"""Public package exports for the Early Congestion and Timing Evaluator agent.

This ``__init__`` exists so importers can ``from agent import EarlyCongestionTimingAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Pre-detail estimates of routability and timing via trial global placement and global route (OpenROAD). Identifies congestion hotspots and critical interfaces. Numbers are estimates, not signoff STA or detailed routing.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``EarlyCongestionTimingAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EDAAgent subclass defined in agent.py for package users.
from agent import EarlyCongestionTimingAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['EarlyCongestionTimingAgent']
