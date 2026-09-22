"""Package marker for the Security/Reliability Agent (`security_reliability`).

Re-exports `SecurityReliabilityAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Define threat, safety, isolation, and reliability obligations, and the verification tasks they require.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import SecurityReliabilityAgent  # Bind the local agent class for package-level re-export.

__all__ = ['SecurityReliabilityAgent']  # Public surface: only the agent class is part of the stable API.
