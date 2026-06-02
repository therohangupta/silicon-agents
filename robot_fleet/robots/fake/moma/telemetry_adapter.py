"""
MOMA telemetry adapter.

Live video via HTTP media plane. State via gRPC → NATS. Recording via blob store.
"""

import asyncio
import csv
import logging
import math
from pathlib import Path
from typing import Optional

from packages.proto import telemetry_pb2
from packages.robot_sdk.src.telemetry.publisher import TelemetryPublisher
from packages.robot_sdk.src.telemetry.video_reader import VideoFrameReader

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
JOINT_CSV = DATA_DIR / "joints.csv"
VIDEO_FILE = DATA_DIR / "sample_vid.MOV"

JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow", "wrist_1", "wrist_2", "wrist_3"]
_LIVE_TASK_ID = "__live__"


def _deg_to_rad(deg: float) -> float:
    return deg * math.pi / 180.0


def _parse_joints_csv() -> list[dict]:
    rows = []
    with open(JOINT_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "timestamp_ms": int(row["timestamp_ms"]),
                "positions": [
                    _deg_to_rad(float(row["shoulder_pan_deg"])),
                    _deg_to_rad(float(row["shoulder_lift_deg"])),
                    _deg_to_rad(float(row["elbow_deg"])),
                    _deg_to_rad(float(row["wrist1_deg"])),
                    _deg_to_rad(float(row["wrist2_deg"])),
                    _deg_to_rad(float(row["wrist3_deg"])),
                ],
                "gripper_pct": float(row["gripper_pct"]),
            })
    return rows


async def stream_idle(publisher: TelemetryPublisher) -> None:
    joint_rows = _parse_joints_csv()
    initial = joint_rows[0] if joint_rows else None

    video: Optional[VideoFrameReader] = None
    if VIDEO_FILE.exists():
        try:
            video = VideoFrameReader(VIDEO_FILE)
        except Exception:
            logger.debug("Could not open video", exc_info=True)

    while True:
        if initial:
            signals = [
                telemetry_pb2.VectorSignal(name=n, labels=[n], values=[initial["positions"][i]], unit="rad")
                for i, n in enumerate(JOINT_NAMES)
            ]
            signals.append(telemetry_pb2.VectorSignal(
                name="gripper", labels=["gripper_pct"],
                values=[initial["gripper_pct"] / 100.0], unit="unitless",
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


async def stream_task(
    publisher: TelemetryPublisher,
    task_id: str,
    task_description: str = "",
    persist: bool = False,
    rate_hz: float = 5.0,
    duration_secs: Optional[float] = None,
) -> None:
    joint_rows = _parse_joints_csv()
    if not joint_rows:
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
    start = asyncio.get_event_loop().time()

    try:
        while True:
            if duration_secs and (asyncio.get_event_loop().time() - start) >= duration_secs:
                break

            row = joint_rows[idx % len(joint_rows)]
            is_last = duration_secs and (asyncio.get_event_loop().time() - start + interval) >= duration_secs

            signals = [
                telemetry_pb2.VectorSignal(name=n, labels=[n], values=[row["positions"][i]], unit="rad")
                for i, n in enumerate(JOINT_NAMES)
            ]
            signals.append(telemetry_pb2.VectorSignal(
                name="gripper", labels=["gripper_pct"],
                values=[row["gripper_pct"] / 100.0], unit="unitless",
            ))
            await publisher.publish_state(
                task_id=task_id, stream_name="joint_states",
                signals=signals, state_type=telemetry_pb2.StatePayload.JOINT,
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
