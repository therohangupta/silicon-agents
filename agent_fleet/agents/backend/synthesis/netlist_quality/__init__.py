"""Public package exports for the Netlist Quality agent.

This ``__init__`` exists so importers can ``from agent import NetlistQualityAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Structural netlist audit: combinational loops, undriven/unused nets, high fanout, unmapped or dont-use cells, DFT/scan survival, congestion-risk cells, and QoR regressions versus a recorded baseline. Catches defects synthesis QoR can hide.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``NetlistQualityAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import NetlistQualityAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['NetlistQualityAgent']
