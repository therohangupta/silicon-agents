"""
Partition manifest management.

Writes and updates a ``_manifest.json`` sidecar inside each Parquet partition
directory. The manifest stores lightweight metadata derived from Parquet file
footers (row counts, step_index ranges) so downstream consumers can discover
partitions and episodes without scanning every file. Writes are atomic via a
``.json.tmp`` rename.
"""

# JSON serialize the manifest dict.
import json
# Warnings on corrupt/unreadable inputs.
import logging
# ISO8601 updated_at stamps in UTC.
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Footer-only metadata reads (no full row scan).
import pyarrow.parquet as pq

# Module logger.
logger = logging.getLogger(__name__)


def _read_existing(manifest_path: Path) -> dict:
    """Return the existing manifest dict, or a blank skeleton.

    On missing file, JSON errors, or OS errors, returns ``{}`` so builders can
    start fresh while optionally preserving ``episode_complete`` when the
    caller passes ``None``.
    """
    # Only attempt read when the sidecar exists.
    if manifest_path.exists():
        try:
            # Parse prior manifest for fields we may preserve.
            return json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            # Corrupt sidecar: rebuild from footers.
            logger.warning("Corrupt manifest at %s — rebuilding", manifest_path)
    # No usable prior state.
    return {}


def build_manifest(
    partition_dir: Path,
    *,
    episode_complete: Optional[bool] = None,
) -> dict:
    """Scan Parquet files in *partition_dir* and return a manifest dict.

    Reads only Parquet footers (metadata), not full row data. If
    *episode_complete* is ``None`` the existing value is preserved (or
    defaults to ``False``). Returns ``{}`` when no readable Parquet files
    exist so ``write_manifest`` can no-op.
    """
    # Stable ordering for the files list in the JSON.
    parquet_files = sorted(partition_dir.glob("*.parquet"))
    # Empty partition: nothing to advertise.
    if not parquet_files:
        return {}

    # Aggregates across all readable parts.
    total_rows = 0
    min_step: Optional[int] = None
    max_step: Optional[int] = None

    filenames: list[str] = []
    for pf in parquet_files:
        try:
            # Footer-only read for num_rows and column stats.
            meta = pq.read_metadata(str(pf))
        except Exception:
            logger.warning("Skipping unreadable file %s", pf)
            continue
        # Track basename for the manifest files array.
        filenames.append(pf.name)
        total_rows += meta.num_rows

        # Walk row groups looking for step_index min/max stats.
        for rg_idx in range(meta.num_row_groups):
            rg = meta.row_group(rg_idx)
            for col_idx in range(rg.num_columns):
                col = rg.column(col_idx)
                # Only step_index contributes to the range fields.
                if col.path_in_schema == "step_index" and col.statistics:
                    stats = col.statistics
                    if stats.has_min_max:
                        lo, hi = stats.min, stats.max
                        min_step = lo if min_step is None else min(min_step, lo)
                        max_step = hi if max_step is None else max(max_step, hi)

    # Merge with prior sidecar when preserving episode_complete.
    existing = _read_existing(partition_dir / "_manifest.json")

    # None means "keep prior / default False".
    if episode_complete is None:
        episode_complete = existing.get("episode_complete", False)

    # Derive a readable partition label from path segments.
    rel_parts = partition_dir.parts
    try:
        # Find modality segment (state|action|vision|event) and join from there.
        modality_idx = next(
            i for i, p in enumerate(rel_parts) if p in ("state", "action", "vision", "event")
        )
        partition_label = "/".join(rel_parts[modality_idx:])
    except StopIteration:
        # Fallback when layout does not match expectations.
        partition_label = str(partition_dir)

    # Assemble the sidecar document.
    return {
        "partition": partition_label,
        "files": filenames,
        "total_rows": total_rows,
        "min_step_index": min_step,
        "max_step_index": max_step,
        "episode_complete": episode_complete,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(
    partition_dir: Path,
    *,
    episode_complete: Optional[bool] = None,
) -> None:
    """Build and atomically write ``_manifest.json`` for *partition_dir*.

    Uses a temporary ``.json.tmp`` file then ``replace`` so readers never see
    a partial JSON document. No-ops when ``build_manifest`` returns empty.
    """
    # Compute the document from footers (+ optional episode flag).
    manifest = build_manifest(partition_dir, episode_complete=episode_complete)
    # Nothing to write for empty partitions.
    if not manifest:
        return

    # Final sidecar path.
    manifest_path = partition_dir / "_manifest.json"
    # Temp path in the same directory for atomic replace.
    tmp = manifest_path.with_suffix(".json.tmp")
    try:
        # Pretty-print with trailing newline for human diffs.
        tmp.write_text(json.dumps(manifest, indent=2) + "\n")
        # Atomic replace on POSIX.
        tmp.replace(manifest_path)
        logger.debug("Wrote manifest %s (%d rows)", manifest_path, manifest["total_rows"])
    except OSError:
        logger.exception("Failed to write manifest %s", manifest_path)
        # Best-effort cleanup of the temp file.
        if tmp.exists():
            tmp.unlink(missing_ok=True)
