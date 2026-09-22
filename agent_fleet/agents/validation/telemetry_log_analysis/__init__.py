"""Public export surface for the Telemetry / Log Analysis agent package (telemetry_log_analysis).

Importing this package re-exports ``TelemetryLogAnalysisAgent`` from the sibling ``agent``
module so tests and composition roots can write
``from … import TelemetryLogAnalysisAgent`` without depending on ``server.py``. Runtime
serving still goes through ``server.py``; this file does not start HTTP.
"""

from agent import TelemetryLogAnalysisAgent  # Concrete EdaAgent subclass defined next to this package.

__all__ = ['TelemetryLogAnalysisAgent']  # Explicit export list for star-import and API clarity.
