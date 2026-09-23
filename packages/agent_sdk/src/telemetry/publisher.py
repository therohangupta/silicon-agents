"""Module ``agent_sdk/src/telemetry/publisher.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Telemetry client and publisher that emit TelemetryEvent streams to the ingest plane.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

gRPC telemetry publisher for optional high-frequency agent streams.
"""


from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class TelemetryPublisher:
    """Publish telemetry events to the telemetry service via gRPC."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        grpc_target: str,
        blob_upload_url: Optional[str] = None,
    ):
        """``callable``"""
        self.agent_id = agent_id
        # Bind ``agent_type`` from agent_type for later use on this instance.
        self.agent_type = agent_type
        # Bind ``grpc_target`` from grpc_target for later use on this instance.
        self.grpc_target = grpc_target
        # Bind ``blob_upload_url`` from blob_upload_url for later use on this instance.
        self.blob_upload_url = blob_upload_url
        # Bind ``_channel`` from None for later use on this instance.
        self._channel = None
        # Bind ``_stub`` from None for later use on this instance.
        self._stub = None
        # Bind ``_sequence_id`` from 0 for later use on this instance.
        self._sequence_id = 0

    async def connect(self) -> None:
        """``connect``"""
        try:
            import grpc
            from packages.proto import telemetry_pb2_grpc

            # Bind ``_channel`` from grpc.aio.insecure_channel(self.grpc_target) for later use on this instance.
            self._channel = grpc.aio.insecure_channel(self.grpc_target)
            # Bind ``_stub`` from telemetry_pb2_grpc.TelemetryIngestionStub(self._channel) for later use on this instance.
            self._stub = telemetry_pb2_grpc.TelemetryIngestionStub(self._channel)
            # Log at info so operators can diagnose this path.
            logger.info("TelemetryPublisher connected to %s", self.grpc_target)
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at warning so operators can diagnose this path.
            logger.warning("TelemetryPublisher connect failed: %s", exc)
            raise

    async def close(self) -> None:
        """``close``"""
        if self._channel is not None:
            # Await ``self._channel.close`` and continue once it completes.
            await self._channel.close()
            # Bind ``_channel`` from None for later use on this instance.
            self._channel = None
            # Bind ``_stub`` from None for later use on this instance.
            self._stub = None

    def _base_event(
        self,
        *,
        task_id: str,
        stream_name: str,
        modality: Any,
        done: bool = False,
        tags: Optional[dict[str, str]] = None,
    ):
        """``callable``"""
        from packages.proto import telemetry_pb2

        self._sequence_id += 1
        # Hand ``telemetry_pb2.TelemetryEvent(`` back to the caller.
        return telemetry_pb2.TelemetryEvent(
            # Local ``event_id`` ← str(uuid.uuid4()),.
            event_id=str(uuid.uuid4()),
            # Local ``event_time_ns`` ← time.time_ns(),.
            event_time_ns=time.time_ns(),
            # Local ``agent_id`` ← self.agent_id,.
            agent_id=self.agent_id,
            # Local ``agent_type`` ← self.agent_type,.
            agent_type=self.agent_type,
            # Local ``task_id`` ← task_id,.
            task_id=task_id,
            # Local ``sequence_id`` ← self._sequence_id,.
            sequence_id=self._sequence_id,
            # Local ``schema_version`` ← "v1",.
            schema_version="v1",
            # Local ``modality`` ← modality,.
            modality=modality,
            # Local ``stream_name`` ← stream_name,.
            stream_name=stream_name,
            # Local ``tags`` ← {k: str(v) for k, v in (tags or {}).items()},.
            tags={k: str(v) for k, v in (tags or {}).items()},
            # Local ``done`` ← done,.
            done=done,
            # Local ``source_id`` ← f"{self.agent_id}:telemetry_adapter",.
            source_id=f"{self.agent_id}:telemetry_adapter",
        )

    async def _ingest(self, event: Any) -> None:
        """``_ingest``"""
        if self._stub is None:
            return
        # Try the fallible work below.
        try:
            from packages.proto import telemetry_pb2

            # Await ``self._stub.IngestBatch`` and continue once it completes.
            await self._stub.IngestBatch(telemetry_pb2.TelemetryBatch(events=[event]))
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("telemetry ingest failed: %s", exc)

    async def publish_state(
        self,
        task_id: str,
        stream_name: str,
        signals: list[Any],
        state_type: Any = None,
        done: bool = False,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """``callable``"""
        try:
            from packages.proto import telemetry_pb2

            # Local ``event`` ← self._base_event(.
            event = self._base_event(
                # Local ``task_id`` ← task_id,.
                task_id=task_id,
                # Local ``modality`` ← telemetry_pb2.STATE,.
                modality=telemetry_pb2.STATE,
                # Local ``stream_name`` ← stream_name,.
                stream_name=stream_name,
                # Local ``done`` ← done,.
                done=done,
                # Local ``tags`` ← tags,.
                tags=tags,
            )
            # Local ``state`` ← telemetry_pb2.StatePayload(state_type=state_type or 0).
            state = telemetry_pb2.StatePayload(state_type=state_type or 0)
            # Call ``state.signals.extend``.
            state.signals.extend(signals)
            # Call ``event.state.CopyFrom``.
            event.state.CopyFrom(state)
            # Await ``self._ingest`` and continue once it completes.
            await self._ingest(event)
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("publish_state failed: %s", exc)

    async def publish_action(
        self,
        task_id: str,
        stream_name: str,
        signals: list[Any],
        action_type: Any = None,
        attributes: Optional[dict[str, str]] = None,
        done: bool = False,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """``callable``"""
        try:
            from packages.proto import telemetry_pb2

            # Local ``event`` ← self._base_event(.
            event = self._base_event(
                # Local ``task_id`` ← task_id,.
                task_id=task_id,
                # Local ``stream_name`` ← stream_name,.
                stream_name=stream_name,
                # Local ``modality`` ← telemetry_pb2.ACTION,.
                modality=telemetry_pb2.ACTION,
                # Local ``done`` ← done,.
                done=done,
                # Local ``tags`` ← tags,.
                tags=tags,
            )
            # Local ``action`` ← telemetry_pb2.ActionPayload(action_type=action_type or 0).
            action = telemetry_pb2.ActionPayload(action_type=action_type or 0)
            # Call ``action.signals.extend``.
            action.signals.extend(signals)
            # Call ``action.attributes.update``.
            action.attributes.update({k: str(v) for k, v in (attributes or {}).items()})
            # Call ``event.action.CopyFrom``.
            event.action.CopyFrom(action)
            # Await ``self._ingest`` and continue once it completes.
            await self._ingest(event)
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("publish_action failed: %s", exc)

    async def publish_event(
        self,
        task_id: str,
        event_type: str,
        message: str,
        severity: Any = None,
        attributes: Optional[dict[str, str]] = None,
        tags: Optional[dict[str, str]] = None,
        stream_name: Optional[str] = None,
    ) -> None:
        """``callable``"""
        try:
            from packages.proto import telemetry_pb2

            # Local ``event`` ← self._base_event(.
            event = self._base_event(
                # Local ``task_id`` ← task_id,.
                task_id=task_id,
                # Local ``stream_name`` ← stream_name or event_type,.
                stream_name=stream_name or event_type,
                # Local ``modality`` ← telemetry_pb2.EVENT,.
                modality=telemetry_pb2.EVENT,
                # Local ``tags`` ← tags,.
                tags=tags,
            )
            # Local ``payload`` ← telemetry_pb2.EventPayload(.
            payload = telemetry_pb2.EventPayload(
                # Local ``event_type`` ← event_type,.
                event_type=event_type,
                # Local ``severity`` ← severity if severity is not None else telemetry_pb2.SEVERITY_INFO….
                severity=severity if severity is not None else telemetry_pb2.SEVERITY_INFO,
                # Local ``message`` ← message,.
                message=message,
            )
            # Call ``payload.attributes.update``.
            payload.attributes.update({k: str(v) for k, v in (attributes or {}).items()})
            # Call ``event.event.CopyFrom``.
            event.event.CopyFrom(payload)
            # Await ``self._ingest`` and continue once it completes.
            await self._ingest(event)
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("publish_event failed: %s", exc)

    async def upload_blob(
        self,
        agent_id: str,
        stream_name: str,
        filename: str,
        data: bytes,
        mime_type: str,
        task_id: str,
    ) -> str:
        """``callable``"""
        if self.blob_upload_url is None:
            # Hand ``f"memory://{agent_id}/{task_id}/{stream_name}/{filename}"`` back to the caller.
            return f"memory://{agent_id}/{task_id}/{stream_name}/{filename}"
        # Try the fallible work below.
        try:
            import httpx

            # Hold ``httpx.AsyncClient(timeout=30.0)`` for the duration of the indented block.
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Local ``response`` ← await client.post(.
                response = await client.post(
                    self.blob_upload_url,
                    # Local ``files`` ← {"file": (filename, data, mime_type)},.
                    files={"file": (filename, data, mime_type)},
                    # Local ``data`` ← {.
                    data={
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "stream_name": stream_name,
                    },
                )
                # Call ``response.raise_for_status``.
                response.raise_for_status()
                # Local ``payload`` ← response.json().
                payload = response.json()
                # Hand ``payload.get("uri") or payload.get("url") or payload.get("path") or fil…`` back to the caller.
                return payload.get("uri") or payload.get("url") or payload.get("path") or filename
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at debug so operators can diagnose this path.
            logger.debug("upload_blob failed: %s", exc)
            # Hand ``f"memory://{agent_id}/{task_id}/{stream_name}/{filename}"`` back to the caller.
            return f"memory://{agent_id}/{task_id}/{stream_name}/{filename}"
