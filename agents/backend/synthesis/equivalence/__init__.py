"""Public package exports for the Equivalence agent.

This ``__init__`` exists so importers can ``from agent import EquivalenceAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: Logical (combinational) and sequential equivalence checking (LEC/SEC) between RTL and a transformed netlist. Compare-point maps, black boxes, and setup/constraints must be justified; mapped-away points without justification are findings. This is a check that feeds synthesis_lead, not an independent tapeout gate.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``EquivalenceAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import EquivalenceAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['EquivalenceAgent']
