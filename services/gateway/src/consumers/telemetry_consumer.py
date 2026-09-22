"""
NATS JetStream consumer for real-time telemetry fan-out to the dashboard.

This module is the gateway's bridge from the TELEMETRY JetStream stream
(subject pattern ``telemetry.>``) into:

1. An in-memory latest-event cache keyed by ``(agent_id, stream_name)`` used by
   ``GET /api/telemetry/{agent_id}/latest``.
2. Per-agent sets of ``asyncio.Queue`` objects feeding
   ``WS /ws/telemetry/{agent_id}`` clients.

The durable consumer name is ``gateway-realtime`` with ``deliver_policy=new``
so reconnecting the gateway does not replay the entire historical stream into
browsers—only events published after subscribe. Queue overflow drops events
for that subscriber (``QueueFull``) rather than blocking the consumer loop.

Lifecycle: ``run_telemetry_consumer(bus)`` is scheduled as an asyncio task in
``app.lifespan``. Cancellation triggers unsubscribe and clean exit. The gateway
still serves REST if NATS never connects; this consumer simply never starts.
"""

import asyncio
import logging
from typing import Optional

# Convert protobuf TelemetryEvent into JSON-serializable dicts for WS/REST.
from google.protobuf.json_format import MessageToDict

# Wire format for agent telemetry published on the bus.
from packages.proto.telemetry_pb2 import TelemetryEvent
# Abstract bus + subscription types (NatsJetStreamBus implements MessageBus).
from packages.message_bus import MessageBus, Subscription

# Logger for subscribe/processing/shutdown diagnostics.
logger = logging.getLogger(__name__)

# agent_id -> {stream_name -> dict (JSON-friendly event)}
# Updated on every successfully parsed message; read by REST latest endpoint.
_latest_cache: dict[str, dict[str, dict]] = {}

# agent_id -> set of asyncio.Queue (one per connected WS client)
# Fan-out targets registered by subscribe_ws / cleared by unsubscribe_ws.
_ws_subscribers: dict[str, set[asyncio.Queue]] = {}


def get_latest_state(agent_id: str) -> dict[str, dict]:
    """
    Return a shallow copy of the latest cached events for one agent.

    Purpose:
        Let REST and WebSocket ``initial_state`` responses snapshot current
        stream payloads without exposing the mutable cache dict.

    Args:
        agent_id: Fleet agent instance id whose streams should be returned.

    Returns:
        Mapping of ``stream_name`` → event dict. Empty dict if nothing cached.

    Side effects:
        None (copy isolates callers from later cache mutations).

    Failure behavior:
        Never raises for unknown agents; returns ``{}``.
    """
    # Copy the inner mapping so callers cannot mutate _latest_cache by accident.
    return dict(_latest_cache.get(agent_id, {}))


def subscribe_ws(agent_id: str) -> asyncio.Queue:
    """
    Register a WebSocket client to receive telemetry for ``agent_id``.

    Purpose:
        Allocate a bounded queue and attach it to the per-agent subscriber set
        so ``run_telemetry_consumer`` can push events without awaiting sockets.

    Args:
        agent_id: Agent whose events should be delivered to this queue.

    Returns:
        A new ``asyncio.Queue`` with ``maxsize=256`` owned by the caller until
        ``unsubscribe_ws``.

    Side effects:
        Mutates ``_ws_subscribers``; creates the agent key if missing.

    Failure behavior:
        Does not raise under normal use; queue creation is local memory only.
    """
    # Bound the queue so a slow browser cannot grow memory unbounded.
    q: asyncio.Queue = asyncio.Queue(maxsize=256)
    # Ensure the agent has a subscriber set, then add this queue.
    _ws_subscribers.setdefault(agent_id, set()).add(q)
    return q


def unsubscribe_ws(agent_id: str, q: asyncio.Queue) -> None:
    """
    Detach a WebSocket client's queue from telemetry fan-out.

    Purpose:
        Prevent further puts after disconnect and reclaim empty agent keys.

    Args:
        agent_id: Agent the queue was subscribed under.
        q: The exact queue instance returned by ``subscribe_ws``.

    Returns:
        None.

    Side effects:
        Removes ``q`` from the set; deletes the agent entry when the set empties.

    Failure behavior:
        No-op if the agent or queue is already gone (``discard`` / missing key).
    """
    # Look up the live subscriber set for this agent (may be None).
    subs = _ws_subscribers.get(agent_id)
    if subs:
        # discard avoids KeyError if double-unsubscribe occurs.
        subs.discard(q)
        # Drop empty sets so the dict does not retain idle agent keys forever.
        if not subs:
            del _ws_subscribers[agent_id]


async def run_telemetry_consumer(bus: MessageBus) -> None:
    """
    Main durable consumer loop: pull TELEMETRY messages until cancelled.

    Purpose:
        Subscribe to ``telemetry.>`` as ``gateway-realtime``, parse each
        ``TelemetryEvent``, update the latest-state cache, and fan out to WS
        queues without blocking on slow clients.

    Args:
        bus: Connected ``MessageBus`` (typically ``NatsJetStreamBus``) that
            already has the TELEMETRY stream ensured by lifespan.

    Returns:
        None (runs until ``CancelledError``).

    Side effects:
        Mutates ``_latest_cache`` and pushes to subscriber queues; unsubscribes
        on cancellation.

    Failure behavior:
        Per-message parse/handler errors are logged and skipped. Subscribe
        failures propagate to lifespan. ``CancelledError`` triggers clean
        unsubscribe. ``QueueFull`` drops that event for that subscriber only.
        ``next_msg`` timeouts return ``None`` and the loop continues (idle poll).
    """
    # Durable push/pull subscription; deliver_policy=new skips historical replay.
    sub = await bus.subscribe(
        subject="telemetry.>",
        consumer_name="gateway-realtime",
        deliver_policy="new",
    )
    logger.info("Gateway telemetry consumer started on telemetry.>")

    try:
        while True:
            # Wait up to 5s for the next message; None means idle timeout.
            msg = await sub.next_msg(timeout=5.0)
            if msg is None:
                # No message this interval; loop again so cancellation can land.
                continue

            try:
                # Allocate an empty protobuf and fill from the wire bytes.
                event = TelemetryEvent()
                event.ParseFromString(msg.data)

                # Keys used for cache indexing and WS routing.
                agent_id = event.agent_id
                stream_name = event.stream_name

                # Preserve proto field names and include empty fields for UI stability.
                event_dict = MessageToDict(
                    event,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=True,
                )

                # Update latest-state cache (overwrite prior event for this stream).
                _latest_cache.setdefault(agent_id, {})[stream_name] = event_dict

                # Fan out to connected WS clients for this agent only.
                queues = _ws_subscribers.get(agent_id)
                if queues:
                    # list() snapshot so unsubscribe during iteration is safe.
                    for q in list(queues):
                        try:
                            # Non-blocking put; drop if the client is too slow.
                            q.put_nowait(event_dict)
                        except asyncio.QueueFull:
                            # Skip this subscriber for this event only.
                            pass

            except Exception:
                # Keep the consumer alive across bad payloads / unexpected bugs.
                logger.exception("Error processing telemetry message")

    except asyncio.CancelledError:
        # Lifespan cancelled the task; unsubscribe then allow cancellation to finish.
        logger.info("Gateway telemetry consumer shutting down")
        await sub.unsubscribe()
