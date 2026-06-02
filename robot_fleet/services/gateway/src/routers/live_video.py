"""
Gateway live video fanout (H264-over-WebSocket).

Publisher path (robot or telemetry producer):
  WS /ws/video/publish/{robot_id}/{camera_name}

Viewer path (frontend):
  WS /ws/video/subscribe/{robot_id}/{camera_name}

Protocol:
- Publisher sends a JSON config first:
    {"type":"config","codec":"h264","width":1280,"height":720}
- Publisher then sends binary chunks.
  The first byte is flags where bit 0 indicates keyframe.
  Remaining bytes are encoded video payload (typically Annex-B H264 NAL units).
- Viewers receive the same JSON config and binary chunks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Live Video"])


@dataclass
class StreamState:
    publisher: WebSocket | None = None
    viewers: set[WebSocket] = field(default_factory=set)
    config: dict[str, Any] = field(default_factory=lambda: {"type": "config", "codec": "h264"})


_streams: dict[str, StreamState] = {}


def _stream_key(robot_id: str, camera_name: str) -> str:
    return f"{robot_id}:{camera_name}"


async def _broadcast_json(state: StreamState, msg: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for ws in state.viewers:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.viewers.discard(ws)


async def _broadcast_bytes(state: StreamState, payload: bytes) -> None:
    dead: list[WebSocket] = []
    for ws in state.viewers:
        try:
            await ws.send_bytes(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.viewers.discard(ws)


@router.websocket("/ws/video/publish/{robot_id}/{camera_name}")
async def publish_video(websocket: WebSocket, robot_id: str, camera_name: str) -> None:
    await websocket.accept()
    key = _stream_key(robot_id, camera_name)
    state = _streams.setdefault(key, StreamState())

    # Single upstream per stream key. Replace stale publisher if needed.
    if state.publisher is not None:
        try:
            await state.publisher.close(code=1012, reason="Publisher replaced")
        except Exception:
            pass
    state.publisher = websocket

    # Immediately send current config to existing viewers.
    await _broadcast_json(state, state.config)
    logger.info("Live video publisher connected: %s", key)

    try:
        while True:
            msg = await websocket.receive()
            if text := msg.get("text"):
                # Config updates (codec, width, height, fps...)
                try:
                    import json

                    parsed = json.loads(text)
                except Exception:
                    continue
                if isinstance(parsed, dict) and parsed.get("type") == "config":
                    state.config = parsed
                    await _broadcast_json(state, parsed)
                continue

            chunk = msg.get("bytes")
            if chunk:
                # Stateless low-latency relay. No buffering to keep latency low.
                await _broadcast_bytes(state, chunk)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Live video publisher failed: %s", key)
    finally:
        if state.publisher is websocket:
            state.publisher = None
        logger.info("Live video publisher disconnected: %s", key)


@router.websocket("/ws/video/subscribe/{robot_id}/{camera_name}")
async def subscribe_video(websocket: WebSocket, robot_id: str, camera_name: str) -> None:
    await websocket.accept()
    key = _stream_key(robot_id, camera_name)
    state = _streams.setdefault(key, StreamState())
    state.viewers.add(websocket)

    # Push latest config right away so client can initialize decoder.
    try:
        await websocket.send_json(state.config)
    except Exception:
        state.viewers.discard(websocket)
        return

    try:
        # Keepalive/read loop. We ignore inbound viewer messages.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Live video viewer failed: %s", key)
    finally:
        state.viewers.discard(websocket)
