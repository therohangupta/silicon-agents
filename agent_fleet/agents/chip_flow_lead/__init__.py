"""Public export surface for the Chip Flow Lead agent package (chip_flow_lead).

Importing this package re-exports ``ChipFlowLeadAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import ChipFlowLeadAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import ChipFlowLeadAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['ChipFlowLeadAgent']  # Explicit export list for star-import and API clarity.
