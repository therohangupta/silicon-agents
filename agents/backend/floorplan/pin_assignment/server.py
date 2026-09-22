"""HTTP entrypoint for the Pin-Assignment agent process.

Boot sequence for this microservice:

1. Ensure this agent directory is on ``sys.path`` so ``from agent import ...`` works
   when the container WORKDIR is this folder.
2. Import ``PinAssignmentAgent`` from ``agent.py`` (loads ``config.yaml`` into ``spec``).
3. Build ``AgentService`` via ``AgentService.from_agent(config.yaml, PinAssignmentAgent)``, which
   wraps the EdaAgent in the shared FastAPI/uvicorn HTTP surface.
4. Expose ``app`` for ASGI servers and call ``server.run()`` when executed as main.

EDA meaning: this process serves Block pin locations, metal layers, bus ordering, and legal feedthroughs against package/bump contracts and edge track capacity. Adapter target: OpenROAD place_pins. Pin density violations create unroutable boundaries and package mismatches.

The default listen port from config.yaml is 8240. Until ``EDA_FRAMEWORK`` binds an
adapter, tool calls return structured ``not_run`` observations rather than invoking
Yosys, OpenROAD, OpenSTA, or a licensed engine.

Side effects:
    Importing constructs the ASGI ``app``. Running as ``__main__`` starts uvicorn
    and blocks until the process is stopped.

Failures:
    Missing config.yaml or invalid AgentSpec aborts process start.
    Port bind errors occur if 8240 is already taken on the host.
"""

# sys is used to mutate the module search path for local agent imports.
import sys
# Path resolves this file's directory in a stable, symlink-aware way.
from pathlib import Path

# Absolute directory containing server.py, agent.py, tools.py, and config.yaml.
_AGENT_DIR = Path(__file__).resolve().parent
# When launched as ``python server.py``, Python may not include the agent dir on
# sys.path; insert it so ``import agent`` and ``import tools`` resolve locally.
if str(_AGENT_DIR) not in sys.path:
    # Prepend (not append) so this agent's modules win over similarly named packages.
    sys.path.insert(0, str(_AGENT_DIR))

# Concrete EdaAgent subclass for Pin-Assignment; importing loads config.yaml into spec.
from agent import PinAssignmentAgent
# Shared HTTP/service factory that turns an agent class + YAML into FastAPI routes.
from domains.eda.server import AgentService

# Construct the service by pairing this directory's config.yaml with PinAssignmentAgent.
server = AgentService.from_agent(
    # Agent manifest path (skills, boundary, connection.port=8240, context policy).
    _AGENT_DIR / "config.yaml",
    # Handler class whose tools.py callables implement the skills listed in YAML.
    PinAssignmentAgent,
)
# ASGI application object for uvicorn / container CMD.
app = server.app

# Standard process entry: ``python server.py`` starts the blocking HTTP server.
if __name__ == "__main__":
    # Bind host/port from config and serve /health plus /tasks/execute.
    server.run()
