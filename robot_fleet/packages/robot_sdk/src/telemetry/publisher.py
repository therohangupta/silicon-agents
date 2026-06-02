"""
TelemetryPublisher — gRPC streaming client for publishing telemetry events.

Each robot creates one publisher instance. During task execution, the robot's
telemetry adapter calls publish_state/publish_action/publish_vision/publish_event
which build canonical TelemetryEvent proto messages and stream them to the
ingestion service.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Optional
from urllib.parse import urlparse

import grpc
import httpx
import websockets

from packages.proto import telemetry_pb2, telemetry_pb2_grpc

logger = logging.getLogger(__name__)


def _ulid() -> str:
    """Simple unique ID. Uses uuid4 as a fallback if ulid-py is not installed."""
    try:
        import ulid as _ulid_mod
        return str(_ulid_mod.new())
    except ImportError:
        return str(uuid.uuid4())


class TelemetryPublisher:
    """
    Publishes canonical TelemetryEvent messages to the ingestion service.

    Uses gRPC bidirectional streaming for state/action/vision/event data,
    and HTTP multipart POST for blob uploads.
    """

    def __init__(
        self,
        robot_id: str,
        robot_type: str,
        grpc_target: str = "localhost:9001",
        blob_upload_url: str = "http://localhost:9000/telemetry/blob",
        schema_version: str = "v1",
        source_id: Optional[str] = None,
    ):
        self.robot_id = robot_id
        self.robot_type = robot_type
        self._grpc_target = grpc_target
        self._blob_upload_url = blob_upload_url
        self._schema_version = schema_version
        self._source_id = source_id or robot_id

        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[telemetry_pb2_grpc.TelemetryIngestionStub] = None
        self._stream = None
        self._send_queue: asyncio.Queue = asyncio.Queue()
        self._stream_task: Optional[asyncio.Task] = None

        # sequence_id: per (robot_id, task_id, modality, stream_name)
        self._sequence_counters: dict[str, int] = {}
        # step_index: per (robot_id, task_id) — shared across all streams
        self._step_counters: dict[str, int] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._live_video_ws: Optional[websockets.WebSocketClientProtocol] = None
        self._live_video_ws_base: Optional[str] = None
        self._live_video_camera: Optional[str] = None
        self._live_video_codec: Optional[str] = None

    async def connect(self) -> None:
        """Open the gRPC channel and start the bidirectional stream."""
        self._channel = grpc.aio.insecure_channel(
            self._grpc_target,
            options=[
                # round_robin tries all resolved addresses (IPv4 + IPv6)
                # so Docker's host.docker.internal works even when IPv6 is unreachable
                ("grpc.lb_policy_name", "round_robin"),
                ("grpc.enable_retries", 1),
            ],
        )
        self._stub = telemetry_pb2_grpc.TelemetryIngestionStub(self._channel)
        self._stream_task = asyncio.create_task(self._run_stream())
        self._http_client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            "TelemetryPublisher connected: robot=%s grpc=%s",
            self.robot_id, self._grpc_target,
        )

    async def _run_stream(self) -> None:
        """Background task that drives the bidi stream with auto-reconnect."""
        retry_delay = 1.0
        max_delay = 30.0

        while True:
            try:
                logger.info("Opening gRPC bidi stream to %s", self._grpc_target)
                self._stream = self._stub.StreamTelemetry(self._event_generator())
                retry_delay = 1.0
                async for ack in self._stream:
                    logger.debug("gRPC ack: ok=%s accepted=%s", ack.ok, ack.accepted)
                    if not ack.ok and ack.error:
                        logger.warning("Ingest ack error: %s", ack.error)
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    break
                logger.warning(
                    "gRPC stream failed (%s) — retrying in %.0fs",
                    e.code(), retry_delay,
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            except asyncio.CancelledError:
                break

    async def _event_generator(self):
        """Yields events from the send queue to the gRPC stream."""
        while True:
            event = await self._send_queue.get()
            if event is None:
                return
            yield event

    def _next_seq(self, stream_key: str) -> int:
        seq = self._sequence_counters.get(stream_key, 0) + 1
        self._sequence_counters[stream_key] = seq
        return seq

    def _next_step(self, task_key: str) -> int:
        step = self._step_counters.get(task_key, 0) + 1
        self._step_counters[task_key] = step
        return step

    def _make_envelope(
        self,
        task_id: str,
        stream_name: str,
        modality: int,
        *,
        completeness: int = telemetry_pb2.FULL,
        done: bool = False,
        sync_group: str = "",
        tags: Optional[dict[str, str]] = None,
    ) -> telemetry_pb2.TelemetryEvent:
        seq_key = f"{self.robot_id}:{task_id}:{modality}:{stream_name}"
        task_key = f"{self.robot_id}:{task_id}"
        event = telemetry_pb2.TelemetryEvent(
            event_id=_ulid(),
            event_time_ns=time.time_ns(),
            robot_id=self.robot_id,
            robot_type=self.robot_type,
            task_id=task_id,
            sequence_id=self._next_seq(seq_key),
            schema_version=self._schema_version,
            modality=modality,
            stream_name=stream_name,
            step_index=self._next_step(task_key),
            source_id=self._source_id,
            completeness=completeness,
            done=done,
            sync_group=sync_group,
        )
        if tags:
            event.tags.update(tags)
        return event

    async def publish_state(
        self,
        task_id: str,
        stream_name: str,
        signals: list[telemetry_pb2.VectorSignal],
        state_type: int = telemetry_pb2.StatePayload.JOINT,
        attributes: Optional[dict[str, str]] = None,
        completeness: int = telemetry_pb2.FULL,
        done: bool = False,
        sync_group: str = "",
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish a STATE telemetry event."""
        event = self._make_envelope(
            task_id, stream_name, telemetry_pb2.STATE,
            completeness=completeness, done=done, sync_group=sync_group, tags=tags,
        )
        event.state.CopyFrom(telemetry_pb2.StatePayload(
            state_type=state_type,
            signals=signals,
            attributes=attributes or {},
        ))
        await self._send_queue.put(event)

    async def publish_action(
        self,
        task_id: str,
        stream_name: str,
        signals: list[telemetry_pb2.VectorSignal],
        action_type: int = telemetry_pb2.ActionPayload.JOINT_POSITION,
        attributes: Optional[dict[str, str]] = None,
        completeness: int = telemetry_pb2.FULL,
        done: bool = False,
        sync_group: str = "",
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish an ACTION telemetry event."""
        event = self._make_envelope(
            task_id, stream_name, telemetry_pb2.ACTION,
            completeness=completeness, done=done, sync_group=sync_group, tags=tags,
        )
        event.action.CopyFrom(telemetry_pb2.ActionPayload(
            action_type=action_type,
            signals=signals,
            attributes=attributes or {},
        ))
        await self._send_queue.put(event)

    async def publish_vision(
        self,
        task_id: str,
        stream_name: str,
        blob_ref: telemetry_pb2.BlobRef,
        camera_name: str = "",
        attributes: Optional[dict[str, str]] = None,
        completeness: int = telemetry_pb2.FULL,
        done: bool = False,
        sync_group: str = "",
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish a VISION telemetry event with a blob reference."""
        event = self._make_envelope(
            task_id, stream_name, telemetry_pb2.VISION,
            completeness=completeness, done=done, sync_group=sync_group, tags=tags,
        )
        event.vision.CopyFrom(telemetry_pb2.VisionPayload(
            blobs=[blob_ref],
            camera_name=camera_name,
            attributes=attributes or {},
        ))
        await self._send_queue.put(event)

    async def publish_event(
        self,
        task_id: str,
        event_type: str,
        severity: int = telemetry_pb2.SEVERITY_INFO,
        message: str = "",
        stream_name: str = "events",
        attributes: Optional[dict[str, str]] = None,
        done: bool = False,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish an EVENT telemetry event."""
        event = self._make_envelope(
            task_id, stream_name, telemetry_pb2.EVENT,
            completeness=telemetry_pb2.FULL, done=done, tags=tags,
        )
        event.event.CopyFrom(telemetry_pb2.EventPayload(
            event_type=event_type,
            severity=severity,
            message=message,
            attributes=attributes or {},
        ))
        await self._send_queue.put(event)

    async def push_live_frame(
        self,
        camera_name: str,
        data: bytes,
        mime_type: str = "image/jpeg",
    ) -> None:
        """
        Deprecated. Use push_live_h264_chunk().

        Kept as a soft fallback for compatibility while callers migrate.
        """
        del mime_type
        await self.push_live_h264_chunk(camera_name=camera_name, encoded_chunk=data, keyframe=True)

    async def _ensure_live_video_ws(self, camera_name: str, codec: str) -> None:
        if self._live_video_ws_base is None:
            # Derive gateway URL from blob upload URL host.
            # Example: http://host:9000/telemetry/blob -> ws://host:8000
            parsed = urlparse(self._blob_upload_url)
            host = parsed.hostname or "localhost"
            self._live_video_ws_base = f"ws://{host}:8000"

        if (
            self._live_video_ws is not None
            and self._live_video_camera == camera_name
            and self._live_video_codec == codec
        ):
            return

        if self._live_video_ws is not None:
            try:
                await self._live_video_ws.close()
            except Exception:
                pass
            self._live_video_ws = None

        ws_url = (
            f"{self._live_video_ws_base}/ws/video/publish/"
            f"{self.robot_id}/{camera_name}"
        )
        self._live_video_ws = await websockets.connect(ws_url, max_queue=1, ping_interval=20)
        self._live_video_camera = camera_name
        self._live_video_codec = codec
        await self._live_video_ws.send(json.dumps({"type": "config", "codec": codec}))

    async def push_live_video_chunk(
        self,
        camera_name: str,
        encoded_chunk: bytes,
        *,
        codec: str = "h264",
        keyframe: bool = False,
    ) -> None:
        """
        Push a pre-encoded video chunk to gateway fanout.

        Binary payload format:
          [1-byte flags][encoded bytes]
        flags bit0 = keyframe
        """
        try:
            await self._ensure_live_video_ws(camera_name, codec)
            if self._live_video_ws is None:
                return
            flags = 0x01 if keyframe else 0x00
            await self._live_video_ws.send(bytes([flags]) + encoded_chunk)
        except Exception:
            logger.debug("Live video chunk push failed", exc_info=True)
            if self._live_video_ws is not None:
                try:
                    await self._live_video_ws.close()
                except Exception:
                    pass
            self._live_video_ws = None
            self._live_video_camera = None
            self._live_video_codec = None

    async def push_live_h264_chunk(
        self,
        camera_name: str,
        encoded_chunk: bytes,
        *,
        keyframe: bool = False,
    ) -> None:
        """
        Push a pre-encoded H264 chunk to gateway fanout.

        Convenience wrapper for H264 streams.
        """
        await self.push_live_video_chunk(
            camera_name=camera_name,
            encoded_chunk=encoded_chunk,
            codec="h264",
            keyframe=keyframe,
        )

    async def upload_blob(
        self,
        robot_id: str,
        stream_name: str,
        filename: str,
        data: bytes,
        mime_type: str = "image/jpeg",
        task_id: str = "",
    ) -> str:
        """
        Upload a blob (image frame, etc.) to the ingestion service.
        Returns the URI for use in BlobRef.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        form = {"robot_id": robot_id, "stream_name": stream_name}
        if task_id:
            form["task_id"] = task_id

        resp = await self._http_client.post(
            self._blob_upload_url,
            data=form,
            files={"file": (filename, data, mime_type)},
        )
        resp.raise_for_status()
        return resp.json()["uri"]

    async def close(self) -> None:
        """Shut down the gRPC stream and channel."""
        await self._send_queue.put(None)
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        if self._channel:
            await self._channel.close()
        if self._http_client:
            await self._http_client.aclose()
        if self._live_video_ws:
            await self._live_video_ws.close()
        logger.info("TelemetryPublisher closed for robot=%s", self.robot_id)
