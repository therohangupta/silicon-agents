"""Public package exports for the Floorplanning Lead agent.

This ``__init__`` exists so importers can ``from agent import FloorplanningLeadAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Partition floorplanning: macros, pin assignment, power distribution network (PDN), blockages/utilization, and early routability/timing estimates. Recommends a candidate for placement without promoting it onto the baseline.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``FloorplanningLeadAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import FloorplanningLeadAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['FloorplanningLeadAgent']
