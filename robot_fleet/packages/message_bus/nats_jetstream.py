"""
NATS JetStream implementation of the MessageBus interface.

Requires ``nats-py``:  pip install nats-py
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

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

from . import Message, MessageBus, Subscription

logger = logging.getLogger(__name__)

_DELIVER_MAP = {
    "all": DeliverPolicy.ALL,
    "new": DeliverPolicy.NEW,
    "last": DeliverPolicy.LAST,
}

_STORAGE_MAP = {
    "file": StorageType.FILE,
    "memory": StorageType.MEMORY,
}


class _NatsSubscription(Subscription):
    """Wraps a NATS JetStream pull or push subscription."""

    def __init__(self, sub, *, is_pull: bool = False):
        self._sub = sub
        self._is_pull = is_pull

    async def next_msg(self, timeout: float = 5.0) -> Optional[Message]:
        try:
            if self._is_pull:
                msgs = await self._sub.fetch(batch=1, timeout=timeout)
                if not msgs:
                    return None
                raw = msgs[0]
            else:
                raw = await self._sub.next_msg(timeout=timeout)

            return Message(
                subject=raw.subject,
                data=raw.data,
                headers=dict(raw.headers) if raw.headers else {},
                sequence=raw.metadata.sequence.stream if raw.metadata else None,
                _ack_func=raw.ack,
            )
        except nats.errors.TimeoutError:
            return None
        except Exception:
            logger.exception("Error fetching next message")
            return None

    async def ack(self, msg: Message) -> None:
        if msg._ack_func and callable(msg._ack_func):
            await msg._ack_func()

    async def unsubscribe(self) -> None:
        try:
            await self._sub.unsubscribe()
        except Exception:
            logger.debug("Error unsubscribing", exc_info=True)


class NatsJetStreamBus(MessageBus):
    """
    NATS JetStream message bus.

    Lightweight, single-binary server with persistent pub/sub, replay,
    consumer groups, and batching via pull consumers.
    """

    def __init__(self, url: str = "nats://localhost:4222"):
        self._url = url
        self._nc: Optional[NatsClient] = None
        self._js: Optional[JetStreamContext] = None

    async def connect(self) -> None:
        self._nc = await nats.connect(self._url)
        self._js = self._nc.jetstream()
        logger.info("Connected to NATS JetStream at %s", self._url)

    async def publish(
        self,
        subject: str,
        data: bytes,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        assert self._js is not None, "Call connect() first"
        await self._js.publish(subject, data, headers=headers)

    async def subscribe(
        self,
        subject: str,
        consumer_name: str,
        deliver_policy: str = "new",
        queue_group: Optional[str] = None,
    ) -> Subscription:
        assert self._js is not None, "Call connect() first"

        dp = _DELIVER_MAP.get(deliver_policy, DeliverPolicy.NEW)

        if queue_group:
            cfg = ConsumerConfig(
                durable_name=consumer_name,
                deliver_policy=dp,
                ack_policy=AckPolicy.EXPLICIT,
                filter_subject=subject,
            )
            sub = await self._js.pull_subscribe(
                subject,
                durable=consumer_name,
                config=cfg,
            )
            return _NatsSubscription(sub, is_pull=True)
        else:
            sub = await self._js.subscribe(
                subject,
                durable=consumer_name,
                deliver_policy=dp,
            )
            return _NatsSubscription(sub, is_pull=False)

    async def ensure_stream(
        self,
        name: str,
        subjects: list[str],
        max_age: int = 7 * 24 * 3600,
        storage: str = "file",
        replicas: int = 1,
    ) -> None:
        assert self._js is not None, "Call connect() first"

        cfg = StreamConfig(
            name=name,
            subjects=subjects,
            retention=RetentionPolicy.LIMITS,
            max_age=max_age,
            storage=_STORAGE_MAP.get(storage, StorageType.FILE),
            num_replicas=replicas,
        )

        try:
            await self._js.find_stream_name_by_subject(subjects[0])
            await self._js.update_stream(cfg)
            logger.info("Updated existing NATS stream '%s'", name)
        except nats.js.errors.NotFoundError:
            await self._js.add_stream(cfg)
            logger.info("Created NATS stream '%s' with subjects %s", name, subjects)

    async def close(self) -> None:
        if self._nc is not None:
            await self._nc.drain()
            self._nc = None
            self._js = None
            logger.info("Disconnected from NATS JetStream")
