"""
Storage writer service entrypoint.

Connects to NATS JetStream and consumes telemetry events, writing them
to partitioned Parquet files.

Usage: python -m services.storage_writer.src.main [--nats-url URL]
"""

import argparse
import asyncio
import logging
import signal

from packages.config import NATS_URL, PARQUET_STORAGE_ROOT
from packages.message_bus.nats_jetstream import NatsJetStreamBus

from .compactor import run_compaction_loop
from .worker import run_storage_writer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def _run(nats_url: str) -> None:
    bus = NatsJetStreamBus(url=nats_url)
    await bus.connect()
    await bus.ensure_stream("TELEMETRY", ["telemetry.>"])

    writer_task = asyncio.create_task(run_storage_writer(bus))
    compaction_task = asyncio.create_task(run_compaction_loop(PARQUET_STORAGE_ROOT))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()

    for t in (writer_task, compaction_task):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
    await bus.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telemetry storage writer")
    parser.add_argument("--nats-url", default=NATS_URL, help="NATS server URL")
    args = parser.parse_args()

    logger.info("Starting storage writer, NATS=%s", args.nats_url)
    asyncio.run(_run(args.nats_url))


if __name__ == "__main__":
    main()
