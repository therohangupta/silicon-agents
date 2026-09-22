"""Public export surface for the DRC/LVS/ERC/DFM Agent package.

This ``__init__`` re-exports ``DrcLvsAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import DrcLvsAgent  # Concrete EdaAgent subclass for physical verification (DRC, LVS, ERC, density, DFM).

__all__ = ['DrcLvsAgent']  # Explicit re-export list for ``from ...drc_lvs import *`` safety.
