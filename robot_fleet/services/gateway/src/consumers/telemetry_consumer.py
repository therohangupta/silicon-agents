"""
NATS JetStream consumer for real-time telemetry fan-out.

Consumes from the TELEMETRY stream (subject ``telemetry.>``) as a durable
push consumer ``gateway-realtime`` and:
  1. Caches the latest event per (robot_id, stream_name) for REST queries.
  2. Fans out events to browsers connected via WS /ws/telemetry/{robot_id}.
"""

import asyncio
import logging
from typing import Optional

from google.protobuf.json_format import MessageToDict

from packages.proto.telemetry_pb2 import TelemetryEvent
from packages.message_bus import MessageBus, Subscription

logger = logging.getLogger(__name__)

# robot_id -> {stream_name -> dict (JSON-friendly event)}
_latest_cache: dict[str, dict[str, dict]] = {}

# robot_id -> set of asyncio.Queue (one per connected WS client)
_ws_subscribers: dict[str, set[asyncio.Queue]] = {}


def get_latest_state(robot_id: str) -> dict[str, dict]:
    """Return the latest cached events for *robot_id*, keyed by stream_name."""
    return dict(_latest_cache.get(robot_id, {}))


def subscribe_ws(robot_id: str) -> asyncio.Queue:
    """Register a new WS client for *robot_id*. Returns a queue for receiving events."""
    q: asyncio.Queue = asyncio.Queue(maxsize=256)
    _ws_subscribers.setdefault(robot_id, set()).add(q)
    return q


def unsubscribe_ws(robot_id: str, q: asyncio.Queue) -> None:
    """Remove a WS client's queue."""
    subs = _ws_subscribers.get(robot_id)
    if subs:
        subs.discard(q)
        if not subs:
            del _ws_subscribers[robot_id]


async def run_telemetry_consumer(bus: MessageBus) -> None:
    """
    Main consumer loop. Runs until cancelled.

    Subscribes to ``telemetry.>`` as durable consumer ``gateway-realtime``
    with deliver_policy=new (no replay of old events at startup).
    """
    sub = await bus.subscribe(
        subject="telemetry.>",
        consumer_name="gateway-realtime",
        deliver_policy="new",
    )
    logger.info("Gateway telemetry consumer started on telemetry.>")

    try:
        while True:
            msg = await sub.next_msg(timeout=5.0)
            if msg is None:
                continue

            try:
                event = TelemetryEvent()
                event.ParseFromString(msg.data)

                robot_id = event.robot_id
                stream_name = event.stream_name

                event_dict = MessageToDict(
                    event,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=True,
                )

                # Update latest-state cache
                _latest_cache.setdefault(robot_id, {})[stream_name] = event_dict

                # Fan out to connected WS clients
                queues = _ws_subscribers.get(robot_id)
                if queues:
                    for q in list(queues):
                        try:
                            q.put_nowait(event_dict)
                        except asyncio.QueueFull:
                            pass

            except Exception:
                logger.exception("Error processing telemetry message")

    except asyncio.CancelledError:
        logger.info("Gateway telemetry consumer shutting down")
        await sub.unsubscribe()
