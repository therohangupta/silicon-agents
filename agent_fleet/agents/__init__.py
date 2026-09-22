"""Top-level package marker for all chip-design agent trees.

``agent_fleet.agents`` is a namespace over frontend, backend, dft, validation,
and ``chip_flow_lead``. Individual agents are discovered by scanning each
agent directory's ``config.yaml`` rather than by importing this package's
``__all__``. See ``agents/README.md`` and ``TELEMETRY.md`` for layout and
observability paths.
"""
