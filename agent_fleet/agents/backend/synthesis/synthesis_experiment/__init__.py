"""Public package exports for the Synthesis Experiment Worker agent.

This ``__init__`` exists so importers can ``from agent import SynthesisExperimentAgent`` via the
package path when the agent directory is on ``sys.path``, and so ``__all__``
documents the single supported entry class for this microservice.

EDA context: One isolated RTL-to-netlist compile with a named hypothesis (script, flatten vs preserve hierarchy, library set). Adapter targets Yosys synth first; a licensed synthesizer later binds the same operations. Emits QoR proxies (area, cell counts, timing estimate), warnings (blackboxes, latches, loops), and a gate-level netlist.

Importing this module imports ``agent.py``, which loads ``config.yaml`` into
``SynthesisExperimentAgent.spec`` but does not start the HTTP server or run synthesis/floorplan tools.
"""

# Re-export the concrete EdaAgent subclass defined in agent.py for package users.
from agent import SynthesisExperimentAgent

# Explicit export list so ``from <pkg> import *`` only exposes the agent class.
__all__ = ['SynthesisExperimentAgent']
