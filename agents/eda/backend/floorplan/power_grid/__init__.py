"""Public package exports for the Power-Grid agent.

This ``__init__`` exists so importers can ``from agent import PowerGridAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: PDN design: rings, straps, standard-cell rails, vias, and macro power connections against IR-drop, electromigration (EM), and routing-resource budgets. Adapter target: OpenROAD pdngen. Early IR/EM proxies guide strap pitch before signoff analysis.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``PowerGridAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EDAAgent subclass defined in agent.py for package users.
from agent import PowerGridAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['PowerGridAgent']
