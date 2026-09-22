"""Load ``config/platform.yaml``.

That file is the only authored copy of platform ports, credentials, and service
locations. Callers receive those values or ``PlatformConfigError``. This module
does not substitute its own ports, hosts, or passwords.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PLATFORM_PATH = PACKAGE_ROOT / "config" / "platform.yaml"


class optional_str:
    """Schema marker for a string that may be empty."""


_REQUIRED: dict[str, Any] = {
    "process_host": str,
    "http_scheme": str,
    "ws_scheme": str,
    "nats_scheme": str,
    "process": {
        "memory_backend": str,
        "memory_root": str,
        "agent_base_port": int,
    },
    "heartbeat": {
        "health_check_timeout_seconds": float,
        "interval_seconds": float,
        "miss_tolerance": int,
        "scanner_interval_seconds": float,
        "slack_seconds": float,
        "max_per_agent": int,
        "agent_interval_seconds": float,
    },
    "storage": {
        "workspace_backend": str,
        "workspace_relative_root": str,
        "blob_backend": str,
        "blob_relative_root": str,
        "parquet_relative_root": str,
        "s3_bucket": optional_str,
        "s3_region": str,
    },
    "cors_extra_origins": [str],
    "startup": {
        "platform_wait_timeout_seconds": int,
        "agent_health_timeout_seconds": int,
        "dashboard_port": int,
        "dashboard_ready_attempts": int,
    },
    "postgres": {
        "user": str,
        "password_env": str,
        "database": str,
        "container_host": str,
        "container_port": int,
        "published_host_port": int,
        "container_scheme": str,
        "process_scheme": str,
    },
    "nats": {
        "container_host": str,
        "client_port": int,
        "monitoring_port": int,
        "published_client_port": int,
        "published_monitoring_port": int,
    },
    "cassandra": {
        "container_host": str,
        "cluster_name": str,
        "container_port": int,
        "published_host_port": int,
    },
    "minio": {
        "container_host": str,
        "access_key": str,
        "secret_key_env": str,
        "bucket": str,
        "api_container_port": int,
        "console_container_port": int,
        "published_api_port": int,
        "published_console_port": int,
    },
    "clickhouse": {
        "container_host": str,
        "user": str,
        "password_env": str,
        "database": str,
        "container_port": int,
        "published_host_port": int,
    },
    "opensearch": {
        "container_host": str,
        "container_port": int,
        "published_host_port": int,
    },
    "vault": {
        "container_host": str,
        "token_env": str,
        "container_port": int,
        "published_host_port": int,
    },
    "git": {
        "container_dir": str,
        "host_relative_dir": str,
        "host_mount": str,
        "container_port": int,
        "published_host_port": int,
    },
    "gateway": {
        "container_host": str,
        "container_port": int,
        "published_host_port": int,
        "event_path": str,
    },
    "fleet_server": {
        "container_host": str,
        "container_port": int,
        "published_host_port": int,
        "default_agent_host": str,
    },
    "telemetry": {
        "container_host": str,
        "http_port": int,
        "grpc_port": int,
        "published_http_port": int,
        "published_grpc_port": int,
        "blob_root": str,
        "parquet_root": str,
    },
    "agent_compose": {
        "project": str,
        "image": str,
        "dockerfile": str,
        "build_context": str,
        "command": [str],
        "restart": str,
        "network": str,
        "external_network": str,
        "working_dir_prefix": str,
        "memory_backend": str,
        "host_port_collision_offset": int,
    },
}


class PlatformConfigError(RuntimeError):
    """Raised when ``config/platform.yaml`` is missing or incomplete."""


_CACHE: dict[str, Any] | None = None


def load_platform() -> dict[str, Any]:
    """Return the platform document. Missing keys raise."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not PLATFORM_PATH.is_file():
        raise PlatformConfigError(f"Platform config not found: {PLATFORM_PATH}")
    document = yaml.safe_load(PLATFORM_PATH.read_text())
    if not isinstance(document, dict):
        raise PlatformConfigError(f"{PLATFORM_PATH} must be a mapping")
    _check(document, _REQUIRED, str(PLATFORM_PATH))
    _CACHE = document
    return document


