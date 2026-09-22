"""Package marker for the Architecture Lead (`architecture_lead`).

Re-exports `ArchitectureLeadAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Own decomposition and high-level tradeoffs. Select a qualified architecture revision with block budgets, not an informal conclusion.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import ArchitectureLeadAgent  # Bind the local agent class for package-level re-export.

__all__ = ['ArchitectureLeadAgent']  # Public surface: only the agent class is part of the stable API.
