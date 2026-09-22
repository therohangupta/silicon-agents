"""Package marker for the Power/Area Estimation Agent (`power_area_estimation`).

Re-exports `PowerAreaEstimationAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Produce early power and area estimates with explicit uncertainty and assumptions.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import PowerAreaEstimationAgent  # Bind the local agent class for package-level re-export.

__all__ = ['PowerAreaEstimationAgent']  # Public surface: only the agent class is part of the stable API.
