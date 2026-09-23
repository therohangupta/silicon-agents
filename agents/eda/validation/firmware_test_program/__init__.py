"""Public export surface for the Firmware / Test Program agent package (firmware_test_program).

Importing this package re-exports ``FirmwareTestProgramAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import FirmwareTestProgramAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import FirmwareTestProgramAgent  # Concrete EDAAgent subclass defined next to this package.

__all__ = ['FirmwareTestProgramAgent']  # Explicit export list for star-import and API clarity.
