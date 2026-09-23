"""Public export surface for the Errata Drafting agent package (errata_drafting).

Importing this package re-exports ``ErrataDraftingAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import ErrataDraftingAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import ErrataDraftingAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['ErrataDraftingAgent']  # Explicit export list for star-import and API clarity.
