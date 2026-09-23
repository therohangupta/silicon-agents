"""Public export surface for the ATPG Campaign agent package (atpg_campaign).

Importing this package re-exports ``AtpgCampaignAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import AtpgCampaignAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import AtpgCampaignAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['AtpgCampaignAgent']  # Explicit export list for star-import and API clarity.
