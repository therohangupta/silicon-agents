"""Operator CLI package for the agent fleet (``agentctl``).

Exposes the Click entrypoint in ``agentctl`` and shared pretty-printers in
``printer``. Installed as a console script (see project packaging) so operators
can register agents, create goals/plans/tasks, and inspect fleet state over
gRPC without using the dashboard. This ``__init__`` only marks the package;
invoke ``cli.agentctl:main`` or the ``agentctl`` script rather than importing
side-effecting command registration at package import time in libraries.
"""
