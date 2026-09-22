"""MessageBus abstraction for decoupled pub/sub across the fleet.

Default implementation: NATS JetStream (``NatsJetStreamBus`` in
``nats_jetstream.py``). The abstract interface can be swapped for Kafka,
Redis Streams, or another durable log without changing telemetry publishers
or memory-plane event writers that depend only on ``MessageBus``.

This package is the message-bus plane of the control architecture: agents
and services publish bytes to subjects; consumers pull with durable names,
optional queue groups, and deliver policies (``all`` / ``new`` / ``last``).
"""

# ABC marks the swappable bus and subscription contracts.
from abc import ABC, abstractmethod
# dataclass builds the Message value object.
from dataclasses import dataclass, field
# Optional for sequence / ack / queue_group fields.
from typing import Optional


@dataclass
class Message:
    """A single message received from the bus.

    ``_ack_func`` holds the transport-specific ack coroutine (e.g. NATS
    ``msg.ack``) and is intentionally excluded from repr to avoid leaking
    callables in logs.
    """

    # NATS-style subject the message arrived on.
    subject: str
    # Raw payload bytes (callers decode JSON/protobuf themselves).
    data: bytes
    # Optional string headers copied from the transport.
    headers: dict[str, str] = field(default_factory=dict)
    # Stream sequence number when the transport provides one.
    sequence: Optional[int] = None
    # Bound ack callable from the underlying client; not for public use.
    _ack_func: Optional[object] = field(default=None, repr=False)


class Subscription(ABC):
    """Handle returned by MessageBus.subscribe for consuming messages."""

    @abstractmethod
    async def next_msg(self, timeout: float = 5.0) -> Optional[Message]:
        """Block up to *timeout* seconds for the next message. Returns None on timeout."""
        ...

    @abstractmethod
    async def ack(self, msg: Message) -> None:
        """Acknowledge successful processing of *msg*."""
        ...

    @abstractmethod
    async def unsubscribe(self) -> None:
        """Detach this subscription from the bus."""
        ...


class MessageBus(ABC):
    """Swappable message-bus interface.

    Implementations must support:

    * persistent publish/subscribe
    # Call ``* replay``.
    * replay (via ``deliver_policy``)
    # Call ``* consumer groups``.
    * consumer groups (via ``queue_group``)
    * batching-friendly pull semantics
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the bus."""
        ...

    @abstractmethod
    async def publish(
        self,
        subject: str,
        data: bytes,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish a message to *subject*."""
        ...

    @abstractmethod
    async def subscribe(
        self,
        subject: str,
        consumer_name: str,
        deliver_policy: str = "new",
        queue_group: Optional[str] = None,
    ) -> Subscription:
        """Subscribe to *subject*.

        Args:
            subject: NATS-style subject (supports wildcards like ``telemetry.>``).
            consumer_name: Durable consumer name.
            deliver_policy: ``"all"`` replay from start, ``"new"`` only new,
                            ``"last"`` from last acked.
            queue_group: If set, messages are load-balanced across the group.
        """
        ...

    @abstractmethod
    async def ensure_stream(
        self,
        name: str,
        subjects: list[str],
        max_age: int = 7 * 24 * 3600,
        storage: str = "file",
        replicas: int = 1,
    ) -> None:
        """Ensure a durable stream exists with the given configuration.

        Idempotent — updates if the stream already exists.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Gracefully disconnect from the bus."""
        ...
