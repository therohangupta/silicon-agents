"""NATS JetStream implementation of the MessageBus interface.

Requires ``nats-py``: ``pip install nats-py``.

This module is the concrete message-bus plane used by telemetry publishers
and the memory plane's NATS projection. It wraps nats-py's JetStream APIs
behind ``MessageBus`` / ``Subscription`` so callers never import nats types
directly. Pull subscriptions are used when a ``queue_group`` is requested
(consumer-group load balancing); otherwise a durable push subscription is
created.
"""

from __future__ import annotations

# asyncio is available for future batching helpers; nats-py is itself async.
import asyncio
# logging reports connect/fetch/unsubscribe issues without crashing callers.
import logging
# Optional for client/js handles and optional stream kwargs.
from typing import Optional

# nats-py top-level connect helper and error types.
import nats
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.api import (
    ConsumerConfig,
    DeliverPolicy,
    AckPolicy,
    StreamConfig,
    StorageType,
    RetentionPolicy,
)

# Abstract Message / MessageBus / Subscription from this package.
from . import Message, MessageBus, Subscription

# Module logger for connection lifecycle and fetch errors.
logger = logging.getLogger(__name__)

# Map our string deliver_policy names onto nats-py enums.
_DELIVER_MAP = {
    "all": DeliverPolicy.ALL,
    "new": DeliverPolicy.NEW,
    "last": DeliverPolicy.LAST,
}

# Map our string storage names onto nats-py StorageType.
_STORAGE_MAP = {
    "file": StorageType.FILE,
    "memory": StorageType.MEMORY,
}


class _NatsSubscription(Subscription):
    """Wraps a NATS JetStream pull or push subscription."""

    def __init__(self, sub, *, is_pull: bool = False):
        # Underlying nats-py subscription object.
        self._sub = sub
        # True when created via pull_subscribe (queue_group path).
        self._is_pull = is_pull

    async def next_msg(self, timeout: float = 5.0) -> Optional[Message]:
        """Fetch the next message, adapting pull vs push APIs to ``Message``."""
        try:
            # Only when (self._is_pull).
            if self._is_pull:
                # Pull consumer: fetch a batch of 1 with the caller's timeout.
                msgs = await self._sub.fetch(batch=1, timeout=timeout)
                # Only when (not msgs).
                if not msgs:
                    # Hand ``None`` back to the caller.
                    return None
                # Local ``raw`` ← msgs[0].
                raw = msgs[0]
            else:
                # Push consumer: block on next_msg.
                raw = await self._sub.next_msg(timeout=timeout)

            # Adapt nats-py message fields into our Message dataclass.
            return Message(
                # Local ``subject`` ← raw.subject,.
                subject=raw.subject,
                # Local ``data`` ← raw.data,.
                data=raw.data,
                # Local ``headers`` ← dict(raw.headers) if raw.headers else {},.
                headers=dict(raw.headers) if raw.headers else {},
                # Local ``sequence`` ← raw.metadata.sequence.stream if raw.metadata else None,.
                sequence=raw.metadata.sequence.stream if raw.metadata else None,
                # Local ``_ack_func`` ← raw.ack,.
                _ack_func=raw.ack,
            )
        # On except nats.errors.TimeoutError: recover or re-raise as appropriate.
        except nats.errors.TimeoutError:
            # Timeout is a normal idle condition — return None to the caller.
            return None
        # On except Exception: recover or re-raise as appropriate.
        except Exception:
            # Unexpected transport errors are logged; caller sees None.
            logger.exception("Error fetching next message")
            # Hand ``None`` back to the caller.
            return None

    async def ack(self, msg: Message) -> None:
        """Invoke the transport ack bound onto ``msg`` at fetch time."""
        if msg._ack_func and callable(msg._ack_func):
            # Await ``msg._ack_func`` and continue once it completes.
            await msg._ack_func()

    async def unsubscribe(self) -> None:
        """Detach from the consumer; swallow unsubscribe races."""
        try:
            # Await ``self._sub.unsubscribe`` and continue once it completes.
            await self._sub.unsubscribe()
        # On except Exception: recover or re-raise as appropriate.
        except Exception:
            # Log at debug so operators can diagnose this path.
            logger.debug("Error unsubscribing", exc_info=True)


