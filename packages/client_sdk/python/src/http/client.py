from __future__ import annotations

"""Module ``client_sdk/python/src/http/client.py``.

HTTP client talking to the Gateway BFF REST API.

Part of the Gateway client SDK: callers use HTTP and WebSocket helpers to talk to the BFF without coupling to fleet_server gRPC.

Hand-written source for ``client.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class GatewayClient:
    """
    Minimal Python client for the Gateway REST API.

    Notes:
    - This is intentionally thin; it should mirror the gateway REST contract.
    - Add richer typed models as the contract stabilizes.
    """

    base_url: str = ""
    bearer_token: Optional[str] = None
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.base_url:
            from packages.platform_config import setting
            self.base_url = setting("GATEWAY_URL")

    def _headers(self) -> dict[str, str]:
        """``_headers`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        # Only when (self.bearer_token).
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        # Hand ``headers`` back to the caller.
        return headers

    def _request(self, method: str, path: str, json: Any | None = None) -> Any:
        """``_request`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        url = f"{self.base_url}{path}"
        # Hold ``httpx.Client(timeout=self.timeout_seconds)`` for the duration of the indented block.
        with httpx.Client(timeout=self.timeout_seconds) as client:
            # Local ``resp`` ← client.request(method, url, json=json, headers=self._headers()).
            resp = client.request(method, url, json=json, headers=self._headers())
            # Only when (resp.status_code >= 400).
            if resp.status_code >= 400:
                # Try the fallible work below.
                try:
                    # Local ``detail`` ← resp.json().get("detail").
                    detail = resp.json().get("detail")
                # On except Exception: recover or re-raise as appropriate.
                except Exception:
                    # Local ``detail`` ← resp.text.
                    detail = resp.text
                # Raise ``RuntimeError`` to signal this failure mode to callers.
                raise RuntimeError(detail or f"HTTP {resp.status_code}")
            # Hand ``resp.json()`` back to the caller.
            return resp.json()

    # Plans
    def list_plans(self) -> Any:
        """``list_plans`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("GET", "/api/plans")

    def get_plan(self, plan_id: int) -> Any:
        """``list_plans`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("GET", f"/api/plans/{plan_id}")

    def create_plan(self, payload: dict[str, Any]) -> Any:
        """``get_plan`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("POST", "/api/plans", json=payload)

    def allocate_plan(self, plan_id: int, allocation_strategy: str) -> Any:
        """``create_plan`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("POST", f"/api/plans/{plan_id}/allocate", json={"allocation_strategy": allocation_strategy})

    def start_plan(self, plan_id: int) -> Any:
        """``allocate_plan`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("POST", f"/api/plans/{plan_id}/start")

    # Tasks
    def list_tasks(self, plan_id: Optional[int] = None) -> Any:
        """``list_tasks`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        q = f"?plan_id={plan_id}" if plan_id is not None else ""
        # Hand ``self._request("GET", f"/api/tasks{q}")`` back to the caller.
        return self._request("GET", f"/api/tasks{q}")

    def update_task(self, task_id: int, payload: dict[str, Any]) -> Any:
        """``update_task`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("PATCH", f"/api/tasks/{task_id}", json=payload)

    def delete_task(self, task_id: int) -> Any:
        """``update_task`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("DELETE", f"/api/tasks/{task_id}")

    # Agents
    def list_agents(self, filter: str = "all") -> Any:
        """``list_agents`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("GET", f"/api/agents?filter={filter}")

    def register_agent(self, payload: dict[str, Any]) -> Any:
        """``list_agents`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("POST", "/api/agents/register", json=payload)

    def unregister_agent(self, agent_id: str) -> Any:
        """``register_agent`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._request("DELETE", f"/api/agents/{agent_id}")

