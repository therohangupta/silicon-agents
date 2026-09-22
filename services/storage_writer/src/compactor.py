"""
Background Parquet compaction worker.

Periodically scans partition directories under the Parquet root, merges small
part files into larger sorted files, deletes the old parts, and refreshes the
partition manifest. Target combined size is ~128 MB. Sorting uses
``(step_index, sequence_id)`` when those columns exist so ML/replay tools can
range-read efficiently.
"""

# Sleep between compaction passes; CancelledError propagation.
import asyncio
# Progress and failure logs.
import logging
# Timestamp component in compacted filenames.
import time
# Unique suffix to avoid name collisions.
import uuid
from pathlib import Path

# Arrow concat/sort and Parquet I/O.
import pyarrow as pa
import pyarrow.parquet as pq

# Refresh sidecars after merge.
from .manifest import write_manifest

# Module logger.
logger = logging.getLogger(__name__)

# Stop merging once a single file is around this size (bytes).
TARGET_FILE_BYTES = 128 * 1024 * 1024  # 128 MB
# Default seconds between full-tree compaction passes.
COMPACTION_INTERVAL_SECS = 300  # 5 minutes


def _total_size(files: list[Path]) -> int:
    """Sum on-disk sizes for existing paths in *files*."""
    return sum(f.stat().st_size for f in files if f.exists())


def _compact_partition(partition_dir: Path) -> None:
    """Merge and sort all part files in a single partition directory.

    No-ops when there is at most one Parquet file. Reads all readable parts,
    concatenates, optionally sorts, writes ``compacted-{ts}_{uuid}.parquet``,
    deletes the old parts, and updates the manifest (episode_complete True if
    any ``done`` value was true).
    """
    # Stable list of current parts.
    parquet_files = sorted(partition_dir.glob("*.parquet"))

    # Nothing to merge.
    if len(parquet_files) <= 1:
        return

    # Combined size of candidates (informational / early-out historically).
    total = _total_size(parquet_files)
    # Historical guard: single large file already at target (unreachable after <=1 check).
    if total >= TARGET_FILE_BYTES and len(parquet_files) == 1:
        return

    # Load each part into memory as an Arrow table.
    tables = []
    for pf in parquet_files:
        try:
            tables.append(pq.read_table(str(pf)))
        except Exception:
            logger.warning("Skipping unreadable file during compaction: %s", pf)

    # All files unreadable: leave directory untouched.
    if not tables:
        return

    # Unify schemas with promote_options for evolving columns.
    combined = pa.concat_tables(tables, promote_options="default")

    # Build sort keys only for columns that exist.
    sort_cols = []
    col_names = set(combined.schema.names)
    if "step_index" in col_names:
        sort_cols.append(("step_index", "ascending"))
    if "sequence_id" in col_names:
        sort_cols.append(("sequence_id", "ascending"))

    # Sort when we have at least one key.
    if sort_cols:
        combined = combined.sort_by(sort_cols)

    # Unique compacted output name.
    compacted_name = f"compacted-{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}.parquet"
    compacted_path = partition_dir / compacted_name

    # Write the merged table with Snappy.
    pq.write_table(combined, str(compacted_path), compression="snappy")

    # Remove the pre-compaction parts (not the new compacted file).
    for pf in parquet_files:
        try:
            pf.unlink()
        except OSError:
            logger.warning("Failed to remove old part file: %s", pf)

    # Detect episode completion from the done column if present.
    has_done = False
    if "done" in col_names:
        done_col = combined.column("done")
        has_done = any(v.as_py() for v in done_col if v.is_valid)

    # Refresh sidecar; force episode_complete when done seen, else preserve.
    write_manifest(
        partition_dir,
        episode_complete=True if has_done else None,
    )

    # Summarize the pass for operators.
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
    # Use a set so multiple parts in one dir yield one entry.
    partitions = set()
    for pf in root.rglob("*.parquet"):
        partitions.add(pf.parent)
    # Stable order for deterministic logs.
    return sorted(partitions)


async def run_compaction_loop(
    root: str,
    interval_secs: float = COMPACTION_INTERVAL_SECS,
) -> None:
    """Run compaction periodically until cancelled.

    Sleeps *interval_secs*, discovers partitions under *root*, and compacts
    each independently. Propagates ``CancelledError`` for clean shutdown;
    other errors are logged and the loop continues.
    """
    # Normalize root to Path once.
    root_path = Path(root)
    logger.info(
        "Compaction loop started: root=%s, interval=%ds",
        root_path, interval_secs,
    )

    while True:
        # Wait between passes (also the cancellation point).
        await asyncio.sleep(interval_secs)

        try:
            # Find every directory that currently holds Parquet.
            partitions = _discover_partitions(root_path)
            if partitions:
                logger.info("Compaction pass: scanning %d partitions", len(partitions))

            # Compact each partition; isolate failures per directory.
            for partition_dir in partitions:
                try:
                    _compact_partition(partition_dir)
                except Exception:
                    logger.exception("Compaction failed for %s", partition_dir)

        except asyncio.CancelledError:
            # Let main._run finish cancellation.
            raise
        except Exception:
            # Keep the loop alive after unexpected pass-level errors.
            logger.exception("Compaction pass failed")
