"""Public export surface for the Thermal and Reliability Agent package.

This ``__init__`` re-exports ``ThermalReliabilityAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import ThermalReliabilityAgent  # Concrete EDAAgent subclass for thermal, aging, variation, and reliability margins.

__all__ = ['ThermalReliabilityAgent']  # Explicit re-export list for ``from ...thermal_reliability import *`` safety.
