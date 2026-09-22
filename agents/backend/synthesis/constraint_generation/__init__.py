"""Public package exports for the Constraint Generation and Validation agent.

This ``__init__`` exists so importers can ``from agent import ConstraintGenerationAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: SDC (Synopsys Design Constraints) authorship and audit: create_clock, create_generated_clock, set_input_delay / set_output_delay, clock uncertainty, clock groups, false paths, multicycle paths, and case analysis. Bad constraints silently create optimistic timing that later fails STA or equivalence.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``ConstraintGenerationAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import ConstraintGenerationAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['ConstraintGenerationAgent']
