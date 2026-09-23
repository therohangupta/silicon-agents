"""Public export surface for the ECO Lead package.

This ``__init__`` re-exports ``EcoLeadAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import EcoLeadAgent  # Concrete EDAAgent subclass for engineering change orders (ECO) for late RTL/timing/power/physical fixes.

__all__ = ['EcoLeadAgent']  # Explicit re-export list for ``from ...eco_lead import *`` safety.
