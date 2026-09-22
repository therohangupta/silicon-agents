"""Public export surface for the Lab Procedure agent package (lab_procedure).

Importing this package re-exports ``LabProcedureAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import LabProcedureAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import LabProcedureAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['LabProcedureAgent']  # Explicit export list for star-import and API clarity.
