"""Package marker for the Lint/Quality Agent (`lint_quality`).

Re-exports `LintQualityAgent` so tests and in-process fleet loaders can import the agent class
from this package path. Detect structural, synthesis, style, and maintainability problems in a candidate.

Importing this module does not start the HTTP server; use `server.py` for that.
"""

from agent import LintQualityAgent  # Bind the local agent class for package-level re-export.

__all__ = ['LintQualityAgent']  # Public surface: only the agent class is part of the stable API.
