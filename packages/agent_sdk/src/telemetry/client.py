from __future__ import annotations

"""Module ``agent_sdk/src/telemetry/client.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Telemetry client and publisher that emit TelemetryEvent streams to the ingest plane.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``client.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from google.protobuf.json_format import MessageToDict

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class TelemetryClient:
    """HTTP telemetry: heartbeats + event batches to the telemetry service."""

    def __init__(
        self,
        agent_id: str,
        endpoint: str | None = None,
        heartbeat_interval_secs: float | None = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        agent_type: Optional[str] = None,
    ):
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        from packages.platform_config import setting

        self.agent_id = agent_id
        self.agent_type = agent_type or agent_id
        self.endpoint = (endpoint or setting("TELEMETRY_URL")).rstrip("/")
        self.heartbeat_interval_secs = (
            heartbeat_interval_secs
            if heartbeat_interval_secs is not None
            else float(setting("AGENT_HEARTBEAT_INTERVAL_SECS"))
        )
        # Bind ``host`` from host for later use on this instance.
        self.host = host
        # Bind ``port`` from port for later use on this instance.
        self.port = port
        self._heartbeat_task: Optional[asyncio.Task] = None
        # Bind ``_busy`` from False for later use on this instance.
        self._busy = False
        self._client: Optional[httpx.AsyncClient] = None
        # Bind ``_sequence_id`` from 0 for later use on this instance.
        self._sequence_id = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """``_get_client`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._client is None:
            # Bind ``_client`` from httpx.AsyncClient(timeout=10.0) for later use on this instance.
            self._client = httpx.AsyncClient(timeout=10.0)
        # Hand ``self._client`` back to the caller.
        return self._client

    async def close(self) -> None:
        """``close`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        await self.stop_heartbeat()
        # Only when (self._client is not None).
        if self._client is not None:
            # Await ``self._client.aclose`` and continue once it completes.
            await self._client.aclose()
            # Bind ``_client`` from None for later use on this instance.
            self._client = None

    def set_busy(self, busy: bool) -> None:
        """``set_busy`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self._busy = busy

    def _next_sequence(self) -> int:
        """``set_busy`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self._sequence_id += 1
        # Hand ``self._sequence_id`` back to the caller.
        return self._sequence_id

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        stream_name: Optional[str] = None,
        task_id: Optional[str] = None,
        severity: str = "info",
        trace_id: Optional[str] = None,
    ) -> None:
        """Publish one EVENT to POST /telemetry/ingest (NATS → storage-writer)."""
        try:
            from packages.proto import telemetry_pb2

            # Local ``severity_map`` ← {.
            severity_map = {
                "info": telemetry_pb2.SEVERITY_INFO,
                "warn": telemetry_pb2.SEVERITY_WARN,
                "warning": telemetry_pb2.SEVERITY_WARN,
                "error": telemetry_pb2.SEVERITY_ERROR,
                "critical": telemetry_pb2.SEVERITY_CRITICAL,
            }
            # Local ``stream`` ← stream_name or event_type.
            stream = stream_name or event_type
            # Local ``message`` ← payload if isinstance(payload.get("message"), str) else json.dump….
            message = payload if isinstance(payload.get("message"), str) else json.dumps(
                payload, default=str
            )
            # Local ``event`` ← telemetry_pb2.TelemetryEvent(.
            event = telemetry_pb2.TelemetryEvent(
                # Local ``event_id`` ← str(uuid.uuid4()),.
                event_id=str(uuid.uuid4()),
                # Local ``event_time_ns`` ← time.time_ns(),.
                event_time_ns=time.time_ns(),
                # Local ``agent_id`` ← self.agent_id,.
                agent_id=self.agent_id,
                # Local ``agent_type`` ← self.agent_type,.
                agent_type=self.agent_type,
                # Local ``task_id`` ← task_id or "",.
                task_id=task_id or "",
                # Local ``sequence_id`` ← self._next_sequence(),.
                sequence_id=self._next_sequence(),
                # Local ``schema_version`` ← "v1",.
                schema_version="v1",
                # Local ``modality`` ← telemetry_pb2.EVENT,.
                modality=telemetry_pb2.EVENT,
                # Local ``stream_name`` ← stream,.
                stream_name=stream,
                # Local ``trace_id`` ← trace_id or "",.
                trace_id=trace_id or "",
                # Local ``source_id`` ← f"{self.agent_id}:telemetry_client",.
                source_id=f"{self.agent_id}:telemetry_client",
            )
            # Local ``ep`` ← telemetry_pb2.EventPayload(.
            ep = telemetry_pb2.EventPayload(
                # Local ``event_type`` ← event_type,.
                event_type=event_type,
                # Local ``severity`` ← severity_map.get(severity.lower(), telemetry_pb2.SEVERITY_INFO),.
                severity=severity_map.get(severity.lower(), telemetry_pb2.SEVERITY_INFO),
                # Local ``message`` ← message[:65536],.
                message=message[:65536],
            )
            # Loop: for key, value in payload.items().
            for key, value in payload.items():
                # Only when (key != "message").
                if key != "message":
                    ep.attributes[str(key)] = str(value)[:1024]
            # Call ``event.event.CopyFrom``.
            event.event.CopyFrom(ep)

            # Local ``client`` ← await self._get_client().
            client = await self._get_client()
            # Await ``client.post`` and continue once it completes.
            await client.post(
                f"{self.endpoint}/telemetry/ingest",
                # Local ``json`` ← {"events": [MessageToDict(event)]},.
                json={"events": [MessageToDict(event)]},
            )
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("Telemetry emit failed: %s", exc)

    async def _heartbeat_loop(self) -> None:
        """``_heartbeat_loop`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        while True:
            payload: dict[str, Any] = {
                "host": self.host or "localhost",
                "port": self.port or 0,
                "reachable": True,
                "busy": self._busy,
            }
            # Try the fallible work below.
            try:
                # Local ``client`` ← await self._get_client().
                client = await self._get_client()
                # Await ``client.post`` and continue once it completes.
                await client.post(f"{self.endpoint}/ingest/heartbeat", json=payload)
            # On except Exception as exc: recover or re-raise as appropriate.
            except Exception as exc:
                # Log at debug so operators can diagnose this path.
                logger.debug("Heartbeat failed: %s", exc)
            # Await ``asyncio.sleep`` and continue once it completes.
            await asyncio.sleep(self.heartbeat_interval_secs)

    def start_heartbeat(self) -> None:
        """``start_heartbeat`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            # Bind ``_heartbeat_task`` from asyncio.create_task(self._heartbeat_loop()) for later use on this instance.
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self) -> None:
        """``stop_heartbeat`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._heartbeat_task is not None:
            # Call ``self._heartbeat_task.cancel``.
            self._heartbeat_task.cancel()
            # Try the fallible work below.
            try:
                # Await ``self._heartbeat_task`` and continue once it completes.
                await self._heartbeat_task
            # On except asyncio.CancelledError: recover or re-raise as appropriate.
            except asyncio.CancelledError:
                pass
            # Bind ``_heartbeat_task`` from None for later use on this instance.
            self._heartbeat_task = None
