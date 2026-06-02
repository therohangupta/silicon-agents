"""
Blob storage backend for telemetry vision data.

Supports local filesystem and S3 (via boto3).
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

from packages.config import BLOB_STORAGE_BACKEND, BLOB_STORAGE_ROOT, S3_BUCKET, S3_REGION

logger = logging.getLogger(__name__)


class BlobStore:
    """Write and read blobs from local disk or S3."""

    def __init__(
        self,
        backend: str = BLOB_STORAGE_BACKEND,
        root: str = BLOB_STORAGE_ROOT,
        s3_bucket: str = S3_BUCKET,
        s3_region: str = S3_REGION,
    ):
        self._backend = backend
        self._root = Path(root)
        self._s3_bucket = s3_bucket
        self._s3_region = s3_region
        self._s3_client = None

    async def write(
        self,
        robot_id: str,
        stream_name: str,
        filename: str,
        data: bytes,
        task_id: str = "",
    ) -> str:
        """
        Write blob data and return its URI.

        When *task_id* is provided the path is scoped per-episode so
        different runs on the same robot never overwrite each other.
        """
        if self._backend == "s3":
            return await self._write_s3(robot_id, stream_name, filename, data, task_id)
        return self._write_local(robot_id, stream_name, filename, data, task_id)

    def _write_local(
        self, robot_id: str, stream_name: str, filename: str, data: bytes, task_id: str = ""
    ) -> str:
        parts = [robot_id]
        if task_id:
            parts.append(task_id)
        parts.append(stream_name)
        dest_dir = self._root
        for p in parts:
            dest_dir = dest_dir / p
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_bytes(data)
        return "/blobs/" + "/".join(parts) + "/" + filename

    async def _write_s3(
        self, robot_id: str, stream_name: str, filename: str, data: bytes, task_id: str = ""
    ) -> str:
        import boto3

        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self._s3_region)

        parts = ["blobs", robot_id]
        if task_id:
            parts.append(task_id)
        parts.extend([stream_name, filename])
        key = "/".join(parts)
        self._s3_client.put_object(
            Bucket=self._s3_bucket,
            Key=key,
            Body=data,
        )
        return f"s3://{self._s3_bucket}/{key}"

    def read_local(self, path: str) -> Optional[bytes]:
        """Read a blob from local storage. *path* is the URI suffix after /blobs/."""
        full = self._root / path.lstrip("/")
        if full.exists():
            return full.read_bytes()
        return None

    def get_presigned_url(self, s3_uri: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL for an S3 blob."""
        import boto3

        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self._s3_region)

        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        return self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )


_store: Optional[BlobStore] = None


def get_blob_store() -> BlobStore:
    global _store
    if _store is None:
        _store = BlobStore()
    return _store
