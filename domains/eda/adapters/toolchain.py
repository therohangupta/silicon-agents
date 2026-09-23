"""HTTP client adapter for the isolated OSS EDA toolchain sidecar."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..schemas.artifact import ArtifactRef
from ..schemas.messages import JobHandle, ToolObservation


class ToolchainAdapter:
    """Run approved EDA recipes through the sidecar, never local shell commands."""

    framework = "yosys"

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 130.0) -> None:
        self.base_url = (base_url or os.environ.get("EDA_TOOLCHAIN_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError("EDA_TOOLCHAIN_URL is required for the toolchain adapter")
        self.timeout_seconds = timeout_seconds

    def invoke(
        self, operation: str, params: dict[str, Any], *, agent_id: str = ""
    ) -> ToolObservation:
        """Submit one bounded operation and convert the sidecar response."""
        payload = json.dumps({
            "operation": operation,
            "params": params,
            "agent_id": agent_id,
        }).encode()
        request = Request(
            f"{self.base_url}/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read())
        except HTTPError as error:
            detail = error.read().decode(errors="replace")
            return self._failed(operation, agent_id, f"toolchain rejected request: {detail}")
        except URLError as error:
            return self._failed(operation, agent_id, f"toolchain unavailable: {error.reason}")

        framework = result.get("framework", self.framework)
        artifacts = [
            ArtifactRef(
                uri=item["uri"],
                type=item.get("type", ""),
                producer_task=str(params.get("task_id", "")),
                tool=framework,
                complete=result["status"] == "succeeded",
            )
            for item in result.get("artifacts", [])
        ]
        return ToolObservation(
            framework=framework,
            operation=operation,
            status=result["status"],
            summary=result["summary"],
            metrics=result.get("metrics", {}),
            artifact_refs=artifacts,
            agent_id=agent_id,
            job=JobHandle(
                job_id=result["job_id"],
                scheduler="eda-toolchain",
                task_id=str(params.get("task_id", "")),
                workspace=result.get("workspace", ""),
                command_manifest=result.get("command_manifest", ""),
                state=result.get("state", result["status"]),
            ),
        )

    def _failed(self, operation: str, agent_id: str, summary: str) -> ToolObservation:
        return ToolObservation(
            framework=self.framework,
            operation=operation,
            status="failed",
            summary=summary,
            agent_id=agent_id,
            job=JobHandle(job_id="toolchain-unavailable", scheduler="eda-toolchain", state="failed"),
        )