class NatsJetStreamBus(MessageBus):
    """NATS JetStream message bus.

    Lightweight, single-binary server with persistent pub/sub, replay,
    consumer groups, and batching via pull consumers.
    """

    def __init__(self, url: str = "nats://localhost:4222"):
        # NATS server URL (may be overridden via packages.config.NATS_URL).
        self._url = url
        # Connected nats-py client, or None before connect().
        self._nc: Optional[NatsClient] = None
        # JetStream context derived from the client.
        self._js: Optional[JetStreamContext] = None

    async def connect(self) -> None:
        """Open the NATS connection and bind the JetStream context."""
        self._nc = await nats.connect(self._url)
        # Bind ``_js`` from self._nc.jetstream() for later use on this instance.
        self._js = self._nc.jetstream()
        # Log at info so operators can diagnose this path.
        logger.info("Connected to NATS JetStream at %s", self._url)

    async def publish(
        self,
        subject: str,
        data: bytes,
        headers: Optional[dict[str, str]] = None,
        stream: Optional[str] = None,
    ) -> None:
        """Publish ``data`` to ``subject``, optionally pinning a stream name."""
        assert self._js is not None, "Call connect() first"
        # Only when (stream).
        if stream:
            # Explicit stream hint for multi-stream deployments.
            await self._js.publish(subject, data, headers=headers, stream=stream)
        else:
            # Let JetStream route by subject interest.
            await self._js.publish(subject, data, headers=headers)

    async def subscribe(
        self,
        subject: str,
        consumer_name: str,
        deliver_policy: str = "new",
        queue_group: Optional[str] = None,
        stream: Optional[str] = None,
    ) -> Subscription:
        """Create a durable pull (queue group) or push subscription."""
        assert self._js is not None, "Call connect() first"

        # Resolve deliver policy string; default to NEW for unknown values.
        dp = _DELIVER_MAP.get(deliver_policy, DeliverPolicy.NEW)

        # Only when (queue_group).
        if queue_group:
            # Queue groups use pull consumers with explicit ack.
            cfg = ConsumerConfig(
                # Local ``durable_name`` ← consumer_name,.
                durable_name=consumer_name,
                # Local ``deliver_policy`` ← dp,.
                deliver_policy=dp,
                # Local ``ack_policy`` ← AckPolicy.EXPLICIT,.
                ack_policy=AckPolicy.EXPLICIT,
                # Local ``filter_subject`` ← subject,.
                filter_subject=subject,
            )
            pull_kwargs: dict = {
                "durable": consumer_name,
                "config": cfg,
            }
            # Only when (stream).
            if stream:
                pull_kwargs["stream"] = stream
            # Local ``sub`` ← await self._js.pull_subscribe(subject, **pull_kwargs).
            sub = await self._js.pull_subscribe(subject, **pull_kwargs)
            # Hand ``_NatsSubscription(sub, is_pull=True)`` back to the caller.
            return _NatsSubscription(sub, is_pull=True)
        else:
            # Single-consumer durable push subscription.
            sub = await self._js.subscribe(
                subject,
                # Local ``durable`` ← consumer_name,.
                durable=consumer_name,
                # Local ``deliver_policy`` ← dp,.
                deliver_policy=dp,
            )
            # Hand ``_NatsSubscription(sub, is_pull=False)`` back to the caller.
            return _NatsSubscription(sub, is_pull=False)

    async def ensure_stream(
        self,
        name: str,
        subjects: list[str],
        max_age: int = 7 * 24 * 3600,
        storage: str = "file",
        replicas: int = 1,
    ) -> None:
        """Create or update a JetStream stream with LIMITS retention."""
        assert self._js is not None, "Call connect() first"

        # Local ``cfg`` ← StreamConfig(.
        cfg = StreamConfig(
            # Local ``name`` ← name,.
            name=name,
            # Local ``subjects`` ← subjects,.
            subjects=subjects,
            # Local ``retention`` ← RetentionPolicy.LIMITS,.
            retention=RetentionPolicy.LIMITS,
            # Local ``max_age`` ← max_age,.
            max_age=max_age,
            # Local ``storage`` ← _STORAGE_MAP.get(storage, StorageType.FILE),.
            storage=_STORAGE_MAP.get(storage, StorageType.FILE),
            # Local ``num_replicas`` ← replicas,.
            num_replicas=replicas,
        )

        # Try the fallible work below.
        try:
            # If any subject already belongs to a stream, update that config.
            await self._js.find_stream_name_by_subject(subjects[0])
            # Await ``self._js.update_stream`` and continue once it completes.
            await self._js.update_stream(cfg)
            # Log at info so operators can diagnose this path.
            logger.info("Updated existing NATS stream '%s'", name)
        # On except nats.js.errors.NotFoundError: recover or re-raise as appropriate.
        except nats.js.errors.NotFoundError:
            # No existing stream — create fresh.
            await self._js.add_stream(cfg)
            # Log at info so operators can diagnose this path.
            logger.info("Created NATS stream '%s' with subjects %s", name, subjects)

    async def close(self) -> None:
        """Drain the connection and clear client handles."""
        if self._nc is not None:
            # Await ``self._nc.drain`` and continue once it completes.
            await self._nc.drain()
            # Bind ``_nc`` from None for later use on this instance.
            self._nc = None
            # Bind ``_js`` from None for later use on this instance.
            self._js = None
            # Log at info so operators can diagnose this path.
            logger.info("Disconnected from NATS JetStream")
