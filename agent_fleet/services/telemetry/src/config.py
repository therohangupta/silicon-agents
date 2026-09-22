"""
Telemetry service configuration re-exports.

All tunables for this service live in ``packages.config`` (single source of
truth for env defaults across fleet_server, gateway, telemetry, and storage
writer). This module only re-exports the subset telemetry code imports so
call sites can write ``from .config import TELEMETRY_PORT`` without coupling
every file to the full shared config surface.

Keeping a local ``config`` module also preserves backward compatibility for
older import paths and documents which settings the telemetry process
actually consumes (CORS, gateway event URL, ports, NATS, blob backends,
heartbeat ring size, reachability threshold, and scanner interval).
"""

# Import the shared knobs telemetry needs; names stay identical to packages.config.
from packages.config import (
    CORS_ORIGINS,  # Allowed browser origins for FastAPI CORSMiddleware.
    GATEWAY_EVENT_URL,  # HTTP target for health_changed fan-out.
    TELEMETRY_PORT,  # Default HTTP listen port for uvicorn / __main__.
    TELEMETRY_GRPC_PORT,  # Separate port for TelemetryIngestion gRPC.
    NATS_URL,  # JetStream URL for telemetry.> publish.
    BLOB_STORAGE_BACKEND,  # "local" vs "s3" blob writer selection.
    BLOB_STORAGE_ROOT,  # Filesystem root when backend is local.
    S3_BUCKET,  # Destination bucket when backend is s3.
    S3_REGION,  # AWS region for the S3 client.
    MAX_HEARTBEATS_PER_AGENT,  # Ring-buffer maxlen per agent_id.
    HEARTBEAT_REACHABLE_THRESHOLD_SECS,  # Age after which reachable becomes false.
    HEARTBEAT_SCANNER_INTERVAL_SECS,  # Background timeout scanner sleep.
)
