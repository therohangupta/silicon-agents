"""HTTP entrypoint for the Extraction Agent.

This module wires ``ExtractionAgent`` into the shared ``AgentService`` so the orchestrator can
health-check and execute signoff tasks over HTTP. It is the process started by the
Dockerfile ``CMD`` and by local ``python server.py`` runs during bring-up.

The server does not itself invoke OpenROAD, OpenSTA, or licensed signoff tools; those
calls happen only when skills in ``tools.py`` are bound to a framework adapter. Until
then, tool calls return structured ``not_run`` observations while still exercising the
fleet control plane.

Domain: parasitic extraction (SPEF) for signoff STA and power. Listening port (see ``config.yaml`` / Dockerfile): 8254.
"""

import sys  # Mutate ``sys.path`` so local ``agent.py`` imports resolve inside the container.
from pathlib import Path  # Locate this agent's directory and ``config.yaml`` on disk.

# Absolute directory containing agent.py, tools.py, and config.yaml for this signoff worker.
_AGENT_DIR = Path(__file__).resolve().parent
# Ensure the agent package directory is importable before ``from agent import ...``.
# Required because Docker WORKDIR and local runs may not place this dir on PYTHONPATH.
if str(_AGENT_DIR) not in sys.path:
    # Prepend (not append) so this agent's ``agent`` module wins over any similarly named package.
    sys.path.insert(0, str(_AGENT_DIR))

from agent import ExtractionAgent  # Extraction Agent class with loaded signoff spec.
from domains.eda.runtime import AgentService  # Shared FastAPI service factory for EDA agents.

# Build the HTTP service from this directory's config.yaml and the concrete agent class.
# Side effect: constructs routes for /health and /tasks/execute using the declared skills.
server = AgentService.from_agent(
    _AGENT_DIR / "config.yaml",  # Manifest: port 8254, skills, boundaries for extraction.
    ExtractionAgent,  # Agent class whose tools implement SPEF completeness, extraction corners, OpenROAD estimate_parasitics.
)
# ASGI app object for uvicorn / FastAPI hosting (imported by some runners as ``app``).
app = server.app

if __name__ == "__main__":
    # Blocking serve loop: binds the configured host/port and processes signoff tasks.
    # Failure mode: raises if the port is taken or config.yaml cannot be parsed.
    server.run()
