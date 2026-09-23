"""Public export surface for the DFT Physical/Timing agent package (dft_physical_timing).

Importing this package re-exports ``DftPhysicalTimingAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import DftPhysicalTimingAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import DftPhysicalTimingAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['DftPhysicalTimingAgent']  # Explicit export list for star-import and API clarity.
