"""Public export surface for the Failure Correlation agent package (failure_correlation).

Importing this package re-exports ``FailureCorrelationAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import FailureCorrelationAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import FailureCorrelationAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['FailureCorrelationAgent']  # Explicit export list for star-import and API clarity.
