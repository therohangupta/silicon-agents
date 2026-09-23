"""Public export surface for the DFT Lead agent package (dft_lead).

Importing this package re-exports ``DftLeadAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import DftLeadAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import DftLeadAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['DftLeadAgent']  # Explicit export list for star-import and API clarity.
