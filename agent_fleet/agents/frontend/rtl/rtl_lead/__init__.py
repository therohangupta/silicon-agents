"""Package marker for the RTL Lead (`rtl_lead`).

Re-exports `RtlLeadAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Plan implementation of one block and coordinate lint, clock, CDC, low-power, and integration checks.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import RtlLeadAgent  # Bind the local agent class for package-level re-export.

__all__ = ['RtlLeadAgent']  # Public surface: only the agent class is part of the stable API.
