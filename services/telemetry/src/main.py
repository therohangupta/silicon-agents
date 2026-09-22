"""
Telemetry service entrypoint module for uvicorn.

Exposes the FastAPI ``app`` object constructed in ``app.py`` so process
managers can target ``services.telemetry.src.main:app`` (or
``src.main:app`` when cwd is this service tree). Prefer
``python -m services.telemetry.src`` when you want the argparse port wrapper
in ``__main__.py``; use this module when uvicorn (or Compose) already owns
host/port flags.

Re-exporting via ``__all__`` makes the public surface explicit for star
imports and static analyzers without pulling lifespan side effects beyond
what importing ``app`` already triggers.
"""

# The real application object (middleware, routers, lifespan) lives in app.py.
from .app import app

# Tell importers/tools that ``app`` is the only intentional public symbol.
__all__ = ["app"]
