"""JSONL MemoryStore shared by agent processes on one machine.

Every read reloads the files under an exclusive ``fcntl`` lock, so a journal
written by one agent is visible to the next. This is the initial shared
deployment path when ``MEMORY_BACKEND=file``. Postgres exposes the
same ``MemoryStore`` API when the backend is switched to postgres.

On-disk layout under ``root``:

* ``records.jsonl`` — one envelope JSON per line
* ``baselines.json`` — scope_path → pointer map
# Call ``* ``copies.json`` — projected store copies``.
* ``copies.json`` — projected store copies (simulates Cassandra KV / etc.)
* ``.lock`` — flock target for cross-process mutual exclusion
"""

from __future__ import annotations

# asyncio.Lock serializes awaiters inside one process.
import asyncio
# deepcopy isolates projected payloads.
import copy
# fcntl.flock coordinates across OS processes sharing the same root.
import fcntl
# json for baselines and copies side files.
import json
# os.replace for atomic file swaps.
import os
# Path for root / lock / jsonl paths.
from pathlib import Path
# Any/Optional for opaque envelopes.
from typing import Any, Optional

# StoreCopy describes one write-policy projection.
from packages.memory.policy import StoreCopy


class FileStore:
    """JSONL store shared by agent processes on one machine.

    Every read reloads the files under a lock, so a journal written by one
    agent is visible to the next. This is the initial shared deployment.
    Postgres is the same API when MEMORY_BACKEND=postgres.
    """

    def __init__(self, root: str | Path, *, record_cls: type) -> None:
        # Pydantic (or compatible) class used to rehydrate JSONL lines.
        self._record_cls = record_cls
        # Absolute/relative root directory for all store files.
        self.root = Path(root)
        # Ensure the directory exists before any IO.
        self.root.mkdir(parents=True, exist_ok=True)
        # Append-only-style envelope journal (fully rewritten on each write).
        self._records_path = self.root / "records.jsonl"
        # Baseline pointer map path.
        self._baseline_path = self.root / "baselines.json"
        # Projected copy list path.
        self._copies_path = self.root / "copies.json"
        # Cross-process flock file.
        self._lock_path = self.root / ".lock"
        # Intra-process async mutex (flock alone is not enough across tasks).
        self._async_lock = asyncio.Lock()

    def _exclusive(self):
        """Return a context manager that holds an exclusive flock on ``.lock``."""
        return _FileLock(self._lock_path)

    def _load(self) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
        """Reload records, idempotency index, and baselines from disk."""
        # memory_id → envelope.
        records: dict[str, Any] = {}
        # idempotency_key → memory_id.
        idempotency: dict[str, str] = {}
        # Only when (self._records_path.exists()).
        if self._records_path.exists():
            # Parse each non-empty JSONL line into a record instance.
            for line in self._records_path.read_text().splitlines():
                # Local ``line`` ← line.strip().
                line = line.strip()
                # Only when (not line).
                if not line:
                    continue
                # Rehydrate via the domain record class.
                record = self._record_cls.model_validate_json(line)
                records[record.memory_id] = record
                # Rebuild the idempotency index from the journal.
                if record.idempotency_key:
                    idempotency[record.idempotency_key] = record.memory_id
        # Load baselines if the side file exists.
        baselines: dict[str, str] = {}
        # Only when (self._baseline_path.exists()).
        if self._baseline_path.exists():
            # Local ``baselines`` ← json.loads(self._baseline_path.read_text()).
            baselines = json.loads(self._baseline_path.read_text())
        # Hand ``records, idempotency, baselines`` back to the caller.
        return records, idempotency, baselines

    def _write_records(self, records: dict[str, Any]) -> None:
        """Atomically rewrite the JSONL journal from the in-memory map."""
        # Write to a temp file then os.replace for crash safety.
        tmp = self._records_path.with_suffix(".jsonl.tmp")
        # Hold ``tmp.open("w")`` for the duration of the indented block.
        with tmp.open("w") as fh:
            # Loop: for record in records.values().
            for record in records.values():
                # One envelope JSON per line.
                fh.write(record.model_dump_json())
                # Call ``fh.write``.
                fh.write("\n")
        # Atomic rename into place.
        os.replace(tmp, self._records_path)

    def _write_baselines(self, baselines: dict[str, str]) -> None:
        """Atomically rewrite the baselines JSON map."""
        tmp = self._baseline_path.with_suffix(".json.tmp")
        # Call ``tmp.write_text``.
        tmp.write_text(json.dumps(baselines))
        # Call ``os.replace``.
        os.replace(tmp, self._baseline_path)

    async def insert(self, record: Any) -> None:
        """Append/upsert ``record`` into the JSONL journal under dual locks."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Reload so we see concurrent writers' commits.
                records, idempotency, _baselines = self._load()
                records[record.memory_id] = record
                # Only when (record.idempotency_key).
                if record.idempotency_key:
                    idempotency[record.idempotency_key] = record.memory_id
                # Persist the updated journal (idempotency is derived on load).
                self._write_records(records)

    async def get(self, memory_id: str) -> Optional[Any]:
        """Load one envelope by id under dual locks."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``records, _idempotency, _baselines = self._load``.
                records, _idempotency, _baselines = self._load()
        # Hand ``records.get(memory_id)`` back to the caller.
        return records.get(memory_id)

    async def find_idempotency(self, key: str) -> Optional[Any]:
        """Resolve an idempotency key through the rebuilt index."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``records, idempotency, _baselines = self._load``.
                records, idempotency, _baselines = self._load()
        # Local ``memory_id`` ← idempotency.get(key).
        memory_id = idempotency.get(key)
        # Only when (memory_id is None).
        if memory_id is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``records.get(memory_id)`` back to the caller.
        return records.get(memory_id)

    async def scan(self) -> list[Any]:
        """Return every envelope currently on disk."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``records, _idempotency, _baselines = self._load``.
                records, _idempotency, _baselines = self._load()
        # Hand ``list(records.values())`` back to the caller.
        return list(records.values())

    async def update(self, record: Any) -> None:
        """Overwrite ``record.memory_id`` in the journal."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``records, _idempotency, _baselines = self._load``.
                records, _idempotency, _baselines = self._load()
                records[record.memory_id] = record
                # Call ``self._write_records``.
                self._write_records(records)

    async def get_baseline(self, scope_path: str) -> Optional[str]:
        """Read the baseline pointer for ``scope_path``."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``_records, _idempotency, baselines = self._load``.
                _records, _idempotency, baselines = self._load()
        # Hand ``baselines.get(scope_path)`` back to the caller.
        return baselines.get(scope_path)

    async def compare_and_set_baseline(
        self,
        scope_path: str,
        expected: Optional[str],
        new_value: str,
    ) -> bool:
        """CAS the baseline pointer under dual locks; return success flag."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``_records, _idempotency, baselines = self._load``.
                _records, _idempotency, baselines = self._load()
                # Local ``current`` ← baselines.get(scope_path).
                current = baselines.get(scope_path)
                # Fail closed when the caller’s expected value is stale.
                if current != expected:
                    # Hand ``False`` back to the caller.
                    return False
                baselines[scope_path] = new_value
                # Call ``self._write_baselines``.
                self._write_baselines(baselines)
                # Hand ``True`` back to the caller.
                return True

    async def apply_copies(self, record: Any, copies: list[StoreCopy]) -> None:
        """Upsert projected copies into ``copies.json`` for the given record."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Local ``items`` ← self._load_copies().
                items = self._load_copies()
                # Loop: for item in copies.
                for item in copies:
                    # Inherit primary payload when the copy has no override.
                    payload = copy.deepcopy(item.payload if item.payload is not None else record.payload)
                    # Drop any prior entry for the same (store, project, key).
                    items = [
                        existing
                        # Loop: for existing in items.
                        for existing in items
                        # Only when (not ().
                        if not (
                            existing["store"] == item.store
                            and existing["project_id"] == record.project_id
                            and existing["key"] == item.key
                        )
                    ]
                    # Append the fresh projection row.
                    items.append({
                        "store": item.store,
                        "project_id": record.project_id,
                        "key": item.key,
                        "memory_id": record.memory_id,
                        "payload": payload,
                    })
                # Call ``self._write_copies``.
                self._write_copies(items)

    async def read_copy(self, store: str, project_id: str, key: str = "") -> Optional[dict[str, Any]]:
        """Return a deep-copied projection payload if present."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Local ``items`` ← self._load_copies().
                items = self._load_copies()
        # Loop: for item in items.
        for item in items:
            # Only when (item["store"] == store and item["project_id"] == project_id and item["key"] == k…).
            if item["store"] == store and item["project_id"] == project_id and item["key"] == key:
                # Hand ``copy.deepcopy(item["payload"])`` back to the caller.
                return copy.deepcopy(item["payload"])
        # Hand ``None`` back to the caller.
        return None

    async def get_lookup(self, project_id: str, key: str) -> Optional[Any]:
        """Return the envelope view for a cassandra_kv-style lookup key."""
        async with self._async_lock:
            # Hold ``self._exclusive()`` for the duration of the indented block.
            with self._exclusive():
                # Call ``records, _idempotency, _baselines = self._load``.
                records, _idempotency, _baselines = self._load()
                # Local ``items`` ← self._load_copies().
                items = self._load_copies()
        # Loop: for item in items.
        for item in items:
            # Only when (item["store"] == "cassandra_kv" and item["project_id"] == project_id and item["k…).
            if item["store"] == "cassandra_kv" and item["project_id"] == project_id and item["key"] == key:
                # Local ``record`` ← records.get(item["memory_id"]).
                record = records.get(item["memory_id"])
                # Only when (record is None).
                if record is None:
                    # Hand ``None`` back to the caller.
                    return None
                # Substitute the KV payload onto a copy of the envelope.
                return record.model_copy(update={"payload": copy.deepcopy(item["payload"])})
        # Hand ``None`` back to the caller.
        return None

    def _load_copies(self) -> list[dict[str, Any]]:
        """Load the projected-copy list from disk (empty list if missing)."""
        if not self._copies_path.exists():
            # Hand ``[]`` back to the caller.
            return []
        # Hand ``list(json.loads(self._copies_path.read_text()))`` back to the caller.
        return list(json.loads(self._copies_path.read_text()))

    def _write_copies(self, items: list[dict[str, Any]]) -> None:
        """Atomically rewrite ``copies.json``."""
        tmp = self._copies_path.with_suffix(".json.tmp")
        # Call ``tmp.write_text``.
        tmp.write_text(json.dumps(items))
        # Call ``os.replace``.
        os.replace(tmp, self._copies_path)


class _FileLock:
    """Context manager wrapping ``fcntl.flock`` exclusive locking."""

    def __init__(self, path: Path) -> None:
        # Path of the lock file shared by all FileStore processes.
        self.path = path
        # Open file handle held for the duration of the critical section.
        self._fh = None

    def __enter__(self):
        """Open the lock file and acquire an exclusive flock."""
        self._fh = self.path.open("a+")
        # Call ``fcntl.flock``.
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        # Hand ``self._fh`` back to the caller.
        return self._fh

    def __exit__(self, exc_type, exc, tb) -> None:
        """Release the flock and close the handle."""
        if self._fh is not None:
            # Call ``fcntl.flock``.
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            # Call ``self._fh.close``.
            self._fh.close()
            # Bind ``_fh`` from None for later use on this instance.
            self._fh = None
