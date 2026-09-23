"""HTTP entrypoint for the Constraint Generation and Validation agent process.

Boot sequence for this microservice:

1. Ensure this agent directory is on ``sys.path`` so ``from agent import ...`` works
   when the container WORKDIR is this folder.
2. Import ``ConstraintGenerationAgent`` from ``agent.py`` (loads ``config.yaml`` into ``eda_config``).
3. Build ``AgentService`` via ``AgentService.from_agent(config.yaml, ConstraintGenerationAgent)``, which
   wraps the EDAAgent in the shared FastAPI/uvicorn HTTP surface.
4. Expose ``app`` for ASGI servers and call ``server.run()`` when executed as main.

EDA meaning: this process serves SDC (Synopsys Design Constraints) authorship and audit: create_clock, create_generated_clock, set_input_delay / set_output_delay, clock uncertainty, clock groups, false paths, multicycle paths, and case analysis. Bad constraints silently create optimistic timing that later fails STA or equivalence.

The default listen port from config.yaml is 8233. Until ``EDA_FRAMEWORK`` binds an
adapter, tool calls return structured ``not_run`` observations rather than invoking
Yosys, OpenROAD, OpenSTA, or a licensed engine.

Side effects:
    Importing constructs the ASGI ``app``. Running as ``__main__`` starts uvicorn
    and blocks until the process is stopped.

Failures:
    Missing config.yaml or invalid EDAAgentConfig aborts process start.
    Port bind errors occur if 8233 is already taken on the host.
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

# Concrete EDAAgent subclass for Constraint Generation and Validation; importing loads config.yaml into spec.
from agent import ConstraintGenerationAgent
# Shared HTTP/service factory that turns an agent class + YAML into FastAPI routes.
from domains.eda.runtime import AgentService

# Construct the service by pairing this directory's config.yaml with ConstraintGenerationAgent.
server = AgentService.from_agent(
    # Agent manifest path (skills, boundary, connection.port=8233, context policy).
    _AGENT_DIR / "config.yaml",
    # Handler class whose tools.py callables implement the skills listed in YAML.
    ConstraintGenerationAgent,
)
# ASGI application object for uvicorn / container CMD.
app = server.app

# Standard process entry: ``python server.py`` starts the blocking HTTP server.
if __name__ == "__main__":
    # Bind host/port from config and serve /health plus /tasks/execute.
    server.run()
