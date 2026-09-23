"""
Shared configuration for all agent_fleet services.

████  SINGLE SOURCE OF TRUTH  ████

Ports, hostnames, credentials, and service URLs are read from
``config/platform.yaml``. An environment variable overrides the matching
host value when a process was given one. This module does not invent
a port, host, password, or bucket when both are missing.

This module is the configuration plane for the fleet control plane: gRPC
fleet-manager address, HTTP gateway, telemetry HTTP/gRPC ports, Postgres
DSN pieces, NATS URL, shared memory-plane backends (Cassandra, MinIO/S3,
OpenSearch, ClickHouse, Vault, git working tree), plan-workspace storage,
and telemetry blob/parquet roots. Comment density here is intentional —
every assignment is a contract other packages import by name.
"""

# Environment overrides for processes Compose already configured.
import os
# Path is used so repo-relative directories resolve regardless of cwd.
from pathlib import Path

# Host view of config/platform.yaml. Environment variables override when set.
from packages.platform_config import load_platform, setting

# =============================================================================
# Path Configuration
# =============================================================================

# Resolve the repository root (parent of packages/).
REPO_ROOT = Path(__file__).parent.parent.resolve()

# Directory that holds agent implementations. Domain packages live underneath.
AGENTS_DIR = REPO_ROOT / "agents"
# Roots the agent loader walks when discovering config.yaml files.
AGENT_PACKAGE_DIRS = (AGENTS_DIR,)

# Where planner strategy type modules live under fleet_server.
PLANNER_TYPES_DIR = REPO_ROOT / "services" / "fleet_server" / "src" / "planners" / "types"
# Where allocator strategy type modules live under fleet_server.
ALLOCATOR_TYPES_DIR = REPO_ROOT / "services" / "fleet_server" / "src" / "allocators" / "types"

# =============================================================================
# Database
# =============================================================================

# Postgres role. Environment overrides config/platform.yaml.
DB_USER = setting("DB_USER")
# Postgres password from config/platform.yaml unless the environment sets it.
DB_PASSWORD = setting("DB_PASSWORD")
# Logical database name for the fleet control plane.
DB_NAME = setting("DB_NAME")
# Hostname of Postgres as seen from this process.
DB_HOST = setting("DB_HOST")
# Postgres port published to this process.
DB_PORT = int(setting("DB_PORT"))

# Full SQLAlchemy/asyncpg URL from config/platform.yaml or DATABASE_URL.
DATABASE_URL = setting("DATABASE_URL")

# =============================================================================
# Service Ports  (one place — grep "PORT" here, not across 30 files)
# =============================================================================

# Fleet Manager gRPC listen port. GRPC_PORT remains an accepted override name.
GRPC_SERVER_PORT = int(os.environ.get("GRPC_PORT") or setting("GRPC_SERVER_PORT"))
# HTTP Gateway / BFF listen port.
GATEWAY_PORT = int(setting("GATEWAY_PORT"))
# Telemetry HTTP ingest / query service port.
TELEMETRY_PORT = int(setting("TELEMETRY_PORT"))
# Vite dashboard port from config/platform.yaml startup.dashboard_port.
FRONTEND_DEV_PORT = int(setting("FRONTEND_DEV_PORT"))

# =============================================================================
# Service Hosts
# =============================================================================

# Host part of the fleet-manager gRPC target.
GRPC_SERVER_HOST = setting("GRPC_SERVER_HOST")
# Host part of the gateway base URL.
GATEWAY_HOST = setting("GATEWAY_HOST")
# Host part of the telemetry HTTP base URL.
TELEMETRY_HOST = setting("TELEMETRY_HOST")

# Host agents register with when the environment does not override it.
DEFAULT_AGENT_HOST = setting("DEFAULT_AGENT_HOST")

# =============================================================================
# Derived URLs  (built from host + port above)
# =============================================================================

# host:port string passed to grpc.aio insecure channels.
GRPC_SERVER_ADDRESS = setting("GRPC_SERVER_ADDRESS")

# Base HTTP URL for the Gateway BFF.
GATEWAY_URL = setting("GATEWAY_URL")

# Internal webhook the control plane posts events into on the gateway.
GATEWAY_EVENT_URL = setting("GATEWAY_EVENT_URL")

# Base HTTP URL for the telemetry service.
TELEMETRY_URL = setting("TELEMETRY_URL")

# =============================================================================
# Agent Defaults
# =============================================================================

# First port assigned when auto-allocating agent HTTP task servers.
DEFAULT_AGENT_BASE_PORT = int(setting("DEFAULT_AGENT_BASE_PORT"))

# =============================================================================
# Health / Heartbeat Tuning
# =============================================================================

# Seconds to wait on a single agent health probe before calling it unreachable.
HEALTH_CHECK_TIMEOUT_SECS = float(setting("HEALTH_CHECK_TIMEOUT_SECS"))

# How often an agent should POST heartbeats to the control plane.
AGENT_HEARTBEAT_INTERVAL_SECS = float(setting("HEARTBEAT_INTERVAL"))

# Number of consecutive missed heartbeats tolerated before marking unreachable.
HEARTBEAT_MISS_TOLERANCE = int(setting("HEARTBEAT_MISS_TOLERANCE"))

