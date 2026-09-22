"""Public export surface for the Timing-Debug Agent package.

This ``__init__`` re-exports ``TimingDebugAgent`` so fleet loaders and tests can import the agent
class from the package root without reaching into ``agent.py`` directly. It does not
start the HTTP server, bind an EDA framework, or execute DRC/LVS/STA/IR/ECO tools.

Importing this module therefore has no side effects on silicon memory, telemetry, or
signoff gates beyond whatever import-time spec load ``agent.py`` performs.
"""

from agent import TimingDebugAgent  # Concrete EdaAgent subclass for STA query and path classification (setup/hold/recovery/removal/clock).

__all__ = ['TimingDebugAgent']  # Explicit re-export list for ``from ...timing_debug import *`` safety.
