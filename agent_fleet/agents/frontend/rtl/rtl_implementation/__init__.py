"""Package marker for the RTL Implementation Agent (`rtl_implementation`).

Re-exports `RtlImplementationAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Make one bounded source change in an isolated branch and record the hypothesis it is testing.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import RtlImplementationAgent  # Bind the local agent class for package-level re-export.

__all__ = ['RtlImplementationAgent']  # Public surface: only the agent class is part of the stable API.
