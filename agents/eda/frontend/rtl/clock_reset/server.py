"""HTTP entrypoint for the Clock/Reset Agent (`clock_reset`).

This module is the process main for the agent container. It adjusts `sys.path` so the
local `agent.py` is imported (agent directories are not installed as site-packages), builds
an `AgentService` from `config.yaml` plus `ClockResetAgent`, and exposes ASGI `app` for uvicorn.

In EDA terms this is how the **rtl** specialist becomes reachable on port 8210 for
`/health` and `/tasks/execute` calls from the fleet orchestrator. No RTL, UPF, or CDC tool
runs at import time; tools execute only when a task invokes skills from `tools.py`.
"""

import sys  # Mutated before the local agent module is imported so sibling agent.py wins.
from pathlib import Path  # Resolves this file's directory independent of process cwd.

_AGENT_DIR = Path(__file__).resolve().parent  # Absolute directory of this agent, independent of cwd.
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))  # Agent folders are not installed packages; this makes `import agent` local.

from agent import ClockResetAgent  # Local agent class bound to this directory's config.yaml.
from domains.eda.runtime import AgentService  # Shared FastAPI/uvicorn wrapper for EDA agents.

# Build the service: loads config.yaml, wires skills, and prepares HTTP routes.
server = AgentService.from_agent(
    _AGENT_DIR / "config.yaml",  # Spec path: ports, capabilities, boundaries, telemetry.
    ClockResetAgent,  # Agent class whose spec and tools back task execution.
)
app = server.app  # ASGI application object for uvicorn or AgentService.run().

if __name__ == "__main__":
    # Foreground server used by Dockerfile CMD and local debugging on port 8210.
    server.run()
