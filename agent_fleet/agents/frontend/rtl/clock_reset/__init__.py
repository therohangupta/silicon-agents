"""Package marker for the Clock/Reset Agent (`clock_reset`).

Re-exports `ClockResetAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Check clocking, reset topology, and clock gating against the declared intent.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import ClockResetAgent  # Bind the local agent class for package-level re-export.

__all__ = ['ClockResetAgent']  # Public surface: only the agent class is part of the stable API.
