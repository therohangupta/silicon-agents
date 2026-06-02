"""
Fake MOMA robot server (v2).
"""
import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlparse as _urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

from packages.robot_sdk.src.models import TaskRequest, TaskResult
from packages.robot_sdk.src.server.server_base import RobotServerBase
from packages.robot_sdk.src.schema.yaml_validator import YAMLValidator
from packages.robot_sdk.src.telemetry.publisher import TelemetryPublisher
from packages.config import (
    TELEMETRY_URL as _TELEMETRY_URL_DEFAULT,
    ROBOT_HEARTBEAT_INTERVAL_SECS,
    TELEMETRY_GRPC_PORT,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TELEMETRY_URL = os.environ.get("TELEMETRY_URL", _TELEMETRY_URL_DEFAULT).rstrip("/")
_tel_host = _urlparse(TELEMETRY_URL).hostname or "localhost"
TELEMETRY_GRPC_TARGET = os.environ.get("TELEMETRY_GRPC_TARGET", f"{_tel_host}:{TELEMETRY_GRPC_PORT}")
HEARTBEAT_INTERVAL = float(os.environ.get("HEARTBEAT_INTERVAL", str(ROBOT_HEARTBEAT_INTERVAL_SECS)))
TASK_DURATION = float(os.environ.get("TASK_DURATION", "8"))

_busy = False
_heartbeat_task: Optional[asyncio.Task] = None
_telemetry_publisher: Optional[TelemetryPublisher] = None
_idle_stream_task: Optional[asyncio.Task] = None


class FakeRobotServer(RobotServerBase):
    def __init__(self, robot_id: str, port: int):
        super().__init__(robot_id, port)
        logger.info("FakeRobotServer '%s' initialized on port %s.", robot_id, port)

    async def _execute_task(self, task_request: TaskRequest) -> TaskResult:
        global _busy, _idle_stream_task
        logger.info("Received task: %s", task_request.task_description)

        desc = task_request.task_description
        if "DO THE FOLLOWING TASK:" in desc:
            desc = desc.split("DO THE FOLLOWING TASK:")[1].strip()
        else:
            desc = desc.strip()
        _busy = True

        if _idle_stream_task is not None:
            _idle_stream_task.cancel()
            try:
                await _idle_stream_task
            except asyncio.CancelledError:
                pass
            _idle_stream_task = None

        telemetry_task = None
        try:
            if _telemetry_publisher is not None:
                import telemetry_adapter
                task_id = task_request.task_id or str(uuid.uuid4())
                telemetry_task = asyncio.create_task(
                    telemetry_adapter.stream_task(
                        _telemetry_publisher,
                        task_id=task_id,
                        task_description=desc,
                        persist=task_request.record_episode,
                        rate_hz=5.0,
                        duration_secs=TASK_DURATION,
                    )
                )

            await asyncio.sleep(TASK_DURATION)
            return TaskResult(
                success=True,
                message=f"Succeeded task!\nTask Given by Planner: '{desc}'\nTask Result Status by Robot: 'Completed: {desc}'",
                replan=False,
            )
        finally:
            _busy = False
            if telemetry_task is not None:
                telemetry_task.cancel()
                try:
                    await telemetry_task
                except asyncio.CancelledError:
                    pass
            if _telemetry_publisher is not None:
                import telemetry_adapter
                _idle_stream_task = asyncio.create_task(telemetry_adapter.stream_idle(_telemetry_publisher))


_instance: Optional[FakeRobotServer] = None
_task_server_host: Optional[str] = None
_task_server_port: Optional[int] = None


async def _send_heartbeat(host: Optional[str], port: Optional[int]):
    payload: dict = {"reachable": True, "busy": _busy}
    if host is not None and port is not None:
        payload["host"] = host
        payload["port"] = port
    while True:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(f"{TELEMETRY_URL}/ingest/heartbeat", json=payload)
        except Exception as e:
            logger.debug("Heartbeat failed: %s", e)
        await asyncio.sleep(HEARTBEAT_INTERVAL)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _heartbeat_task, _telemetry_publisher, _idle_stream_task
    if _instance is not None:
        _heartbeat_task = asyncio.create_task(_send_heartbeat(_task_server_host, _task_server_port))
        logger.info("Heartbeat task started -> %s every %ss", TELEMETRY_URL, HEARTBEAT_INTERVAL)

        try:
            _telemetry_publisher = TelemetryPublisher(
                robot_id=_instance.robot_id,
                robot_type="moma",
                grpc_target=TELEMETRY_GRPC_TARGET,
                blob_upload_url=f"{TELEMETRY_URL}/telemetry/blob",
            )
            await _telemetry_publisher.connect()
            logger.info("Telemetry publisher connected to %s", TELEMETRY_GRPC_TARGET)

            import telemetry_adapter
            _idle_stream_task = asyncio.create_task(telemetry_adapter.stream_idle(_telemetry_publisher))
            logger.info("Idle telemetry stream started")
        except Exception:
            logger.warning("Telemetry publisher failed to connect", exc_info=True)
            _telemetry_publisher = None

    yield

    if _idle_stream_task is not None:
        _idle_stream_task.cancel()
        try:
            await _idle_stream_task
        except asyncio.CancelledError:
            pass
    if _telemetry_publisher is not None:
        await _telemetry_publisher.close()
    if _heartbeat_task:
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "healthy", "robot_id": _instance.robot_id if _instance else None}


@app.post("/do_task", response_model=TaskResult)
async def do_task(request: TaskRequest):
    if _instance is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    try:
        return await _instance._execute_task(request)
    except Exception as e:
        logger.exception("Error processing task")
        raise HTTPException(status_code=500, detail=str(e)) from e


def main():
    global _instance, _task_server_host, _task_server_port
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to robot YAML config")
    args = parser.parse_args()
    validator = YAMLValidator()
    config = validator.validate_file(args.config)
    port = int(config["taskServer"]["port"])
    _task_server_host = os.environ.get("TASK_SERVER_HOST") or config["taskServer"].get("host", "localhost")
    _task_server_port = int(os.environ.get("TASK_SERVER_PORT", str(port)))

    robot_id = os.environ.get("ROBOT_ID", f"{_task_server_host}:{_task_server_port}")
    _instance = FakeRobotServer(robot_id=robot_id, port=port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
