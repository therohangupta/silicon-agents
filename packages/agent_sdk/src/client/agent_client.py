from __future__ import annotations

"""Module ``agent_sdk/src/client/agent_client.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-to-agent / control-plane HTTP client helpers inside the agent SDK.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``agent_client.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import httpx

from ..contracts import AgentTaskRequest, AgentTaskResult
from ..server import AgentHealth


class AgentClient:
    """``AgentClient``"""
    def __init__(self, host: str, port: int, execute_path: str = "/tasks/execute"):
        """``AgentClient``"""
        if not host or not isinstance(port, int):
            # Raise ``ValueError`` to signal this failure mode to callers.
            raise ValueError("Host and port must be provided and valid.")
        # Bind ``base_url`` from f"http://{host}:{port}" for later use on this instance.
        self.base_url = f"http://{host}:{port}"
        # Bind ``execute_path`` from execute_path for later use on this instance.
        self.execute_path = execute_path
        # Bind ``_client`` from httpx.AsyncClient(timeout=None) for later use on this instance.
        self._client = httpx.AsyncClient(timeout=None)

    async def health(self) -> AgentHealth:
        """``health``"""
        response = await self._client.get(f"{self.base_url}/health")
        # Call ``response.raise_for_status``.
        response.raise_for_status()
        # Hand ``AgentHealth(**response.json())`` back to the caller.
        return AgentHealth(**response.json())

    async def execute_task(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute_task``"""
        response = await self._client.post(f"{self.base_url}{self.execute_path}", json=request.model_dump(mode="json"))
        # Call ``response.raise_for_status``.
        response.raise_for_status()
        # Hand ``AgentTaskResult(**response.json())`` back to the caller.
        return AgentTaskResult(**response.json())

    async def close(self) -> None:
        """``close``"""
        await self._client.aclose()
