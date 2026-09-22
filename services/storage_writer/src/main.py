"""
Storage writer service entrypoint.

Connects to NATS JetStream, ensures the TELEMETRY stream exists, then runs
two concurrent tasks: the Parquet pull-consumer worker and the compaction
loop. Handles SIGINT/SIGTERM via an asyncio Event so Docker stop and Ctrl-C
flush remaining buffers cleanly before closing the bus.

Usage: ``python -m services.storage_writer.src.main [--nats-url URL]``
"""

# argparse for --nats-url override.
import argparse
# asyncio.run and task orchestration.
import asyncio
# Process logging setup.
import logging
# POSIX signal registration for graceful shutdown.
import signal

# Shared NATS URL and Parquet root from packages.config.
from packages.config import NATS_URL, PARQUET_STORAGE_ROOT
# JetStream bus used for consume + ensure_stream.
from packages.message_bus.nats_jetstream import NatsJetStreamBus

# Background merge/sort of small part files.
from .compactor import run_compaction_loop
# Pull consumer that writes Parquet.
from .worker import run_storage_writer

# Configure root logging once for the process.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
# Module logger for startup messages.
logger = logging.getLogger(__name__)


async def _run(nats_url: str) -> None:
    """Connect the bus, start worker + compaction, wait for stop signals.

    Ensures the TELEMETRY stream with subject ``telemetry.>`` so this process
    can consume even if telemetry started later. Cancels both tasks on
    SIGINT/SIGTERM, awaits CancelledError, then closes the bus.
    """
    # Build bus pointed at the CLI/env URL.
    bus = NatsJetStreamBus(url=nats_url)
    # Open the NATS connection.
    await bus.connect()
    # Create/update the stream telemetry also ensures (idempotent).
    await bus.ensure_stream("TELEMETRY", ["telemetry.>"])

    # Start the pull-consumer writer as a background task.
    writer_task = asyncio.create_task(run_storage_writer(bus))
    # Start compaction against the configured Parquet root.
    compaction_task = asyncio.create_task(run_compaction_loop(PARQUET_STORAGE_ROOT))

    # Event flipped by signal handlers to exit the wait.
    stop = asyncio.Event()
    # Running loop needed for add_signal_handler.
    loop = asyncio.get_running_loop()
    # Register both Ctrl-C and docker stop equivalents.
    for sig in (signal.SIGINT, signal.SIGTERM):
        # stop.set is sync and safe as a signal callback.
        loop.add_signal_handler(sig, stop.set)

    # Block until a stop signal arrives.
    await stop.wait()

    # Cancel writer and compaction; ignore CancelledError from each.
    for t in (writer_task, compaction_task):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            # Expected on shutdown.
            pass
    # Release NATS resources.
    await bus.close()


def main() -> None:
    """Parse CLI args and run the async supervisor via asyncio.run.

    ``--nats-url`` defaults to ``NATS_URL`` from shared config so Compose and
    bare-metal runs stay aligned. Logs the chosen URL then blocks in ``_run``.
    """
    # Build the small CLI.
    parser = argparse.ArgumentParser(description="Telemetry storage writer")
    # Allow overriding NATS without changing env files.
    parser.add_argument("--nats-url", default=NATS_URL, help="NATS server URL")
    # Parse argv.
    args = parser.parse_args()

    # Announce startup for operators watching container logs.
    logger.info("Starting storage writer, NATS=%s", args.nats_url)
    # Drive the async lifecycle until signals fire.
    asyncio.run(_run(args.nats_url))


# Script guard for direct execution of this file.
if __name__ == "__main__":
    main()
