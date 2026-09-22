"""Public export surface for the IR/EM Agent package.

This ``__init__`` re-exports ``IrEmAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import IrEmAgent  # Concrete EdaAgent subclass for IR drop and electromigration (EM) on the power grid.

__all__ = ['IrEmAgent']  # Explicit re-export list for ``from ...ir_em import *`` safety.
