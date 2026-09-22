"""Package marker for the Interface Agent (`interface`).

Re-exports `InterfaceAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Define inter-block protocols and contracts, including the assertions those contracts imply.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import InterfaceAgent  # Bind the local agent class for package-level re-export.

__all__ = ['InterfaceAgent']  # Public surface: only the agent class is part of the stable API.
