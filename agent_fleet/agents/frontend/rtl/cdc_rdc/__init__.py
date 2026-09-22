"""Package marker for the CDC/RDC Agent (`cdc_rdc`).

Re-exports `CdcRdcAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Analyze clock and reset domain crossings and return evidence for a fix or a human waiver.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import CdcRdcAgent  # Bind the local agent class for package-level re-export.

__all__ = ['CdcRdcAgent']  # Public surface: only the agent class is part of the stable API.
