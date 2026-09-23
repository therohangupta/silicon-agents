"""
Durable task delivery via NATS JetStream for the Fleet Executor.

When ``DURABLE_TASK_DISPATCH=true``, the Executor prefers
``TaskDeliveryBus.dispatch_and_deliver`` over a direct ``AgentClient`` HTTP
call. The bus:

  1. Ensures an ``AGENT_TASKS`` stream covering ``tasks.dispatch.>``.
  2. Publishes a dispatch payload (agent host/port + ``AgentTaskRequest``).
  3. Subscribes as a work-queue consumer, waits for the matching message,
     executes the HTTP task against the agent, and **defers ack** until the
     Executor finalizes success/failure (``ack``), enabling at-least-once
     redelivery if the process crashes mid-flight.

``publish_dispatch`` alone is also used during reconciliation to re-enqueue
rows still marked ``dispatch_state=dispatched`` without a terminal result.
"""

# Postpone annotation evaluation.
from __future__ import annotations

# json encodes/decodes JetStream message payloads.
import json
# logging for connect / skip / timeout diagnostics.
import logging
# os.environ provides NATS_URL defaulting.
import os
# dataclass for DeliveredTaskResult container.
from dataclasses import dataclass
# Optional typing for bus/subscription fields.
from typing import Optional

# HTTP client used when delivering a pulled dispatch message to an agent.
from packages.agent_sdk.src.client.agent_client import AgentClient
# Request/result models carried inside the JetStream payload.
from packages.agent_sdk.src.contracts import AgentTaskRequest, AgentTaskResult
# Message bus abstractions for subscribe/ack.
from packages.message_bus import Message, Subscription
# NATS JetStream implementation of the message bus.
from packages.message_bus.nats_jetstream import NatsJetStreamBus

# Module logger.
logger = logging.getLogger(__name__)

# JetStream stream name for durable agent task dispatches.
TASK_STREAM = "AGENT_TASKS"
# Subject prefix; per-agent subjects are ``tasks.dispatch.<safe_agent_id>``.
DISPATCH_SUBJECT_PREFIX = "tasks.dispatch"


def dispatch_subject(agent_id: str) -> str:
    """
    Build a JetStream subject for an agent's dispatch work queue.

    Sanitizes ``:`` and ``/`` in agent ids so subjects remain valid NATS tokens.

    Args:
        agent_id: Raw agent instance identifier.

    Returns:
        Subject string like ``tasks.dispatch.nav-1``.
    """
    # Replace characters that are illegal or awkward in NATS subject tokens.
    safe = agent_id.replace(":", "_").replace("/", "_")
    # Prefix with the shared dispatch namespace.
    return f"{DISPATCH_SUBJECT_PREFIX}.{safe}"


@dataclass
class DeliveredTaskResult:
    """
    Holds an executed task result plus the JetStream message to ack later.

    The Executor keeps this in ``_pending_delivery_ack`` until the task reaches
    a terminal outcome, then calls ``TaskDeliveryBus.ack``.
    """
    # Outcome from the agent HTTP execute_task call (or idempotent skip).
    result: AgentTaskResult
    # Subscription used to receive the message (needed for ack/unsubscribe).
    subscription: Optional[Subscription] = None
    # The raw JetStream message to acknowledge after terminal handling.
    message: Optional[Message] = None


