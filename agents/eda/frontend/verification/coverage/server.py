"""HTTP service entrypoint for the Coverage Agent.

In the EDA agent fleet, each verification specialist runs as its own process
(often a container) exposing health and task-execute endpoints. This module is
that process for ``coverage``: it puts this agent directory on ``sys.path``, loads
``CoverageAgent`` and ``config.yaml``, wraps them in ``AgentService``, and
exposes the FastAPI ``app`` for uvicorn or ``server.run()``.

Preserving bootstrap order matters: ``sys.path`` must be mutated before
``from agent import …`` so the local ``agent.py`` wins over any other module
named ``agent``.
"""

import sys  # Mutated before the local agent module is imported so sibling agent.py wins.
from pathlib import Path  # Resolves this file's directory independent of process cwd.

# Directory containing agent.py, tools.py, and config.yaml. Absolute so launch cwd does not matter.
_AGENT_DIR = Path(__file__).resolve().parent
if str(_AGENT_DIR) not in sys.path:
    # Agent folders are not installed packages. Front of sys.path makes `import agent` local.
    sys.path.insert(0, str(_AGENT_DIR))

from agent import CoverageAgent  # Specialist class defined in this directory's agent.py.
from domains.eda.runtime import AgentService  # Shared FastAPI wrapper for EDA specialists.

# Bind YAML metadata + agent class into a runnable service (routes, lifecycle, tool dispatch).
server = AgentService.from_agent(
    _AGENT_DIR / "config.yaml",  # Fleet spec: skills, port 8220, boundaries, observability.
    CoverageAgent,  # Concrete EDAAgent subclass for coverage.
)
app = server.app  # ASGI application object for uvicorn / container CMD.

if __name__ == "__main__":
    # Direct process launch (local debug or Docker CMD ["python", "server.py"]).
    server.run()
