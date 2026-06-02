"""
MessageBus abstraction for decoupled pub/sub.

Default implementation: NATS JetStream (NatsJetStreamBus).
The interface can be swapped for Kafka, Redis Streams, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Message:
    """A single message received from the bus."""

    subject: str
    data: bytes
    headers: dict[str, str] = field(default_factory=dict)
    sequence: Optional[int] = None
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
    """
    Swappable message-bus interface.

    Implementations must support:
      - persistent publish/subscribe
      - replay (via deliver_policy)
      - consumer groups (via queue_group)
      - batching-friendly pull semantics
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
        """
        Subscribe to *subject*.

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
        """
        Ensure a durable stream exists with the given configuration.
        Idempotent — updates if the stream already exists.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Gracefully disconnect from the bus."""
        ...
