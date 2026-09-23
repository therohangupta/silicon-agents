"""Package export for the CTS Agent.

This ``__init__`` re-exports ``CtsAgent`` so fleet scanners and tests can import the
agent class from the package root of ``cts/``. Importing this
module loads ``agent.py``, which reads ``config.yaml`` into an ``EDAAgentConfig`` via
``EDAAgent.load_config``. It does not open sockets; ``server.py`` is what serves HTTP.
"""

# Import the concrete EDA agent class defined beside this package marker.
from agent import CtsAgent

# Public export list used by ``from ... import *`` and documentation scanners.
__all__ = ['CtsAgent']
