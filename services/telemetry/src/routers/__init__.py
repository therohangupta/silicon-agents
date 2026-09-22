"""HTTP router subpackage for the telemetry FastAPI app.

Modules in this package each define an ``APIRouter`` that ``app.py`` includes.
Keeping routers split by concern (heartbeat ingest, health reads, telemetry
batch ingest, blob upload) makes OpenAPI tags and ownership clear. This
``__init__`` stays free of imports so importing ``routers.ingest`` does not
pull every route module at once.
"""
