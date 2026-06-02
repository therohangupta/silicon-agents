"""
Background Parquet compaction worker.

Periodically scans partition directories, merges small part files into
larger sorted files, and updates the partition manifest.

Target file size: ~128 MB (configurable).  Sorting is by
``(step_index, sequence_id)`` to enable efficient range reads for ML
pipelines and replay tools.
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .manifest import write_manifest

logger = logging.getLogger(__name__)

TARGET_FILE_BYTES = 128 * 1024 * 1024  # 128 MB
COMPACTION_INTERVAL_SECS = 300  # 5 minutes


def _total_size(files: list[Path]) -> int:
    return sum(f.stat().st_size for f in files if f.exists())


def _compact_partition(partition_dir: Path) -> None:
    """Merge and sort all part files in a single partition directory."""
    parquet_files = sorted(partition_dir.glob("*.parquet"))

    if len(parquet_files) <= 1:
        return

    total = _total_size(parquet_files)
    if total >= TARGET_FILE_BYTES and len(parquet_files) == 1:
        return

    tables = []
    for pf in parquet_files:
        try:
            tables.append(pq.read_table(str(pf)))
        except Exception:
            logger.warning("Skipping unreadable file during compaction: %s", pf)

    if not tables:
        return

    combined = pa.concat_tables(tables, promote_options="default")

    sort_cols = []
    col_names = set(combined.schema.names)
    if "step_index" in col_names:
        sort_cols.append(("step_index", "ascending"))
    if "sequence_id" in col_names:
        sort_cols.append(("sequence_id", "ascending"))

    if sort_cols:
        combined = combined.sort_by(sort_cols)

    compacted_name = f"compacted-{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}.parquet"
    compacted_path = partition_dir / compacted_name

    pq.write_table(combined, str(compacted_path), compression="snappy")

    for pf in parquet_files:
        try:
            pf.unlink()
        except OSError:
            logger.warning("Failed to remove old part file: %s", pf)

    has_done = False
    if "done" in col_names:
        done_col = combined.column("done")
        has_done = any(v.as_py() for v in done_col if v.is_valid)

    write_manifest(
        partition_dir,
        episode_complete=True if has_done else None,
    )

    logger.info(
        "Compacted %d files (%d rows, %.1f KB -> %.1f KB) in %s",
        len(parquet_files),
        combined.num_rows,
        total / 1024,
        compacted_path.stat().st_size / 1024,
        partition_dir,
    )


def _discover_partitions(root: Path) -> list[Path]:
    """Find all leaf partition directories (those containing .parquet files)."""
    partitions = set()
    for pf in root.rglob("*.parquet"):
        partitions.add(pf.parent)
    return sorted(partitions)


async def run_compaction_loop(
    root: str,
    interval_secs: float = COMPACTION_INTERVAL_SECS,
) -> None:
    """Run compaction periodically until cancelled."""
    root_path = Path(root)
    logger.info(
        "Compaction loop started: root=%s, interval=%ds",
        root_path, interval_secs,
    )

    while True:
        await asyncio.sleep(interval_secs)

        try:
            partitions = _discover_partitions(root_path)
            if partitions:
                logger.info("Compaction pass: scanning %d partitions", len(partitions))

            for partition_dir in partitions:
                try:
                    _compact_partition(partition_dir)
                except Exception:
                    logger.exception("Compaction failed for %s", partition_dir)

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Compaction pass failed")
