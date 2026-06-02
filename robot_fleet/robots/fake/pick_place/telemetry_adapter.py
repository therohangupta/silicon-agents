"""
Pick-place robot telemetry adapter.

Streaming modes:
  stream_idle — always-on low-rate state + live video push.
  stream_task — full-rate state/action + live video push. persist flag adds blob storage.

Live video: frames are pushed via HTTP to the telemetry server's media plane
(in-memory only). State/action go through gRPC → NATS → gateway → WebSocket.
When recording (persist=True), frames are ALSO uploaded to the blob store and
a vision event with the URI goes through the telemetry bus for Parquet storage.
"""

import asyncio
import csv
import logging
from pathlib import Path
from typing import Optional

from packages.proto import telemetry_pb2
from packages.robot_sdk.src.telemetry.publisher import TelemetryPublisher
from packages.robot_sdk.src.telemetry.video_reader import VideoFrameReader

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
ACTIONS_CSV = DATA_DIR / "actions.csv"
VIDEO_FILE = DATA_DIR / "task_video.MOV"

JOINT_NAMES = ["joint_1", "joint_2", "joint_3", "joint_4"]
_INITIAL_POS = [0.0, -0.78, 1.57, 0.0]
_LIVE_TASK_ID = "__live__"


def _parse_actions_csv() -> list[dict]:
    rows = []
    with open(ACTIONS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "step": int(row["step"]),
                "cmd_type": row["cmd_type"],
                "targets": [float(row["j1_target"]), float(row["j2_target"]),
                            float(row["j3_target"]), float(row["j4_target"])],
                "grip_force": float(row["grip_force_n"]),
            })
    return rows


# ── idle stream ──────────────────────────────────────────────────────────────

async def stream_idle(publisher: TelemetryPublisher) -> None:
    """Low-rate continuous stream for live UI. Runs until cancelled."""
    video: Optional[VideoFrameReader] = None
    if VIDEO_FILE.exists():
        try:
            video = VideoFrameReader(VIDEO_FILE)
        except Exception:
            logger.debug("Could not open video", exc_info=True)

    while True:
        signals = [
            telemetry_pb2.VectorSignal(name=n, labels=[n], values=[_INITIAL_POS[i]], unit="rad")
            for i, n in enumerate(JOINT_NAMES)
        ]
        signals.append(telemetry_pb2.VectorSignal(
            name="gripper_force", labels=["force"], values=[0.0], unit="N",
        ))
        await publisher.publish_state(
            task_id=_LIVE_TASK_ID, stream_name="joint_states",
            signals=signals, state_type=telemetry_pb2.StatePayload.JOINT,
        )

        if video is not None:
            result = video.read_next_jpeg()
            if result:
                await publisher.push_live_video_chunk("front_camera", result[0], codec="jpeg", keyframe=True)

        await asyncio.sleep(1.0)


# ── task stream ──────────────────────────────────────────────────────────────

async def stream_task(
    publisher: TelemetryPublisher,
    task_id: str,
    task_description: str = "",
    persist: bool = False,
    rate_hz: float = 5.0,
    duration_secs: Optional[float] = None,
) -> None:
    """Full-rate stream during task execution.
    Always pushes frames to live media plane.
    When persist=True, also uploads to blob store + publishes vision events for Parquet."""
    action_rows = _parse_actions_csv()
    if not action_rows:
        logger.warning("No action data in %s", ACTIONS_CSV)
        return

    tags = {"persist": "true"} if persist else None

    if task_description and persist:
        await publisher.publish_event(
            task_id=task_id, event_type="task_started",
            message=task_description, tags=tags,
        )

    video: Optional[VideoFrameReader] = None
    if VIDEO_FILE.exists():
        try:
            video = VideoFrameReader(VIDEO_FILE)
        except Exception:
            logger.warning("Could not open video %s", VIDEO_FILE, exc_info=True)

    interval = 1.0 / rate_hz
    idx = 0
    current_pos = list(_INITIAL_POS)
    start = asyncio.get_event_loop().time()

    try:
        while True:
            if duration_secs and (asyncio.get_event_loop().time() - start) >= duration_secs:
                break

            row = action_rows[idx % len(action_rows)]
            targets = row["targets"]
            current_pos = [cp + 0.3 * (tgt - cp) for cp, tgt in zip(current_pos, targets)]
            is_last = duration_secs and (asyncio.get_event_loop().time() - start + interval) >= duration_secs

            state_signals = [
                telemetry_pb2.VectorSignal(name=n, labels=[n], values=[current_pos[i]], unit="rad")
                for i, n in enumerate(JOINT_NAMES)
            ]
            state_signals.append(telemetry_pb2.VectorSignal(
                name="gripper_force", labels=["force"], values=[row["grip_force"]], unit="N",
            ))
            await publisher.publish_state(
                task_id=task_id, stream_name="joint_states",
                signals=state_signals, state_type=telemetry_pb2.StatePayload.JOINT,
                done=bool(is_last), tags=tags,
            )

            action_signals = [
                telemetry_pb2.VectorSignal(name=n, labels=[n], values=[targets[i]], unit="rad")
                for i, n in enumerate(JOINT_NAMES)
            ]
            await publisher.publish_action(
                task_id=task_id, stream_name="joint_commands",
                signals=action_signals,
                action_type=telemetry_pb2.ActionPayload.JOINT_POSITION,
                attributes={"cmd_type": row["cmd_type"]},
                done=bool(is_last), tags=tags,
            )

            if idx % 2 == 0 and video is not None:
                result = video.read_next_jpeg()
                if result is not None:
                    frame_data, frame_idx = result
                    await publisher.push_live_video_chunk("front_camera", frame_data, codec="jpeg", keyframe=(frame_idx % 30 == 0))

                    if persist:
                        try:
                            uri = await publisher.upload_blob(
                                robot_id=publisher.robot_id, stream_name="front_camera",
                                filename=f"frame_{frame_idx:06d}.jpg", data=frame_data,
                                mime_type="image/jpeg", task_id=task_id,
                            )
                            blob_ref = telemetry_pb2.BlobRef(
                                uri=uri, mime_type="image/jpeg", encoding="rgb8",
                                width=video.width, height=video.height,
                                frame_index=frame_idx, byte_length=len(frame_data),
                            )
                            await publisher.publish_vision(
                                task_id=task_id, stream_name="front_camera",
                                blob_ref=blob_ref, camera_name="front",
                                done=bool(is_last), tags=tags,
                            )
                        except Exception:
                            logger.debug("Blob upload failed", exc_info=True)

            idx += 1
            await asyncio.sleep(interval)
    finally:
        if video is not None:
            video.close()
