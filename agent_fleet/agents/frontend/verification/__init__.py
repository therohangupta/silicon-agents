"""Frontend verification agent package for the EDA chip-design agent fleet.

This package groups every specialist that owns silicon verification for a
pinned RTL candidate: UVM environment construction, reference-model authoring,
assertion and formal proof campaigns, stimulus generation, regression
execution, coverage analysis, failure triage, failure reproduction, and the
independent verification gate.

The verification lead coordinates those specialists. Individual agent
subpackages under this directory each expose ``agent.py`` (domain agent class),
``tools.py`` (stable operation contracts), ``server.py`` (HTTP service entry),
and ``config.yaml`` (fleet metadata and skill bindings). Importing this package
does not register agents; fleet YAML and per-agent servers do that at runtime.
"""
