"""Public export surface for the Extraction Agent package.

This ``__init__`` re-exports ``ExtractionAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import ExtractionAgent  # Concrete EDAAgent subclass for parasitic extraction (SPEF) for signoff STA and power.

__all__ = ['ExtractionAgent']  # Explicit re-export list for ``from ...extraction import *`` safety.
