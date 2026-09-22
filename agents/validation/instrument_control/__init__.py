"""Public export surface for the Instrument Control agent package (instrument_control).

Importing this package re-exports ``InstrumentControlAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import InstrumentControlAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import InstrumentControlAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['InstrumentControlAgent']  # Explicit export list for star-import and API clarity.
