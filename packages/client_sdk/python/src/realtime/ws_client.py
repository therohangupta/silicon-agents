from __future__ import annotations

"""Module ``client_sdk/python/src/realtime/ws_client.py``.

WebSocket / realtime event clients for Gateway live updates.

Part of the Gateway client SDK: callers use HTTP and WebSocket helpers to talk to the BFF without coupling to fleet_server gRPC.

Hand-written source for ``ws_client.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
from typing import Callable, Optional

import websockets

from .events import GatewayRealtimeMessage


class GatewayRealtimeClient:
    """``GatewayRealtimeClient`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def __init__(self, ws_base_url: str | None = None):
        """``GatewayRealtimeClient`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if not ws_base_url:
            from packages.platform_config import setting
            ws_base_url = setting("GATEWAY_WS_URL")
        self.ws_base_url = ws_base_url.rstrip("/")

    async def watch_global_updates(self, on_message: Callable[[GatewayRealtimeMessage], None]) -> None:
        """``__init__`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        url = f"{self.ws_base_url}/ws/global-updates"
        # Hold ``websockets.connect(url)`` for the duration of the indented block.
        async with websockets.connect(url) as ws:
            # Loop: async for msg in ws.
            async for msg in ws:
                # Try the fallible work below.
                try:
                    # Call ``on_message``.
                    on_message(json.loads(msg))
                # On except Exception: recover or re-raise as appropriate.
                except Exception:
                    pass

    async def watch_plan_execution(self, plan_id: int, on_message: Callable[[GatewayRealtimeMessage], None]) -> None:
        """``watch_plan_execution`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        url = f"{self.ws_base_url}/ws/execution/{plan_id}"
        # Hold ``websockets.connect(url)`` for the duration of the indented block.
        async with websockets.connect(url) as ws:
            # Loop: async for msg in ws.
            async for msg in ws:
                # Try the fallible work below.
                try:
                    # Call ``on_message``.
                    on_message(json.loads(msg))
                # On except Exception: recover or re-raise as appropriate.
                except Exception:
                    pass

