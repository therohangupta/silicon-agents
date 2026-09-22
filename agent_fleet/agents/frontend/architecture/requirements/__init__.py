"""Package marker for the Requirements Agent (`requirements`).

Re-exports `RequirementsAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Convert product goals into traceable, measurable requirements and acceptance criteria.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import RequirementsAgent  # Bind the local agent class for package-level re-export.

__all__ = ['RequirementsAgent']  # Public surface: only the agent class is part of the stable API.