def published_host_ports(document: dict[str, Any] | None = None) -> set[int]:
    """Every ``published_*`` integer in the platform document."""
    found: set[int] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).startswith("published_") and isinstance(value, int):
                    found.add(value)
                else:
                    walk(value)

    walk(document if document is not None else load_platform())
    if not found:
        raise PlatformConfigError(f"{PLATFORM_PATH} declares no published_ host ports")
    return found


def _compose_secret(environment_name: str) -> str:
    """Return a Compose-only secret placeholder, never the secret itself."""
    return f"${{{environment_name}:?set {environment_name} in the repository .env}}"


def _secret(environment_name: str) -> str:
    """Read a required secret supplied by the process environment."""
    value = os.environ.get(environment_name)
    if not value:
        raise PlatformConfigError(
            f"{environment_name} is required in the process environment; "
            "define it in the repository .env for Compose or inject it in deployment"
        )
    return value


def agent_environment(document: dict[str, Any] | None = None) -> dict[str, str]:
    """Environment injected into agent containers. Hosts are Compose DNS names."""
    doc = document if document is not None else load_platform()
    postgres = doc["postgres"]
    database_url = _url(
        postgres["container_scheme"],
        postgres["user"],
        _compose_secret(postgres["password_env"]),
        postgres["container_host"],
        postgres["container_port"],
        postgres["database"],
    )
    return {
        "MEMORY_BACKEND": str(doc["agent_compose"]["memory_backend"]),
        "DATABASE_URL": database_url,
        "MEMORY_DATABASE_URL": database_url,
        "MEMORY_CASSANDRA_HOSTS": str(doc["cassandra"]["container_host"]),
        "MEMORY_CASSANDRA_PORT": str(doc["cassandra"]["container_port"]),
        "MEMORY_S3_ENDPOINT": _origin(
            doc["http_scheme"], doc["minio"]["container_host"], doc["minio"]["api_container_port"]
        ),
        "MEMORY_S3_ACCESS_KEY": str(doc["minio"]["access_key"]),
        "MEMORY_S3_SECRET_KEY": _compose_secret(doc["minio"]["secret_key_env"]),
        "MEMORY_S3_BUCKET": str(doc["minio"]["bucket"]),
        "MEMORY_OPENSEARCH_URL": _origin(
            doc["http_scheme"], doc["opensearch"]["container_host"], doc["opensearch"]["container_port"]
        ),
        "MEMORY_CLICKHOUSE_URL": _origin(
            doc["http_scheme"], doc["clickhouse"]["container_host"], doc["clickhouse"]["container_port"]
        ),
        "MEMORY_CLICKHOUSE_USER": str(doc["clickhouse"]["user"]),
        "MEMORY_CLICKHOUSE_PASSWORD": _compose_secret(doc["clickhouse"]["password_env"]),
        "MEMORY_CLICKHOUSE_DATABASE": str(doc["clickhouse"]["database"]),
        "MEMORY_VAULT_ADDR": _origin(
            doc["http_scheme"], doc["vault"]["container_host"], doc["vault"]["container_port"]
        ),
        "MEMORY_VAULT_TOKEN": _compose_secret(doc["vault"]["token_env"]),
        "MEMORY_GIT_DIR": str(doc["git"]["container_dir"]),
        "MEMORY_NATS_URL": _origin(
            doc["nats_scheme"], doc["nats"]["container_host"], doc["nats"]["client_port"]
        ),
        "NATS_URL": _origin(
            doc["nats_scheme"], doc["nats"]["container_host"], doc["nats"]["client_port"]
        ),
        "TELEMETRY_URL": _origin(
            doc["http_scheme"], doc["telemetry"]["container_host"], doc["telemetry"]["http_port"]
        ),
        "TELEMETRY_GRPC_PORT": str(doc["telemetry"]["grpc_port"]),
        "TELEMETRY_GRPC_TARGET": (
            f"{doc['telemetry']['container_host']}:{doc['telemetry']['grpc_port']}"
        ),
    }


