"""One memory API over the stores in the design\'s physical-storage table.

A write policy chooses which payload reaches which store. Postgres holds the
envelope when the policy includes it, plus leases, approvals, canonical
pointers, and decisions. Cassandra holds journals and dictionary keys. Git
holds source. MinIO holds large artifacts. ClickHouse holds measurements.
OpenSearch holds full text. The pgvector index holds semantic pointers. NATS
JetStream holds the durable event. Vault holds secrets, which never enter the
other stores.

``MemoryPlane`` is the memory-plane façade used by domain EngineeringMemory
services in production. Envelope CRUD delegates to ``PostgresStore``; every
``apply_copies`` call fans out to the matching physical writer.
"""

from __future__ import annotations

# asyncio.to_thread offloads blocking Cassandra/S3/git drivers.
import asyncio
# json for ClickHouse rows, NATS payloads, and search document bodies.
import json
# os.environ for embedding endpoint and MEMORY_/MEMORY_ overrides.
import os
# subprocess drives git init/add/commit/push for GIT placement.
import subprocess
# timezone-aware timestamps for ClickHouse recorded_at.
from datetime import datetime, timezone
# Path for the git working tree and source reads.
from pathlib import Path
# Any/Optional for opaque envelopes and lazy clients.
from typing import Any, Optional

# Local hash embedding used when MEMORY_EMBEDDING_URL is unset.
from packages.memory.embed import embed_text
# Placement enum, StoreCopy model, and refresh helper for updates.
from packages.memory.policy import Placement, StoreCopy, refresh_copies
# Transactional envelope store underneath the plane.
from packages.memory.stores.postgres import PostgresStore
# Enum-to-string helper for Cassandra/OpenSearch/NATS labels.
from packages.memory.values import label


def _env(name: str) -> str:
    """Read MEMORY_* or the named variable, then ``config/platform.yaml``.

    There is no literal fallback. A missing name raises ``PlatformConfigError``.
    """
    from packages.platform_config import PlatformConfigError, host_settings

    raw = os.environ.get(name)
    if raw:
        return raw
    values = host_settings()
    if not values.get(name):
        raise PlatformConfigError(
            f"{name} is not set in the environment and is not in config/platform.yaml"
        )
    return values[name]


