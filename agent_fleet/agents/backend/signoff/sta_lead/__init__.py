"""Public export surface for the STA Lead package.

This ``__init__`` re-exports ``StaLeadAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import StaLeadAgent  # Concrete EdaAgent subclass for multi-mode multi-corner (MMMC) static timing ownership.

__all__ = ['StaLeadAgent']  # Explicit re-export list for ``from ...sta_lead import *`` safety.
