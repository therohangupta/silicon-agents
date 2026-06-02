"""
Partition manifest management.

Writes and updates a ``_manifest.json`` sidecar inside each Parquet
partition directory.  The manifest stores lightweight metadata derived
from Parquet file footers (row counts, step_index ranges) so that
downstream consumers can discover partitions and episodes without
scanning every file.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


def _read_existing(manifest_path: Path) -> dict:
    """Return the existing manifest dict, or a blank skeleton."""
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt manifest at %s — rebuilding", manifest_path)
    return {}


def build_manifest(
    partition_dir: Path,
    *,
    episode_complete: Optional[bool] = None,
) -> dict:
    """Scan Parquet files in *partition_dir* and return a manifest dict.

    Reads only Parquet footers (metadata), not full row data.
    If *episode_complete* is ``None`` the existing value is preserved
    (or defaults to ``False``).
    """
    parquet_files = sorted(partition_dir.glob("*.parquet"))
    if not parquet_files:
        return {}

    total_rows = 0
    min_step: Optional[int] = None
    max_step: Optional[int] = None

    filenames: list[str] = []
    for pf in parquet_files:
        try:
            meta = pq.read_metadata(str(pf))
        except Exception:
            logger.warning("Skipping unreadable file %s", pf)
            continue
        filenames.append(pf.name)
        total_rows += meta.num_rows

        for rg_idx in range(meta.num_row_groups):
            rg = meta.row_group(rg_idx)
            for col_idx in range(rg.num_columns):
                col = rg.column(col_idx)
                if col.path_in_schema == "step_index" and col.statistics:
                    stats = col.statistics
                    if stats.has_min_max:
                        lo, hi = stats.min, stats.max
                        min_step = lo if min_step is None else min(min_step, lo)
                        max_step = hi if max_step is None else max(max_step, hi)

    existing = _read_existing(partition_dir / "_manifest.json")

    if episode_complete is None:
        episode_complete = existing.get("episode_complete", False)

    rel_parts = partition_dir.parts
    try:
        modality_idx = next(
            i for i, p in enumerate(rel_parts) if p in ("state", "action", "vision", "event")
        )
        partition_label = "/".join(rel_parts[modality_idx:])
    except StopIteration:
        partition_label = str(partition_dir)

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
    """Build and atomically write ``_manifest.json`` for *partition_dir*."""
    manifest = build_manifest(partition_dir, episode_complete=episode_complete)
    if not manifest:
        return

    manifest_path = partition_dir / "_manifest.json"
    tmp = manifest_path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(manifest, indent=2) + "\n")
        tmp.replace(manifest_path)
        logger.debug("Wrote manifest %s (%d rows)", manifest_path, manifest["total_rows"])
    except OSError:
        logger.exception("Failed to write manifest %s", manifest_path)
        if tmp.exists():
            tmp.unlink(missing_ok=True)