class MemoryPlane:
    """Primary store is Postgres. Every other system is a real projection.

    Callers treat this object like a MemoryStore for envelope CRUD, then call
    ``apply_copies`` with the validated ``StoreCopy`` list from
    ``assemble_copies`` to project into Cassandra, OpenSearch, vector,
    NATS, object storage, ClickHouse, git, and Vault.
    """

    def __init__(self, *, record_cls: type) -> None:
        # Domain envelope class for Cassandra KV rehydration.
        self._record_cls = record_cls
        # Always-on transactional store for envelopes and control tables.
        self.postgres = PostgresStore(record_cls=record_cls)
        # Cassandra contact points (comma-separated).
        self._cassandra_hosts = _env("MEMORY_CASSANDRA_HOSTS")
        # Cassandra native port.
        self._cassandra_port = int(_env("MEMORY_CASSANDRA_PORT"))
        # MinIO / S3 endpoint for OBJECT placement.
        self._s3_endpoint = _env("MEMORY_S3_ENDPOINT")
        # Bucket used for large artifacts.
        self._s3_bucket = _env("MEMORY_S3_BUCKET")
        # S3 access key.
        self._s3_key = _env("MEMORY_S3_ACCESS_KEY")
        # S3 secret key.
        self._s3_secret = _env("MEMORY_S3_SECRET_KEY")
        # OpenSearch base URL (trailing slash stripped for join safety).
        self._opensearch = _env("MEMORY_OPENSEARCH_URL").rstrip("/")
        # ClickHouse HTTP URL.
        self._clickhouse = _env("MEMORY_CLICKHOUSE_URL").rstrip("/")
        # ClickHouse database name.
        self._clickhouse_db = _env("MEMORY_CLICKHOUSE_DATABASE")
        # ClickHouse user.
        self._clickhouse_user = _env("MEMORY_CLICKHOUSE_USER")
        # ClickHouse password.
        self._clickhouse_password = _env("MEMORY_CLICKHOUSE_PASSWORD")
        # Vault address for secret placement.
        self._vault = _env("MEMORY_VAULT_ADDR").rstrip("/")
        # Vault token.
        self._vault_token = _env("MEMORY_VAULT_TOKEN")
        # Git working tree for source placement.
        self._git_dir = Path(_env("MEMORY_GIT_DIR"))
        # NATS URL for memory event stream.
        self._nats_url = _env("MEMORY_NATS_URL")
        # Lazy Cassandra session.
        self._cassandra: Any = None
        # Lazy boto3 S3 client.
        self._s3: Any = None
        # Lazy NATS client.
        self._nats: Any = None
        # Lazy JetStream context.
        self._js: Any = None
        # Whether the OpenSearch ``memory`` index mapping has been ensured.
        self._index_ready = False
        # Whether the ClickHouse measurement table has been ensured.
        self._clickhouse_ready = False
        # Serializes git commits across concurrent writers.
        self._git_lock = asyncio.Lock()

    async def insert(self, record: Any) -> None:
        """Persist the envelope to Postgres (projections via apply_copies)."""
        await self.postgres.insert(record)

    async def get(self, memory_id: str) -> Optional[Any]:
        """Load one envelope from Postgres by id."""
        return await self.postgres.get(memory_id)

    async def find_idempotency(self, key: str) -> Optional[Any]:
        """Resolve an idempotency key through Postgres."""
        return await self.postgres.find_idempotency(key)

    async def scan(self) -> list[Any]:
        """Scan every Postgres envelope."""
        return await self.postgres.scan()

    async def update(self, record: Any) -> None:
        """Update the Postgres envelope and refresh inherited projections."""
        await self.postgres.update(record)
        # Only inherited refreshable stores are rewritten on envelope change.
        refreshed = refresh_copies(record.copies)
        # Only when (refreshed).
        if refreshed:
            # Await ``self.apply_copies`` and continue once it completes.
            await self.apply_copies(record, refreshed)

    async def get_baseline(self, scope_path: str) -> Optional[str]:
        """Read the baseline pointer from Postgres."""
        return await self.postgres.get_baseline(scope_path)

    async def compare_and_set_baseline(self, scope_path: str, expected: Optional[str], new_value: str) -> bool:
        """CAS the baseline pointer in Postgres."""
        return await self.postgres.compare_and_set_baseline(scope_path, expected, new_value)

    async def search_text(self, *, project: str, query: str, scope: Any = None) -> list[Any]:
        """Full-text search via OpenSearch, then rehydrate envelopes from Postgres.

        Optional ``scope`` objects expose ``contains(record.scope)`` to filter
        hits to a domain scope tree after retrieval.
        """
        await self._ensure_search_index()
        import httpx

        # simple_query_string over summary/body/tags, filtered by project_id.
        body = {
            "size": 20,
            "query": {
                "bool": {
                    "must": [{"simple_query_string": {"query": query, "fields": ["summary", "body", "tags"]}}],
                    "filter": [{"term": {"project_id": project}}],
                }
            },
        }
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.post(f"{self._opensearch}/memory/_search", json=body….
            response = await client.post(f"{self._opensearch}/memory/_search", json=body)
            response.raise_for_status()
            # Local ``hits`` ← response.json().get("hits", {}).get("hits", []).
            hits = response.json().get("hits", {}).get("hits", [])
        records: list[Any] = []
        # Loop: for hit in hits.
        for hit in hits:
            # OpenSearch only stores a projection; Postgres is source of truth.
            memory_id = hit.get("_source", {}).get("memory_id", "")
            # Local ``record`` ← await self.postgres.get(memory_id).
            record = await self.postgres.get(memory_id)
            # Only when (record is None).
            if record is None:
                continue
            # Optional domain scope filter after rehydration.
            if scope is not None and not scope.contains(record.scope):
                continue
            records.append(record)
        # Hand ``records`` back to the caller.
        return records

    async def search_semantic(self, *, project: str, query: str, limit: int = 5) -> list[Any]:
        """Embed ``query`` and run pgvector cosine search within ``project``."""
        return await self.postgres.search_embedding(project, await self._vector(query), limit)

    async def read_journal(self, project_id: str, task_id: str) -> list[dict[str, Any]]:
        """Read Cassandra journal_by_task rows for a project/task pair."""
        session = await self._cassandra_session()

        def _read() -> list[dict[str, Any]]:
            # Blocking cassandra driver call runs in a worker thread.
            rows = session.execute(
                """
                SELECT created_at, memory_id, record_type, summary
                FROM journal_by_task WHERE project_id = %s AND task_id = %s
                """,
                (project_id, task_id),
            )
            # Hand ``[`` back to the caller.
            return [
                {
                    "memory_id": row.memory_id,
                    "record_type": row.record_type,
                    "summary": row.summary,
                    "source": "cassandra",
                }
                # Loop: for row in rows.
                for row in rows
            ]

        # Hand ``await asyncio.to_thread(_read)`` back to the caller.
        return await asyncio.to_thread(_read)

    async def read_scope(self, namespace: str, scope_key: str) -> list[dict[str, Any]]:
        """Read Cassandra memory_by_scope rows for a namespace/scope_key."""
        session = await self._cassandra_session()

        def _read() -> list[dict[str, Any]]:
            # Local ``rows`` ← session.execute(.
            rows = session.execute(
                """
                SELECT created_at, memory_id, summary
                FROM memory_by_scope WHERE namespace = %s AND scope_key = %s
                """,
                (namespace, scope_key),
            )
            # Hand ``[{"memory_id": row.memory_id, "summary": row.summary, "source": "cassa…`` back to the caller.
            return [{"memory_id": row.memory_id, "summary": row.summary, "source": "cassandra"} for row in rows]

        # Hand ``await asyncio.to_thread(_read)`` back to the caller.
        return await asyncio.to_thread(_read)

    async def put_artifact(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Write bytes to the object store; create the bucket if missing."""
        client = self._s3_client()
        # Local ``bucket`` ← self._s3_bucket.
        bucket = self._s3_bucket

        def _put() -> str:
            from botocore.exceptions import ClientError

            # Try the fallible work below.
            try:
                # Idempotent bucket create for local MinIO.
                client.create_bucket(Bucket=bucket)
            # On except ClientError as exc: recover or re-raise as appropriate.
            except ClientError as exc:
                # Local ``code`` ← exc.response.get("Error", {}).get("Code", "").
                code = exc.response.get("Error", {}).get("Code", "")
                # Ignore already-exists races; re-raise other errors.
                if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    raise
            client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
            # Hand ``f"s3://{bucket}/{key}"`` back to the caller.
            return f"s3://{bucket}/{key}"

        # Hand ``await asyncio.to_thread(_put)`` back to the caller.
        return await asyncio.to_thread(_put)

    async def get_artifact(self, key: str) -> bytes:
        """Read an object-store artifact by key."""
        client = self._s3_client()
        # Local ``bucket`` ← self._s3_bucket.
        bucket = self._s3_bucket

        def _get() -> bytes:
            # Local ``body`` ← client.get_object(Bucket=bucket, Key=key)["Body"].read().
            body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
            # Hand ``bytes(body)`` back to the caller.
            return bytes(body)

        # Hand ``await asyncio.to_thread(_get)`` back to the caller.
        return await asyncio.to_thread(_get)

    async def put_source(self, *, path: str, data: bytes, message: str) -> str:
        """Commit ``data`` at ``path`` in the git working tree; return HEAD sha."""
        relative = path.strip().lstrip("/")
        # Refuse empty paths and path-traversal segments.
        if not relative or ".." in Path(relative).parts:
            # Raise ``ValueError`` to signal this failure mode to callers.
            raise ValueError(f"Refusing source path {path}")
        # Hold ``self._git_lock`` for the duration of the indented block.
        async with self._git_lock:
            # Hand ``await asyncio.to_thread(self._git_commit, relative, data, message)`` back to the caller.
            return await asyncio.to_thread(self._git_commit, relative, data, message)

    async def get_source(self, path: str) -> bytes:
        """Read a committed source file from the git working tree."""
        relative = path.strip().lstrip("/")
        # Local ``target`` ← self._git_dir / relative.
        target = self._git_dir / relative
        # Hand ``target.read_bytes()`` back to the caller.
        return target.read_bytes()

    async def put_secret(self, *, name: str, value: str) -> None:
        """Write a KV v2 secret under secret/data/memory/{name}."""
        import httpx

        # Local ``url`` ← f"{self._vault}/v1/secret/data/memory/{name.strip('/')}".
        url = f"{self._vault}/v1/secret/data/memory/{name.strip('/')}"
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.post(.
            response = await client.post(
                url,
                # Local ``headers`` ← {"X-Vault-Token": self._vault_token},.
                headers={"X-Vault-Token": self._vault_token},
                # Local ``json`` ← {"data": {"value": value}},.
                json={"data": {"value": value}},
            )
            response.raise_for_status()

    async def get_secret(self, name: str) -> str:
        """Read a KV v2 secret value from Vault."""
        import httpx

        # Local ``url`` ← f"{self._vault}/v1/secret/data/memory/{name.strip('/')}".
        url = f"{self._vault}/v1/secret/data/memory/{name.strip('/')}"
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.get(url, headers={"X-Vault-Token": self._vault_token….
            response = await client.get(url, headers={"X-Vault-Token": self._vault_token})
            response.raise_for_status()
            # Hand ``str(response.json()["data"]["data"]["value"])`` back to the caller.
            return str(response.json()["data"]["data"]["value"])

    async def record_measurement(
        self,
        *,
        namespace: str,
        experiment_id: str,
        metric: str,
        value: float,
        dimensions: dict[str, Any] | None = None,
    ) -> None:
        """Insert one measurement row into ClickHouse."""
        await self._ensure_clickhouse()
        import httpx

        # Local ``row`` ← {.
        row = {
            "namespace": namespace,
            "experiment_id": experiment_id,
            "metric": metric,
            "value": float(value),
            "dimensions": json.dumps(dimensions or {}),
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.post(.
            response = await client.post(
                self._clickhouse,
                # Local ``params`` ← {.
                params={
                    "database": self._clickhouse_db,
                    "user": self._clickhouse_user,
                    "password": self._clickhouse_password,
                    "query": "INSERT INTO measurement FORMAT JSONEachRow",
                },
                # Local ``content`` ← json.dumps(row) + "\n",.
                content=json.dumps(row) + "\n",
            )
            response.raise_for_status()

    async def query_measurements(self, *, namespace: str, experiment_id: str) -> list[dict[str, Any]]:
        """Select measurement rows for a namespace/experiment pair."""
        await self._ensure_clickhouse()
        import httpx

        # Defend the string-interpolated query against quote injection.
        if "'" in namespace or "'" in experiment_id:
            # Raise ``ValueError`` to signal this failure mode to callers.
            raise ValueError("Measurement identifiers cannot contain quotes")
        # Local ``query`` ← (.
        query = (
            "SELECT metric, value FROM measurement "
            f"WHERE namespace = \'{namespace}\' AND experiment_id = \'{experiment_id}\' "
            "ORDER BY metric FORMAT JSON"
        )
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.post(.
            response = await client.post(
                self._clickhouse,
                # Local ``params`` ← {.
                params={
                    "database": self._clickhouse_db,
                    "user": self._clickhouse_user,
                    "password": self._clickhouse_password,
                },
                # Local ``content`` ← query,.
                content=query,
            )
            response.raise_for_status()
            # Hand ``list(response.json().get("data", []))`` back to the caller.
            return list(response.json().get("data", []))

    async def acquire_lease(self, *, lease_id: str, task_id: str, holder: str, scope_path: str, ttl_secs: int = 60) -> bool:
        """Acquire a Postgres-backed exclusive lease for a task."""
        return await self.postgres.acquire_lease(lease_id, task_id, holder, scope_path, ttl_secs)

    async def release_lease(self, *, task_id: str, holder: str) -> bool:
        """Release a Postgres-backed lease held by ``holder``."""
        return await self.postgres.release_lease(task_id, holder)

    async def record_approval(
        self,
        *,
        approval_id: str,
        subject_ref: str,
        approver: str,
        decision: str,
        evidence_ref: str = "",
    ) -> None:
        """Persist an approval decision in Postgres."""
        await self.postgres.record_approval(approval_id, subject_ref, approver, decision, evidence_ref)

    async def get_approval(self, approval_id: str) -> Optional[dict[str, Any]]:
        """Load an approval record from Postgres."""
        return await self.postgres.get_approval(approval_id)

    async def list_decisions(self, scope_path: str) -> list[dict[str, Any]]:
        """List decision log rows for a scope from Postgres."""
        return await self.postgres.list_decisions(scope_path)

    async def apply_copies(self, record: Any, copies: list[StoreCopy]) -> None:
        """Fan out each StoreCopy to its physical writer."""
        for copy in copies:
            # Await ``self._apply_copy`` and continue once it completes.
            await self._apply_copy(record, copy)

    async def _apply_copy(self, record: Any, copy: StoreCopy) -> None:
        """Dispatch one StoreCopy to the matching placement writer."""
        # Effective payload: override or inherited primary.
        payload = record.payload if copy.payload is None else copy.payload
        # Build a view with the override body when it differs from primary.
        view = record if payload == record.payload else record.model_copy(update={"payload": payload})
        # Local ``store`` ← copy.store.
        store = copy.store
        # Postgres envelope was already written by insert/update.
        if store == Placement.POSTGRES.value:
            return
        # Append-only journal + scope index in Cassandra.
        if store == Placement.CASSANDRA_JOURNAL.value:
            # Await ``self._write_cassandra`` and continue once it completes.
            await self._write_cassandra(view)
            return
        # Dictionary lookup row in Cassandra value_by_key.
        if store == Placement.CASSANDRA_KV.value:
            # Await ``self._write_kv`` and continue once it completes.
            await self._write_kv(view, copy.key)
            return
        # Full-text document in OpenSearch.
        if store == Placement.OPENSEARCH.value:
            # Await ``self._index_opensearch`` and continue once it completes.
            await self._index_opensearch(view, copy.key)
            return
        # pgvector embedding derived from summary/tags/payload text.
        if store == Placement.VECTOR.value:
            # Await ``self.postgres.upsert_embedding`` and continue once it completes.
            await self.postgres.upsert_embedding(record.memory_id, await self._vector(self._search_text(view)))
            return
        # Durable NATS JetStream event.
        if store == Placement.NATS.value:
            # Await ``self._publish_event`` and continue once it completes.
            await self._publish_event(view)
            return
        # Large artifact in MinIO/S3.
        if store == Placement.OBJECT.value:
            data, content_type = _object_body(payload)
            # Await ``self.put_artifact`` and continue once it completes.
            await self.put_artifact(key=copy.key, data=data, content_type=content_type)
            return
        # Numeric measurement in ClickHouse.
        if store == Placement.CLICKHOUSE.value:
            # Local ``reserved`` ← {"metric", "value", "experiment_id", "dimensions"}.
            reserved = {"metric", "value", "experiment_id", "dimensions"}
            # Flatten non-reserved scalar fields into dimensions.
            extra = {
                key: item
                # Loop: for key, item in payload.items().
                for key, item in payload.items()
                # Only when (key not in reserved and isinstance(item, (str, int, float)) and not isinstance(i…).
                if key not in reserved and isinstance(item, (str, int, float)) and not isinstance(item, bool)
            }
            # Only when (isinstance(payload.get("dimensions"), dict)).
            if isinstance(payload.get("dimensions"), dict):
                extra.update(payload["dimensions"])
            # Await ``self.record_measurement`` and continue once it completes.
            await self.record_measurement(
                # Local ``namespace`` ← record.project_id,.
                namespace=record.project_id,
                # Local ``experiment_id`` ← str(payload.get("experiment_id") or copy.key),.
                experiment_id=str(payload.get("experiment_id") or copy.key),
                # Local ``metric`` ← str(payload["metric"]),.
                metric=str(payload["metric"]),
                # Local ``value`` ← float(payload["value"]),.
                value=float(payload["value"]),
                # Local ``dimensions`` ← extra,.
                dimensions=extra,
            )
            return
        # Versioned source file in git.
        if store == Placement.GIT.value:
            # Local ``text`` ← _payload_text(payload).
            text = _payload_text(payload)
            # Local ``message`` ← str(payload.get("message") or record.summary or "memory write").
            message = str(payload.get("message") or record.summary or "memory write")
            # Await ``self.put_source`` and continue once it completes.
            await self.put_source(path=copy.key, data=text.encode(), message=message)
            return
        # Secret in Vault (never duplicated elsewhere — enforced by policy).
        if store == Placement.VAULT.value:
            # Await ``self.put_secret`` and continue once it completes.
            await self.put_secret(name=copy.key, value=str(payload["value"]))
            return
        # Raise ``ValueError`` to signal this failure mode to callers.
        raise ValueError(f"No writer for store {store}")

    async def read_copy(self, store: str, project_id: str, key: str = "") -> Any:
        """Read a projected copy back from its physical store."""
        if store == Placement.CASSANDRA_KV.value:
            # Local ``found`` ← await self.get_lookup(project_id, key).
            found = await self.get_lookup(project_id, key)
            # Only when (found is None).
            if found is None:
                # Hand ``None`` back to the caller.
                return None
            # Hand ``found.payload`` back to the caller.
            return found.payload
        # Only when (store == Placement.OBJECT.value).
        if store == Placement.OBJECT.value:
            # Local ``body`` ← await self.get_artifact(key).
            body = await self.get_artifact(key)
            # Hand ``{"text": body.decode()}`` back to the caller.
            return {"text": body.decode()}
        # Only when (store == Placement.GIT.value).
        if store == Placement.GIT.value:
            # Local ``body`` ← await self.get_source(key).
            body = await self.get_source(key)
            # Hand ``{"text": body.decode()}`` back to the caller.
            return {"text": body.decode()}
        # Only when (store == Placement.VAULT.value).
        if store == Placement.VAULT.value:
            # Hand ``{"value": await self.get_secret(key)}`` back to the caller.
            return {"value": await self.get_secret(key)}
        # Only when (store == Placement.CLICKHOUSE.value).
        if store == Placement.CLICKHOUSE.value:
            # Hand ``await self.query_measurements(namespace=project_id, experiment_id=key)`` back to the caller.
            return await self.query_measurements(namespace=project_id, experiment_id=key)
        # Hand ``None`` back to the caller.
        return None

    async def get_lookup(self, project_id: str, key: str) -> Optional[Any]:
        """Load the envelope bound to a Cassandra KV lookup key."""
        session = await self._cassandra_session()

        def _read() -> Optional[str]:
            # Local ``row`` ← session.execute(.
            row = session.execute(
                "SELECT envelope FROM value_by_key WHERE project_id = %s AND lookup_key = %s",
                (project_id, key),
            ).one()
            # Only when (row is None).
            if row is None:
                # Hand ``None`` back to the caller.
                return None
            # Hand ``str(row.envelope)`` back to the caller.
            return str(row.envelope)

        # Local ``raw`` ← await asyncio.to_thread(_read).
        raw = await asyncio.to_thread(_read)
        # Only when (raw is None).
        if raw is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``self._record_cls.model_validate_json(raw)`` back to the caller.
        return self._record_cls.model_validate_json(raw)

    async def _vector(self, text: str) -> list[float]:
        """Embed ``text`` via MEMORY_EMBEDDING_URL or the local hash embedder."""
        endpoint = os.environ.get("MEMORY_EMBEDDING_URL", "").strip()
        # Only when (not endpoint).
        if not endpoint:
            # Hand ``embed_text(text)`` back to the caller.
            return embed_text(text)
        import httpx

        # Hold ``httpx.AsyncClient(timeout=20.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Local ``response`` ← await client.post(endpoint, json={"input": text}).
            response = await client.post(endpoint, json={"input": text})
            response.raise_for_status()
            # Local ``body`` ← response.json().
            body = response.json()
            # Support both OpenAI-style and flat embedding response shapes.
            vector = body.get("embedding") or body["data"][0]["embedding"]
            # Hand ``[float(value) for value in vector]`` back to the caller.
            return [float(value) for value in vector]

    def _search_text(self, record: Any) -> str:
        """Concatenate summary, tags, and payload for embedding / OpenSearch body."""
        return " ".join([
            record.summary,
            " ".join(record.tags),
            json.dumps(record.payload, sort_keys=True),
        ])

    async def _cassandra_session(self) -> Any:
        """Lazily connect to Cassandra and ensure keyspace/tables exist."""
        if self._cassandra is not None:
            # Hand ``self._cassandra`` back to the caller.
            return self._cassandra

        # Local ``hosts`` ← [item.strip() for item in self._cassandra_hosts.split(",") if ite….
        hosts = [item.strip() for item in self._cassandra_hosts.split(",") if item.strip()]
        # Local ``port`` ← self._cassandra_port.
        port = self._cassandra_port

        def _connect() -> Any:
            from cassandra.cluster import Cluster

            # Local ``cluster`` ← Cluster(hosts, port=port).
            cluster = Cluster(hosts, port=port)
            # Local ``session`` ← cluster.connect().
            session = cluster.connect()
            # Dev-friendly SimpleStrategy RF=1 keyspace.
            session.execute(
                """
                CREATE KEYSPACE IF NOT EXISTS agent_memory
                WITH replication = {\'class\': \'SimpleStrategy\', \'replication_factor\': 1}
                """
            )
            session.set_keyspace("agent_memory")
            # Append-only journal partitioned by project+task.
            session.execute(
                """
                CREATE TABLE IF NOT EXISTS journal_by_task (
                    project_id text,
                    task_id text,
                    created_at timestamp,
                    memory_id text,
                    record_type text,
                    summary text,
                    envelope text,
                    PRIMARY KEY ((project_id, task_id), created_at, memory_id)
                ) WITH CLUSTERING ORDER BY (created_at ASC, memory_id ASC)
                """
            )
            # Dictionary lookup by project+key.
            session.execute(
                """
                CREATE TABLE IF NOT EXISTS value_by_key (
                    project_id text,
                    lookup_key text,
                    memory_id text,
                    summary text,
                    envelope text,
                    PRIMARY KEY ((project_id, lookup_key))
                )
                """
            )
            # Scope timeline for browsing a namespace/scope_key.
            session.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_by_scope (
                    namespace text,
                    scope_key text,
                    created_at timestamp,
                    memory_id text,
                    summary text,
                    envelope text,
                    PRIMARY KEY ((namespace, scope_key), created_at, memory_id)
                ) WITH CLUSTERING ORDER BY (created_at ASC, memory_id ASC)
                """
            )
            # Hand ``session`` back to the caller.
            return session

        # Bind ``_cassandra`` from await asyncio.to_thread(_connect) for later use on this instance.
        self._cassandra = await asyncio.to_thread(_connect)
        # Hand ``self._cassandra`` back to the caller.
        return self._cassandra

    async def _write_cassandra(self, record: Any) -> None:
        """Insert journal_by_task and memory_by_scope rows for ``record``."""
        session = await self._cassandra_session()
        # Local ``created`` ← record.created_at.
        created = record.created_at
        # Local ``envelope`` ← record.model_dump_json().
        envelope = record.model_dump_json()
        # Local ``scope_key`` ← record.scope_key.
        scope_key = record.scope_key

        def _write() -> None:
            session.execute(
                """
                INSERT INTO journal_by_task (
                    project_id, task_id, created_at, memory_id, record_type, summary, envelope
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record.project_id,
                    record.task_id or "_",
                    created,
                    record.memory_id,
                    label(record.record_type),
                    record.summary,
                    envelope,
                ),
            )
            session.execute(
                """
                INSERT INTO memory_by_scope (
                    namespace, scope_key, created_at, memory_id, summary, envelope
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    record.project_id,
                    scope_key,
                    created,
                    record.memory_id,
                    record.summary,
                    envelope,
                ),
            )

        # Await ``asyncio.to_thread`` and continue once it completes.
        await asyncio.to_thread(_write)

    async def _write_kv(self, record: Any, key: str) -> None:
        """Upsert a value_by_key dictionary row."""
        session = await self._cassandra_session()
        # Local ``envelope`` ← record.model_dump_json().
        envelope = record.model_dump_json()

        def _write() -> None:
            session.execute(
                """
                INSERT INTO value_by_key (project_id, lookup_key, memory_id, summary, envelope)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (record.project_id, key, record.memory_id, record.summary, envelope),
            )

        # Await ``asyncio.to_thread`` and continue once it completes.
        await asyncio.to_thread(_write)

    async def _ensure_search_index(self) -> None:
        """Create the OpenSearch ``memory`` index mapping if needed."""
        if self._index_ready:
            return
        import httpx

        # Local ``mapping`` ← {.
        mapping = {
            "mappings": {
                "properties": {
                    "memory_id": {"type": "keyword"},
                    "project_id": {"type": "keyword"},
                    "scope_path": {"type": "keyword"},
                    "record_type": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "body": {"type": "text"},
                    "tags": {"type": "keyword"},
                }
            }
        }
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.put(f"{self._opensearch}/memory", json=mapping).
            response = await client.put(f"{self._opensearch}/memory", json=mapping)
            # 400 usually means the index already exists — acceptable.
            if response.status_code not in (200, 400):
                response.raise_for_status()
        # Bind ``_index_ready`` from True for later use on this instance.
        self._index_ready = True

    async def _index_opensearch(self, record: Any, key: str = "") -> None:
        """Upsert one OpenSearch document for ``record``."""
        await self._ensure_search_index()
        import httpx

        # Local ``document`` ← {.
        document = {
            "memory_id": record.memory_id,
            "project_id": record.project_id,
            "scope_path": record.scope_path,
            "record_type": label(record.record_type),
            "summary": record.summary,
            "body": self._search_text(record),
            "tags": record.tags,
        }
        # Optional key suffix allows multiple docs per envelope.
        doc_id = record.memory_id if not key else f"{record.memory_id}:{key}"
        # Hold ``httpx.AsyncClient(timeout=10.0)`` for the duration of the indented block.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.put(.
            response = await client.put(
                f"{self._opensearch}/memory/_doc/{doc_id}",
                # Local ``params`` ← {"refresh": "true"},.
                params={"refresh": "true"},
                # Local ``json`` ← document,.
                json=document,
            )
            response.raise_for_status()

    def _s3_client(self) -> Any:
        """Lazily construct a path-style S3 client aimed at MinIO/local S3."""
        if self._s3 is None:
            import boto3
            from botocore.config import Config

            # Bind ``_s3`` from boto3.client( for later use on this instance.
            self._s3 = boto3.client(
                "s3",
                # Local ``endpoint_url`` ← self._s3_endpoint,.
                endpoint_url=self._s3_endpoint,
                # Local ``aws_access_key_id`` ← self._s3_key,.
                aws_access_key_id=self._s3_key,
                # Local ``aws_secret_access_key`` ← self._s3_secret,.
                aws_secret_access_key=self._s3_secret,
                # Local ``region_name`` ← "us-east-1",.
                region_name="us-east-1",
                # Local ``config`` ← Config(s3={"addressing_style": "path"}, signature_version="s3v4")….
                config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
            )
        # Hand ``self._s3`` back to the caller.
        return self._s3

    async def _ensure_clickhouse(self) -> None:
        """Create the measurement MergeTree table if it does not exist."""
        if self._clickhouse_ready:
            return
        import httpx

        # Local ``statement`` ← """.
        statement = """
        CREATE TABLE IF NOT EXISTS measurement (
            namespace String,
            experiment_id String,
            metric String,
            value Float64,
            dimensions String,
            recorded_at DateTime
        ) ENGINE = MergeTree
        ORDER BY (namespace, experiment_id, metric)
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Local ``response`` ← await client.post(.
            response = await client.post(
                self._clickhouse,
                # Local ``params`` ← {.
                params={
                    "database": self._clickhouse_db,
                    "user": self._clickhouse_user,
                    "password": self._clickhouse_password,
                },
                # Local ``content`` ← statement,.
                content=statement,
            )
            response.raise_for_status()
        # Bind ``_clickhouse_ready`` from True for later use on this instance.
        self._clickhouse_ready = True

    def _git_commit(self, relative: str, data: bytes, message: str) -> str:
        """Write ``data`` and commit+push to a sibling bare repo; return HEAD sha."""
        root = self._git_dir
        root.mkdir(parents=True, exist_ok=True)
        # Initialize a main-branch repo with a local identity on first use.
        if not (root / ".git").exists():
            subprocess.run(["git", "init", "-b", "main", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "memory@localhost"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "memory"], check=True)
        # Local ``target`` ← root / relative.
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        subprocess.run(["git", "-C", str(root), "add", relative], check=True)
        # Only commit when the index actually changed.
        cached = subprocess.run(["git", "-C", str(root), "diff", "--cached", "--quiet"])
        # Only when (cached.returncode != 0).
        if cached.returncode != 0:
            subprocess.run(["git", "-C", str(root), "commit", "-m", message], check=True)
        # Local ``sha`` ← subprocess.check_output(["git", "-C", str(root), "rev-parse", "HE….
        sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        # Mirror into a bare repo beside the working tree for durability.
        bare = root.parent / "memory.git"
        # Only when (not bare.exists()).
        if not bare.exists():
            subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True)
        subprocess.run(["git", "-C", str(root), "push", "--force", str(bare), "HEAD:main"], check=True)
        # Hand ``sha`` back to the caller.
        return sha

    async def _publish_event(self, record: Any) -> None:
        """Publish a compact memory event onto the MEMORY JetStream stream."""
        import nats

        # Only when (self._nats is None).
        if self._nats is None:
            # Bind ``_nats`` from await nats.connect(self._nats_url) for later use on this instance.
            self._nats = await nats.connect(self._nats_url)
            # Bind ``_js`` from self._nats.jetstream() for later use on this instance.
            self._js = self._nats.jetstream()
            # Try the fallible work below.
            try:
                # Await ``self._js.add_stream`` and continue once it completes.
                await self._js.add_stream(name="MEMORY", subjects=["memory.>"])
            # On except Exception as exc: recover or re-raise as appropriate.
            except Exception as exc:
                # Treat "already exists" as success; re-raise anything else.
                if "already" not in str(exc).lower():
                    raise
        # Local ``payload`` ← json.dumps({.
        payload = json.dumps({
            "memory_id": record.memory_id,
            "project_id": record.project_id,
            "task_id": record.task_id,
            "record_type": label(record.record_type),
            "summary": record.summary,
        }).encode()
        # Await ``self._js.publish`` and continue once it completes.
        await self._js.publish(f"memory.{label(record.record_type)}", payload)

    async def event_count(self) -> int:
        """Return the number of messages currently in the MEMORY stream."""
        import nats

        # Only when (self._nats is None).
        if self._nats is None:
            # Bind ``_nats`` from await nats.connect(self._nats_url) for later use on this instance.
            self._nats = await nats.connect(self._nats_url)
            # Bind ``_js`` from self._nats.jetstream() for later use on this instance.
            self._js = self._nats.jetstream()
        # Local ``info`` ← await self._js.stream_info("MEMORY").
        info = await self._js.stream_info("MEMORY")
        # Hand ``int(info.state.messages)`` back to the caller.
        return int(info.state.messages)


def _payload_text(payload: dict[str, Any]) -> str:
    """Extract a text body for GIT placement from common payload shapes."""
    if "text" in payload:
        # Hand ``str(payload["text"])`` back to the caller.
        return str(payload["text"])
    # Only when ("body" in payload).
    if "body" in payload:
        # Hand ``str(payload["body"])`` back to the caller.
        return str(payload["body"])
    # Hand ``json.dumps(payload)`` back to the caller.
    return json.dumps(payload)


def _object_body(payload: dict[str, Any]) -> tuple[bytes, str]:
    """Extract (bytes, content_type) for OBJECT placement from a payload dict."""
    if "text" in payload:
        # Hand ``str(payload["text"]).encode(), str(payload.get("content_type") or "tex…`` back to the caller.
        return str(payload["text"]).encode(), str(payload.get("content_type") or "text/plain")
    # Only when ("body" in payload).
    if "body" in payload:
        # Hand ``str(payload["body"]).encode(), str(payload.get("content_type") or "app…`` back to the caller.
        return str(payload["body"]).encode(), str(payload.get("content_type") or "application/octet-stream")
    # Hand ``json.dumps(payload).encode(), "application/json"`` back to the caller.
    return json.dumps(payload).encode(), "application/json"
