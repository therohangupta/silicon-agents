"""Package marker for the RTL Integration Agent (`rtl_integration`).

Re-exports `RtlIntegrationAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Merge compatible block candidates and mark stale downstream results.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import RtlIntegrationAgent  # Bind the local agent class for package-level re-export.

__all__ = ['RtlIntegrationAgent']  # Public surface: only the agent class is part of the stable API.
