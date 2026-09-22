"""HTTP entrypoint for the Clock Validation Agent.

Wires ``ClockValidationAgent`` into ``domains.eda.server.AgentService`` using this directory's
``config.yaml``. The resulting FastAPI ``app`` exposes health and task-execute
endpoints on port 8248 (see connection.port in the YAML). Running this
file as ``__main__`` starts the uvicorn loop via ``server.run()``.

EDA meaning: this process does not itself route wires or build clocks; it hosts
the agent that plans/calls tools whose adapters (when bound) talk to OpenROAD
or other engines. Until an adapter is bound, tools return ``not_run`` observations.
"""

# sys.path mutation lets ``from agent import ...`` resolve when cwd differs from package layout.
import sys
# Path locates the agent directory that holds config.yaml, agent.py, and tools.py.
from pathlib import Path

# Absolute directory of this server module (the agent package root).
_AGENT_DIR = Path(__file__).resolve().parent
# Ensure the agent directory is importable so local ``agent`` and ``tools`` modules resolve.
if str(_AGENT_DIR) not in sys.path:
    # Prepend (not append) so this agent's modules win over similarly named packages.
    sys.path.insert(0, str(_AGENT_DIR))

# Concrete agent class whose spec was loaded from config.yaml at import time.
from agent import ClockValidationAgent
# AgentService builds the FastAPI app and dispatches /tasks/execute to EdaAgent.handle.
from domains.eda.server import AgentService

# Construct the service by pairing YAML connection/skills with the agent class.
server = AgentService.from_agent(
    _AGENT_DIR / "config.yaml",  # authoritative port, skills, boundaries, memory policy
    ClockValidationAgent,  # handler class for this physical-design stage
)
# ASGI application object for uvicorn / container CMD.
app = server.app

# Allow ``python server.py`` to block and serve (Docker CMD uses this path).
if __name__ == "__main__":
    # Start the HTTP server; binds using connection settings from config.yaml.
    server.run()
