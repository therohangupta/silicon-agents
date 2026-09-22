"""Package marker for the Performance Modeling Agent (`performance_modeling`).

Re-exports `PerformanceModelingAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Model target workloads and bottlenecks, and report projected metrics with their assumptions.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import PerformanceModelingAgent  # Bind the local agent class for package-level re-export.

__all__ = ['PerformanceModelingAgent']  # Public surface: only the agent class is part of the stable API.
