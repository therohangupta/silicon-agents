"""Public export surface for the DFT Validator agent package (dft_validator).

Importing this package re-exports ``DftValidatorAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import DftValidatorAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import DftValidatorAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['DftValidatorAgent']  # Explicit export list for star-import and API clarity.