def host_settings(document: dict[str, Any] | None = None) -> dict[str, str]:
    """Values a process on the host uses when the matching environment variable is unset."""
    doc = document if document is not None else load_platform()
    host = str(doc["process_host"])
    postgres = doc["postgres"]
    process_database = _url(
        postgres["process_scheme"],
        postgres["user"],
        _secret(postgres["password_env"]),
        host,
        postgres["published_host_port"],
        postgres["database"],
    )
    container_database = _url(
        postgres["container_scheme"],
        postgres["user"],
        _secret(postgres["password_env"]),
        host,
        postgres["published_host_port"],
        postgres["database"],
    )
    gateway = doc["gateway"]
    fleet_server = doc["fleet_server"]
    telemetry = doc["telemetry"]
    gateway_url = _origin(doc["http_scheme"], host, gateway["published_host_port"])
    event_path = str(gateway["event_path"])
    if not event_path.startswith("/"):
        raise PlatformConfigError("gateway.event_path must start with /")
    return {
        "DB_USER": str(postgres["user"]),
        "DB_PASSWORD": _secret(postgres["password_env"]),
        "DB_NAME": str(postgres["database"]),
        "DB_HOST": host,
        "DB_PORT": str(postgres["published_host_port"]),
        "DATABASE_URL": process_database,
        "GRPC_SERVER_PORT": str(fleet_server["published_host_port"]),
        "GATEWAY_PORT": str(gateway["published_host_port"]),
        "TELEMETRY_PORT": str(telemetry["published_http_port"]),
        "FRONTEND_DEV_PORT": str(doc["startup"]["dashboard_port"]),
        "GRPC_SERVER_HOST": host,
        "GATEWAY_HOST": host,
        "TELEMETRY_HOST": host,
        "DEFAULT_AGENT_HOST": host,
        "GRPC_SERVER_ADDRESS": f"{host}:{fleet_server['published_host_port']}",
        "GATEWAY_URL": gateway_url,
        "GATEWAY_WS_URL": _origin(doc["ws_scheme"], host, gateway["published_host_port"]),
        "GATEWAY_EVENT_URL": f"{gateway_url}{event_path}",
        "TELEMETRY_URL": _origin(doc["http_scheme"], host, telemetry["published_http_port"]),
        "DEFAULT_AGENT_BASE_PORT": str(doc["process"]["agent_base_port"]),
        "NATS_URL": _origin(doc["nats_scheme"], host, doc["nats"]["published_client_port"]),
        "MEMORY_BACKEND": str(doc["process"]["memory_backend"]),
        "MEMORY_ROOT": str(doc["process"]["memory_root"]),
        "MEMORY_CASSANDRA_HOSTS": host,
        "MEMORY_CASSANDRA_PORT": str(doc["cassandra"]["published_host_port"]),
        "MEMORY_S3_ENDPOINT": _origin(doc["http_scheme"], host, doc["minio"]["published_api_port"]),
        "MEMORY_S3_BUCKET": str(doc["minio"]["bucket"]),
        "MEMORY_S3_ACCESS_KEY": str(doc["minio"]["access_key"]),
        "MEMORY_S3_SECRET_KEY": _secret(doc["minio"]["secret_key_env"]),
        "MEMORY_OPENSEARCH_URL": _origin(
            doc["http_scheme"], host, doc["opensearch"]["published_host_port"]
        ),
        "MEMORY_CLICKHOUSE_URL": _origin(
            doc["http_scheme"], host, doc["clickhouse"]["published_host_port"]
        ),
        "MEMORY_CLICKHOUSE_DATABASE": str(doc["clickhouse"]["database"]),
        "MEMORY_CLICKHOUSE_USER": str(doc["clickhouse"]["user"]),
        "MEMORY_CLICKHOUSE_PASSWORD": _secret(doc["clickhouse"]["password_env"]),
        "MEMORY_VAULT_ADDR": _origin(doc["http_scheme"], host, doc["vault"]["published_host_port"]),
        "MEMORY_VAULT_TOKEN": _secret(doc["vault"]["token_env"]),
        "MEMORY_GIT_DIR": str(PACKAGE_ROOT / str(doc["git"]["host_relative_dir"])),
        "MEMORY_NATS_URL": _origin(doc["nats_scheme"], host, doc["nats"]["published_client_port"]),
        "MEMORY_DATABASE_URL": container_database,
        "TELEMETRY_GRPC_PORT": str(telemetry["published_grpc_port"]),
        "HEALTH_CHECK_TIMEOUT_SECS": str(doc["heartbeat"]["health_check_timeout_seconds"]),
        "HEARTBEAT_INTERVAL": str(doc["heartbeat"]["interval_seconds"]),
        "HEARTBEAT_MISS_TOLERANCE": str(doc["heartbeat"]["miss_tolerance"]),
        "HEARTBEAT_SCANNER_INTERVAL_SECS": str(doc["heartbeat"]["scanner_interval_seconds"]),
        "HEARTBEAT_SLACK_SECONDS": str(doc["heartbeat"]["slack_seconds"]),
        "MAX_HEARTBEATS_PER_AGENT": str(doc["heartbeat"]["max_per_agent"]),
        "AGENT_HEARTBEAT_INTERVAL_SECS": str(doc["heartbeat"]["agent_interval_seconds"]),
        "WORKSPACE_STORAGE_BACKEND": str(doc["storage"]["workspace_backend"]),
        "WORKSPACE_STORAGE_ROOT": str(PACKAGE_ROOT / str(doc["storage"]["workspace_relative_root"])),
        "BLOB_STORAGE_BACKEND": str(doc["storage"]["blob_backend"]),
        "BLOB_STORAGE_ROOT": str(PACKAGE_ROOT / str(doc["storage"]["blob_relative_root"])),
        "PARQUET_STORAGE_ROOT": str(PACKAGE_ROOT / str(doc["storage"]["parquet_relative_root"])),
        "S3_BUCKET": str(doc["storage"]["s3_bucket"]),
        "S3_REGION": str(doc["storage"]["s3_region"]),
    }


