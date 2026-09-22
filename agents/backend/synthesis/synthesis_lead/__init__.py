"""Public package exports for the Synthesis Lead agent.

This ``__init__`` exists so importers can ``from agent import SynthesisLeadAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: RTL-to-gate synthesis orchestration: constraints, experiment hypotheses, retiming studies, logical/sequential equivalence, and netlist structural quality. PPA (power, performance, area) and equivalence acceptance decide which netlist may advance; failed equivalence always makes a candidate ineligible.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``SynthesisLeadAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import SynthesisLeadAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['SynthesisLeadAgent']