# Age threshold: interval * misses + slack; beyond this an agent is stale.
HEARTBEAT_REACHABLE_THRESHOLD_SECS = (
    AGENT_HEARTBEAT_INTERVAL_SECS * HEARTBEAT_MISS_TOLERANCE
    + float(setting("HEARTBEAT_SLACK_SECONDS"))
)

# How often the fleet scanner reaps stale heartbeats.
HEARTBEAT_SCANNER_INTERVAL_SECS = float(setting("HEARTBEAT_SCANNER_INTERVAL_SECS"))

# Cap on retained heartbeat samples per agent (ring-buffer style).
MAX_HEARTBEATS_PER_AGENT = int(setting("MAX_HEARTBEATS_PER_AGENT"))

# =============================================================================
# NATS / Message Bus
# =============================================================================

# NATS server URL for JetStream telemetry and memory events.
NATS_URL = setting("NATS_URL")

# =============================================================================
# Shared memory plane
# Postgres is the transactional store and the pgvector index.
# The other URLs are the stores named in the physical-storage table.
# =============================================================================

# Which primary MemoryStore adapter to construct when the environment is unset.
MEMORY_BACKEND = setting("MEMORY_BACKEND")
# Comma-separated Cassandra contact points for journals and KV lookups.
MEMORY_CASSANDRA_HOSTS = setting("MEMORY_CASSANDRA_HOSTS")
# Cassandra native protocol port.
MEMORY_CASSANDRA_PORT = int(setting("MEMORY_CASSANDRA_PORT"))
# MinIO / S3-compatible endpoint for large memory artifacts.
MEMORY_S3_ENDPOINT = setting("MEMORY_S3_ENDPOINT")
# Bucket name used by MemoryPlane object placement.
MEMORY_S3_BUCKET = setting("MEMORY_S3_BUCKET")
# Access key for the object store.
MEMORY_S3_ACCESS_KEY = setting("MEMORY_S3_ACCESS_KEY")
# Secret key for the object store.
MEMORY_S3_SECRET_KEY = setting("MEMORY_S3_SECRET_KEY")
# OpenSearch base URL for full-text memory indexing.
MEMORY_OPENSEARCH_URL = setting("MEMORY_OPENSEARCH_URL")
# ClickHouse HTTP interface for measurement rows.
MEMORY_CLICKHOUSE_URL = setting("MEMORY_CLICKHOUSE_URL")
# ClickHouse database holding the measurement table.
MEMORY_CLICKHOUSE_DATABASE = setting("MEMORY_CLICKHOUSE_DATABASE")
# ClickHouse auth user.
MEMORY_CLICKHOUSE_USER = setting("MEMORY_CLICKHOUSE_USER")
# ClickHouse auth password.
MEMORY_CLICKHOUSE_PASSWORD = setting("MEMORY_CLICKHOUSE_PASSWORD")
# HashiCorp Vault address for secret placement (never written elsewhere).
MEMORY_VAULT_ADDR = setting("MEMORY_VAULT_ADDR")
# Vault token.
MEMORY_VAULT_TOKEN = setting("MEMORY_VAULT_TOKEN")
# Working tree where GIT placement commits source artifacts.
MEMORY_GIT_DIR = setting("MEMORY_GIT_DIR")
# NATS URL specifically for memory event projection.
MEMORY_NATS_URL = setting("MEMORY_NATS_URL")

# =============================================================================
# Plan Workspace Storage
# =============================================================================

# Backend for plan workspaces: local filesystem or S3.
WORKSPACE_STORAGE_BACKEND = setting("WORKSPACE_STORAGE_BACKEND")
# Root directory when using the local workspace backend.
WORKSPACE_STORAGE_ROOT = setting("WORKSPACE_STORAGE_ROOT")
# S3 bucket for workspaces when backend is s3.
WORKSPACE_S3_BUCKET = os.environ.get("WORKSPACE_S3_BUCKET") or setting("S3_BUCKET")

# =============================================================================
# Telemetry Storage
# =============================================================================

# Where vision/blob payloads land: local disk or S3.
BLOB_STORAGE_BACKEND = setting("BLOB_STORAGE_BACKEND")
# Local root for telemetry blob files when backend is local.
BLOB_STORAGE_ROOT = setting("BLOB_STORAGE_ROOT")
# Local root for Parquet trajectory partitions.
PARQUET_STORAGE_ROOT = setting("PARQUET_STORAGE_ROOT")

# Shared S3 bucket name used by telemetry and optionally workspaces.
S3_BUCKET = setting("S3_BUCKET")
# Region for S3 clients.
S3_REGION = setting("S3_REGION")

# TelemetryIngestion gRPC listen port (see packages/proto/telemetry.proto).
TELEMETRY_GRPC_PORT = int(setting("TELEMETRY_GRPC_PORT"))

# =============================================================================
# CORS Configuration
# =============================================================================

# Origins the gateway allows for browser clients.
_PLATFORM = load_platform()
CORS_ORIGINS = [
    f"{_PLATFORM['http_scheme']}://{_PLATFORM['process_host']}:{FRONTEND_DEV_PORT}",
    *[str(origin) for origin in _PLATFORM["cors_extra_origins"]],
]
