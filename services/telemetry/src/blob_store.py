"""
Blob storage backend for telemetry vision data.

Agents upload frames via ``POST /telemetry/blob``; this module writes bytes to
local disk under ``BLOB_STORAGE_ROOT`` or to S3 and returns a URI that later
VisionPayload events reference. Local URIs look like ``/blobs/...``; S3 URIs
are ``s3://bucket/key``. Helpers also support reading local blobs and minting
presigned GET URLs for S3.
"""

# hashlib imported for potential content hashing (kept for parity with prior surface).
import hashlib  # noqa: F401  # retained import; write paths use filename from caller
# Logging for store diagnostics.
import logging
# os available for path edge cases; Path is the primary API.
import os  # noqa: F401
from pathlib import Path
from typing import Optional

# Shared blob backend knobs from packages.config.
from packages.config import BLOB_STORAGE_BACKEND, BLOB_STORAGE_ROOT, S3_BUCKET, S3_REGION

# Module logger for upload/read failures and info.
logger = logging.getLogger(__name__)


class BlobStore:
    """Write and read blobs from local disk or S3.

    Backend selection is ``BLOB_STORAGE_BACKEND`` (``local`` vs ``s3``). Local
    layout: ``{root}/{agent_id}/[{task_id}/]{stream_name}/{filename}``. S3 keys
    prefix with ``blobs/`` and the same path segments. The S3 client is created
    lazily on first S3 operation.
    """

    def __init__(
        self,
        backend: str = BLOB_STORAGE_BACKEND,
        root: str = BLOB_STORAGE_ROOT,
        s3_bucket: str = S3_BUCKET,
        s3_region: str = S3_REGION,
    ):
        """Capture backend settings; defer boto3 client creation.

        Args:
            backend: ``local`` or ``s3`` (anything other than ``s3`` uses disk).
            root: Filesystem root for local writes.
            s3_bucket: Destination bucket for S3 writes.
            s3_region: Region passed to boto3.client.
        """
        # Store backend name for write() branching.
        self._backend = backend
        # Normalize root to Path for join/mkdir.
        self._root = Path(root)
        # Bucket name for put_object / presign.
        self._s3_bucket = s3_bucket
        # Region for the S3 client.
        self._s3_region = s3_region
        # Lazy boto3 client handle.
        self._s3_client = None

    async def write(
        self,
        agent_id: str,
        stream_name: str,
        filename: str,
        data: bytes,
        task_id: str = "",
    ) -> str:
        """
        Write blob data and return its URI.

        When *task_id* is provided the path is scoped per-episode so
        different runs on the same agent never overwrite each other.
        Dispatches to ``_write_s3`` or ``_write_local`` based on backend.
        """
        # S3 path when configured for object storage.
        if self._backend == "s3":
            return await self._write_s3(agent_id, stream_name, filename, data, task_id)
        # Default: filesystem under BLOB_STORAGE_ROOT.
        return self._write_local(agent_id, stream_name, filename, data, task_id)

    def _write_local(
        self, agent_id: str, stream_name: str, filename: str, data: bytes, task_id: str = ""
    ) -> str:
        """Write bytes under the local root and return a ``/blobs/...`` URI."""
        # Start path segments with agent identity.
        parts = [agent_id]
        # Optional task scope to isolate episodes.
        if task_id:
            parts.append(task_id)
        # Stream name partitions cameras/modalities.
        parts.append(stream_name)
        # Walk Path joins to build the destination directory.
        dest_dir = self._root
        for p in parts:
            dest_dir = dest_dir / p
        # Create parents as needed (idempotent).
        dest_dir.mkdir(parents=True, exist_ok=True)
        # Final file path.
        dest = dest_dir / filename
        # Atomic-enough for our purposes: single write_bytes call.
        dest.write_bytes(data)
        # HTTP-style URI relative to a /blobs mount convention.
        return "/blobs/" + "/".join(parts) + "/" + filename

    async def _write_s3(
        self, agent_id: str, stream_name: str, filename: str, data: bytes, task_id: str = ""
    ) -> str:
        """Upload bytes to S3 and return an ``s3://bucket/key`` URI."""
        # Import boto3 only on S3 path so local-only installs stay light.
        import boto3

        # Lazily construct the client once.
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self._s3_region)

        # Key always starts with blobs/ then agent (and optional task).
        parts = ["blobs", agent_id]
        if task_id:
            parts.append(task_id)
        # Stream + filename complete the object key.
        parts.extend([stream_name, filename])
        key = "/".join(parts)
        # PutObject with raw body bytes.
        self._s3_client.put_object(
            Bucket=self._s3_bucket,
            Key=key,
            Body=data,
        )
        # Canonical S3 URI for BlobRef.uri.
        return f"s3://{self._s3_bucket}/{key}"

    def read_local(self, path: str) -> Optional[bytes]:
        """Read a blob from local storage. *path* is the URI suffix after /blobs/.

        Returns None when the file does not exist. Does not support S3 reads;
        use ``get_presigned_url`` for remote objects.
        """
        # Join root with the relative path (strip leading slashes).
        full = self._root / path.lstrip("/")
        # Missing file => None for callers to 404.
        if full.exists():
            return full.read_bytes()
        return None

    def get_presigned_url(self, s3_uri: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL for an S3 blob.

        Parses ``s3://bucket/key``, ensures a boto3 client exists, and returns
        a temporary URL valid for ``expires_in`` seconds (default one hour).
        """
        import boto3

        # Create client if write never ran first.
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self._s3_region)

        # Split s3://bucket/key into bucket and key.
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        # Presign GetObject for browser/agent download.
        return self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )


# Process singleton; None until get_blob_store().
_store: Optional[BlobStore] = None


def get_blob_store() -> BlobStore:
    """Return the module-level BlobStore singleton, creating it on first use.

    Routers call this so all uploads share one backend configuration from env.
    """
    global _store
    if _store is None:
        _store = BlobStore()
    return _store