def compose_values(document: dict[str, Any] | None = None) -> dict[str, str]:
    """Values substituted into the generated Compose manifest.

    This is renderer input only. It is never written to a project ``.env``
    file: the repository-level ``.env`` is reserved for operator secrets.
    """
    doc = document if document is not None else load_platform()
    postgres = doc["postgres"]
    gateway = doc["gateway"]
    fleet_server = doc["fleet_server"]
    telemetry = doc["telemetry"]
    nats = doc["nats"]
    fleet_database = _url(
        postgres["process_scheme"],
        postgres["user"],
        _compose_secret(postgres["password_env"]),
        postgres["container_host"],
        postgres["container_port"],
        postgres["database"],
    )
    gateway_origin = _origin(doc["http_scheme"], gateway["container_host"], gateway["container_port"])
    event_path = str(gateway["event_path"])
    return {
        "POSTGRES_USER": str(postgres["user"]),
        "POSTGRES_PASSWORD": _compose_secret(postgres["password_env"]),
        "POSTGRES_DB": str(postgres["database"]),
        "POSTGRES_PUBLISHED_PORT": str(postgres["published_host_port"]),
        "POSTGRES_CONTAINER_PORT": str(postgres["container_port"]),
        "FLEET_DATABASE_URL": fleet_database,
        "GATEWAY_EVENT_URL": f"{gateway_origin}{event_path}",
        "DEFAULT_AGENT_HOST": str(fleet_server["default_agent_host"]),
        "GRPC_PUBLISHED_PORT": str(fleet_server["published_host_port"]),
        "GRPC_CONTAINER_PORT": str(fleet_server["container_port"]),
        "GRPC_SERVER_ADDRESS": f"{fleet_server['container_host']}:{fleet_server['container_port']}",
        "NATS_CLIENT_PORT": str(nats["client_port"]),
        "NATS_MONITORING_PORT": str(nats["monitoring_port"]),
        "NATS_PUBLISHED_CLIENT_PORT": str(nats["published_client_port"]),
        "NATS_PUBLISHED_MONITORING_PORT": str(nats["published_monitoring_port"]),
        "NATS_CONTAINER_URL": _origin(doc["nats_scheme"], nats["container_host"], nats["client_port"]),
        "TELEMETRY_HTTP_PORT": str(telemetry["http_port"]),
        "TELEMETRY_GRPC_PORT": str(telemetry["grpc_port"]),
        "TELEMETRY_PUBLISHED_HTTP_PORT": str(telemetry["published_http_port"]),
        "TELEMETRY_PUBLISHED_GRPC_PORT": str(telemetry["published_grpc_port"]),
        "TELEMETRY_CONTAINER_URL": _origin(
            doc["http_scheme"], telemetry["container_host"], telemetry["http_port"]
        ),
        "BLOB_STORAGE_ROOT": str(telemetry["blob_root"]),
        "PARQUET_STORAGE_ROOT": str(telemetry["parquet_root"]),
        "GATEWAY_CONTAINER_PORT": str(gateway["container_port"]),
        "GATEWAY_PUBLISHED_PORT": str(gateway["published_host_port"]),
        "CASSANDRA_CLUSTER_NAME": str(doc["cassandra"]["cluster_name"]),
        "CASSANDRA_PUBLISHED_PORT": str(doc["cassandra"]["published_host_port"]),
        "CASSANDRA_CONTAINER_PORT": str(doc["cassandra"]["container_port"]),
        "MINIO_ROOT_USER": str(doc["minio"]["access_key"]),
        "MINIO_ROOT_PASSWORD": _compose_secret(doc["minio"]["secret_key_env"]),
        "MINIO_API_CONTAINER_PORT": str(doc["minio"]["api_container_port"]),
        "MINIO_CONSOLE_CONTAINER_PORT": str(doc["minio"]["console_container_port"]),
        "MINIO_PUBLISHED_API_PORT": str(doc["minio"]["published_api_port"]),
        "MINIO_PUBLISHED_CONSOLE_PORT": str(doc["minio"]["published_console_port"]),
        "CLICKHOUSE_USER": str(doc["clickhouse"]["user"]),
        "CLICKHOUSE_PASSWORD": _compose_secret(doc["clickhouse"]["password_env"]),
        "CLICKHOUSE_DB": str(doc["clickhouse"]["database"]),
        "CLICKHOUSE_CONTAINER_PORT": str(doc["clickhouse"]["container_port"]),
        "CLICKHOUSE_PUBLISHED_PORT": str(doc["clickhouse"]["published_host_port"]),
        "OPENSEARCH_PUBLISHED_PORT": str(doc["opensearch"]["published_host_port"]),
        "OPENSEARCH_CONTAINER_PORT": str(doc["opensearch"]["container_port"]),
        "VAULT_DEV_ROOT_TOKEN_ID": _compose_secret(doc["vault"]["token_env"]),
        "VAULT_CONTAINER_PORT": str(doc["vault"]["container_port"]),
        "VAULT_PUBLISHED_PORT": str(doc["vault"]["published_host_port"]),
        "GIT_HOST_MOUNT": str(doc["git"]["host_mount"]),
        "GIT_CONTAINER_PORT": str(doc["git"]["container_port"]),
        "GIT_PUBLISHED_PORT": str(doc["git"]["published_host_port"]),
        "PLATFORM_NETWORK": str(doc["agent_compose"]["external_network"]),
        "AGENT_COMPOSE_PROJECT": str(doc["agent_compose"]["project"]),
        "AGENT_IMAGE": str(doc["agent_compose"]["image"]),
        "PLATFORM_WAIT_TIMEOUT": str(doc["startup"]["platform_wait_timeout_seconds"]),
        "AGENT_HEALTH_TIMEOUT": str(doc["startup"]["agent_health_timeout_seconds"]),
        "DASHBOARD_HOST": str(doc["process_host"]),
        "DASHBOARD_PORT": str(doc["startup"]["dashboard_port"]),
        "DASHBOARD_READY_ATTEMPTS": str(doc["startup"]["dashboard_ready_attempts"]),
        "PROCESS_HOST": str(doc["process_host"]),
    }