class TaskDeliveryBus:
    """
    Durable task dispatch via NATS JetStream work queue.

    Lifecycle: ``connect()`` → ``dispatch_and_deliver`` / ``publish_dispatch``
    → ``ack`` → ``close()``. Safe to construct even when NATS is down; the
    Executor disables durable mode if ``connect`` fails.
    """

    def __init__(self, nats_url: Optional[str] = None):
        """
        Store the NATS URL and initialize connection state flags.

        Args:
            nats_url: Optional override; otherwise reads the configured
                ``NATS_URL``.
        """
        from packages.config import NATS_URL

        # Resolve URL from the explicit argument or the platform configuration.
        self.nats_url = nats_url or os.environ.get("NATS_URL") or NATS_URL
        # Underlying JetStream bus; created in connect().
        self._bus: Optional[NatsJetStreamBus] = None
        # True after a successful connect + stream ensure.
        self._connected = False

    async def connect(self) -> None:
        """
        Connect to NATS and ensure the ``AGENT_TASKS`` stream exists.

        Idempotent: returns immediately if already connected.
        """
        # Skip work when already connected in this process.
        if self._connected:
            return
        # Construct the JetStream bus wrapper.
        self._bus = NatsJetStreamBus(self.nats_url)
        # Open the NATS connection.
        await self._bus.connect()
        # Ensure the durable stream covers all dispatch subjects.
        await self._bus.ensure_stream(
            TASK_STREAM,
            subjects=[f"{DISPATCH_SUBJECT_PREFIX}.>"],
        )
        # Mark ready for publish/subscribe.
        self._connected = True
        logger.info("Task delivery bus connected to %s", self.nats_url)

    async def publish_dispatch(
        self,
        agent_id: str,
        host: str,
        port: int,
        request: AgentTaskRequest,
        plan_id: int,
        task_id: int,
    ) -> None:
        """
        Publish a dispatch payload for later pull/execution.

        Args:
            agent_id: Target agent id (also shapes the subject).
            host: Agent task server host to use when delivering.
            port: Agent task server port.
            request: Full AgentTaskRequest to execute.
            plan_id: Owning plan id (included in payload for consumers).
            task_id: Task id (also set as a header for filtering).
        """
        # Require connect() before publish.
        assert self._bus is not None
        # Build the JSON-serializable payload consumed by _deliver_payload.
        payload = {
            "agent_id": agent_id,
            "host": host,
            "port": port,
            "plan_id": plan_id,
            "task_id": task_id,
            "request": request.model_dump(mode="json"),
        }
        # Publish onto the agent-specific subject within AGENT_TASKS.
        await self._bus.publish(
            dispatch_subject(agent_id),
            json.dumps(payload).encode(),
            headers={"task_id": str(task_id), "agent_id": agent_id},
            stream=TASK_STREAM,
        )

    async def _deliver_payload(
        self,
        payload: dict,
        completed_task_ids: set[str],
    ) -> AgentTaskResult:
        """
        Execute the agent HTTP call for a pulled dispatch payload.

        Skips execution (idempotent success) when the task id is already in
        ``completed_task_ids``.

        Args:
            payload: Dec with host/port/request/task_id fields.
            completed_task_ids: Set of task ids already finished.

        Returns:
            ``AgentTaskResult`` from the agent or an idempotent skip result.
        """
        # Normalize task id to string for set membership checks.
        task_id = str(payload["task_id"])
        if task_id in completed_task_ids:
            logger.info("Skipping duplicate dispatch for task %s", task_id)
            return AgentTaskResult(success=True, message="idempotent skip: already completed")

        # Rebuild the request model from the serialized payload.
        request = AgentTaskRequest(**payload["request"])
        # Open a short-lived HTTP client to the agent task server.
        client = AgentClient(payload["host"], int(payload["port"]))
        try:
            # Perform the actual agent task execution.
            return await client.execute_task(request)
        finally:
            # Always close the client to release connections.
            await client.close()

    async def _wait_for_task_message(
        self,
        sub: Subscription,
        expected_task_id: int,
        receive_timeout_secs: float,
    ) -> Message:
        """
        Pull messages until one matches ``expected_task_id`` or time expires.

        Non-matching messages are acked and skipped so they do not block the
        consumer. Invalid JSON is acked and skipped similarly.

        Args:
            sub: Active JetStream subscription.
            expected_task_id: Task id we published and expect to receive.
            receive_timeout_secs: Total budget across chunked next_msg waits.

        Returns:
            The matching ``Message``.

        Raises:
            TimeoutError: If no matching message arrives in time.
        """
        # Remaining time budget for receiving the matching message.
        deadline = receive_timeout_secs
        while deadline > 0:
            # Wait in ≤5s chunks so we can decrement the deadline smoothly.
            chunk = min(5.0, deadline)
            msg = await sub.next_msg(timeout=chunk)
            deadline -= chunk
            # None means the chunk timed out without a message.
            if msg is None:
                continue
            try:
                # Decode payload to inspect task_id.
                payload = json.loads(msg.data)
            except json.JSONDecodeError:
                # Drop poison messages so they are not redelivered forever.
                await sub.ack(msg)
                continue
            # Accept only the task we are currently dispatching.
            if int(payload.get("task_id", -1)) == expected_task_id:
                return msg
            # Unrelated message: ack and keep waiting.
            await sub.ack(msg)
        # Exhausted the budget without a match.
        raise TimeoutError(f"No durable task message received for task {expected_task_id}")

    async def dispatch_and_deliver(
        self,
        agent_id: str,
        host: str,
        port: int,
        request: AgentTaskRequest,
        plan_id: int,
        task_id: int,
        completed_task_ids: set[str],
        receive_timeout_secs: float,
    ) -> DeliveredTaskResult:
        """
        Subscribe, publish, pull matching message, execute HTTP, defer ack.

        Args:
            agent_id: Target agent for subject + consumer naming.
            host: Agent task server host.
            port: Agent task server port.
            request: Task request to embed in the published payload.
            plan_id: Plan id for payload metadata.
            task_id: Task id expected on the pulled message.
            completed_task_ids: For idempotent skip inside delivery.
            receive_timeout_secs: Budget for waiting on the matching message.

        Returns:
            ``DeliveredTaskResult`` with result + subscription/message for later ack.

        Raises:
            Exception: Propagates after unsubscribing on failure paths.
        """
        # Require an established bus connection.
        assert self._bus is not None
        # Per-agent subject for the work queue.
        subject = dispatch_subject(agent_id)
        # Consumer name sanitized for NATS durable consumer constraints.
        consumer = f"task_worker_{agent_id.replace('-', '_').replace(':', '_')}"
        # Subscribe with new deliver policy and a shared queue group.
        sub = await self._bus.subscribe(
            subject,
            consumer_name=consumer,
            deliver_policy="new",
            queue_group="fleet_executors",
            stream=TASK_STREAM,
        )
        try:
            # Publish after subscribe so we do not miss the message.
            await self.publish_dispatch(agent_id, host, port, request, plan_id, task_id)
            # Wait specifically for our task_id.
            msg = await self._wait_for_task_message(sub, task_id, receive_timeout_secs)
            # Decode and execute against the agent.
            payload = json.loads(msg.data)
            result = await self._deliver_payload(payload, completed_task_ids)
            # Return without acking — Executor acks on terminal outcome.
            return DeliveredTaskResult(result=result, subscription=sub, message=msg)
        except Exception:
            # On failure, drop the subscription so we do not leak consumers.
            await sub.unsubscribe()
            raise

    async def ack(self, delivered: Optional[DeliveredTaskResult]) -> None:
        """
        Acknowledge and unsubscribe a previously delivered message.

        Args:
            delivered: Optional result from ``dispatch_and_deliver``; no-op if
                None or missing subscription/message.
        """
        if delivered and delivered.subscription and delivered.message:
            # Ack so JetStream will not redeliver this message.
            await delivered.subscription.ack(delivered.message)
            # Unsubscribe to release the consumer subscription.
            await delivered.subscription.unsubscribe()

    async def close(self) -> None:
        """
        Close the underlying NATS connection and clear the connected flag.
        """
        if self._bus:
            # Close JetStream / NATS resources.
            await self._bus.close()
            # Allow a future connect() to re-establish.
            self._connected = False
