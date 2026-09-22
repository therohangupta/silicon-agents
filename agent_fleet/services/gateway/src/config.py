"""
Gateway configuration re-exports.

Gateway routers and services prefer ``from ..config import X`` (or
``from .config import X``) rather than reaching into ``packages.config``
directly. That keeps import paths stable if the shared config package moves,
and makes gateway-local dependencies obvious when grepping this tree.

Every name below is defined in ``packages.config`` and driven by environment
variables / defaults at process start. This module does not mutate settings;
it only re-exports symbols for convenience.

Imported settings cover: repository layout (``REPO_ROOT``, agent/planner/
allocator dirs), fleet gRPC address pieces, Postgres ``DATABASE_URL``,
Telemetry base URL, NATS URL, blob storage backend/root, default agent host
and base port, health-check timeout, and CORS allow-list origins used by the
FastAPI CORS middleware in ``app.py``.
"""

# Re-export shared configuration symbols so gateway code stays decoupled from
# the physical location of packages.config while preserving identical values.
from packages.config import (
    REPO_ROOT,                 # Absolute path to the agent_fleet / repo root for YAML resolution
    AGENT_PACKAGE_DIRS,        # Roots scanned for agents/**/config.yaml embodiments
    PLANNER_TYPES_DIR,         # Directory of planner method packages (summary.yaml + prompts)
    ALLOCATOR_TYPES_DIR,       # Directory of allocator method packages
    GRPC_SERVER_ADDRESS,       # Full host:port string for the fleet manager (preferred)
    GRPC_SERVER_HOST,          # Host fallback when address has no port component
    GRPC_SERVER_PORT,          # Port fallback / default when parsing address
    DATABASE_URL,              # SQLAlchemy URL for AgentInstanceRegistry plan/task extras
    TELEMETRY_URL,             # Base URL of the Telemetry HTTP service (health proxy)
    NATS_URL,                  # NATS JetStream URL for realtime telemetry consumer
    BLOB_STORAGE_BACKEND,      # Backend selector for telemetry blobs (local vs S3, etc.)
    BLOB_STORAGE_ROOT,         # Filesystem root when serving local blob URIs
    DEFAULT_AGENT_BASE_PORT,   # Default task-server port for new agent instances
    DEFAULT_AGENT_HOST,        # Default task-server host (often localhost)
    HEALTH_CHECK_TIMEOUT_SECS, # httpx timeout for direct agent /health pings
    CORS_ORIGINS,              # Allowed browser origins for CORSMiddleware
)
