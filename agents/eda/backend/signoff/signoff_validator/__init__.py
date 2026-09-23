"""Public export surface for the Independent Signoff Validator package.

This ``__init__`` re-exports ``SignoffValidatorAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import SignoffValidatorAgent  # Concrete EDAAgent subclass for independent signoff gate grading and waiver audit.

__all__ = ['SignoffValidatorAgent']  # Explicit re-export list for ``from ...signoff_validator import *`` safety.
