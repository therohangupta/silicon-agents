"""Public export surface for the Scan Insertion agent package (scan_insertion).

Importing this package re-exports ``ScanInsertionAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import ScanInsertionAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import ScanInsertionAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['ScanInsertionAgent']  # Explicit export list for star-import and API clarity.
