"""Public export surface for the Testability Analysis agent package (testability_analysis).

Importing this package re-exports ``TestabilityAnalysisAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import TestabilityAnalysisAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import TestabilityAnalysisAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['TestabilityAnalysisAgent']  # Explicit export list for star-import and API clarity.
