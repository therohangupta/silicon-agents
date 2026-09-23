"""Public export surface for the Power-Analysis Agent package.

This ``__init__`` re-exports ``PowerAnalysisAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import PowerAnalysisAgent  # Concrete EDAAgent subclass for vector-based and vectorless power estimation.

__all__ = ['PowerAnalysisAgent']  # Explicit re-export list for ``from ...power_analysis import *`` safety.
