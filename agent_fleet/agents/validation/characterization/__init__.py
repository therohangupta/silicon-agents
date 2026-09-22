"""Public export surface for the Characterization agent package (characterization).

Importing this package re-exports ``CharacterizationAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import CharacterizationAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import CharacterizationAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['CharacterizationAgent']  # Explicit export list for star-import and API clarity.
