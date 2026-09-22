"""
Agent Fleet Dashboard — ASGI entry point for the gateway service.

This module exists so process managers and uvicorn can target a stable import
path (``src.main:app``) without needing to know that the FastAPI application
is constructed inside ``app.create_app()``.

Typical invocations:

- Docker CMD: ``uvicorn src.main:app --host 0.0.0.0 --port 8000``
- Local reload (from ``services/gateway``): ``uvicorn src.main:app --reload``

Importing this module has the side effect of constructing the global ``app``
singleton via ``app.py`` (middleware, routers, and lifespan hooks attached).
No HTTP server is started until uvicorn (or another ASGI server) binds to
``app``. Failure to import usually means missing editable install of the repo
(``pip install -e .``) or unreachable package paths for ``packages.*``.
"""

# Import the fully configured FastAPI application from the factory module.
# ``app`` is already created at import time in app.py (create_app() + assignment).
from .app import app

# Public re-export list used by star-imports and documentation tools; uvicorn
# only needs the ``app`` attribute but __all__ documents the intentional API.
__all__ = ["app"]
