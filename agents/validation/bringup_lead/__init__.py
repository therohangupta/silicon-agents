"""Public export surface for the Bring-up Lead agent package (bringup_lead).

Importing this package re-exports ``BringupLeadAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import BringupLeadAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import BringupLeadAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['BringupLeadAgent']  # Explicit export list for star-import and API clarity.
