"""Package marker for the Low-Power Agent (`low_power`).

Re-exports `LowPowerAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Maintain power domains, isolation, retention, and UPF consistency.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import LowPowerAgent  # Bind the local agent class for package-level re-export.

__all__ = ['LowPowerAgent']  # Public surface: only the agent class is part of the stable API.