def render_compose_template(template: Path, output: Path) -> Path:
    """Render a Compose template from ``config/platform.yaml``.

    The template may use only ``${NAME:?config/platform.yaml}`` placeholders.
    Rendering rejects a missing value and rejects any unresolved placeholder,
    yielding a complete deployment manifest that Docker can consume without a
    generated ``.env`` file.
    """
    import re

    values = compose_values()
    marker = re.compile(r"\$\{([A-Z][A-Z0-9_]*):\?config/platform\.yaml\}")

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        try:
            value = values[name]
        except KeyError as exc:
            raise PlatformConfigError(
                f"{name} is referenced by {template} but not produced from {PLATFORM_PATH}"
            ) from exc
        if not value or any(character in value for character in "\n\r"):
            raise PlatformConfigError(f"Invalid rendered value for {name}")
        return value

    rendered = marker.sub(replace, template.read_text())
    if marker.search(rendered):
        raise PlatformConfigError(f"Unresolved platform placeholder in {template}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered)
    return output


def shell_exports(document: dict[str, Any] | None = None) -> str:
    """Return safe Bash exports for startup-only values from platform YAML."""
    import shlex

    values = compose_values(document)
    return "".join(f"export {key}={shlex.quote(value)}\n" for key, value in values.items())


def setting(name: str) -> str:
    """Environment variable if set, otherwise the host value from ``config/platform.yaml``."""
    raw = os.environ.get(name)
    if raw:
        return raw
    values = host_settings()
    if name not in values:
        raise PlatformConfigError(
            f"{name} is not in {PLATFORM_PATH} and is not set in the environment"
        )
    return values[name]


def _url(scheme: str, user: str, password: str, host: str, port: int, database: str) -> str:
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def _origin(scheme: str, host: str, port: int) -> str:
    return f"{scheme}://{host}:{port}"


def _check(document: object, spec: object, where: str) -> None:
    if isinstance(spec, dict):
        if not isinstance(document, dict):
            raise PlatformConfigError(f"{where} must be a mapping")
        missing = sorted(set(spec) - set(document))
        if missing:
            raise PlatformConfigError(f"{where} is missing {missing[0]}")
        for key, child in spec.items():
            _check(document[key], child, f"{where}.{key}")
        return
    if isinstance(spec, list):
        if not isinstance(document, list) or not document:
            raise PlatformConfigError(f"{where} must be a non-empty list")
        item_spec = spec[0]
        for index, item in enumerate(document):
            _check(item, item_spec, f"{where}[{index}]")
        return
    if spec is int:
        if isinstance(document, bool) or not isinstance(document, int):
            raise PlatformConfigError(f"{where} must be an integer")
        return
    if spec is str:
        if not isinstance(document, str) or not document.strip():
            raise PlatformConfigError(f"{where} must be a non-empty string")
        return
    if spec is optional_str:
        if not isinstance(document, str):
            raise PlatformConfigError(f"{where} must be a string")
        return
    if spec is float:
        if isinstance(document, bool) or not isinstance(document, (int, float)):
            raise PlatformConfigError(f"{where} must be a number")
        return
    raise PlatformConfigError(f"Internal schema error at {where}")
