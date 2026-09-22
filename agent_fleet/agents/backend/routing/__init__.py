"""Backend routing agents package

Groups the routing lead and workers that close global routing, detailed routing repair, signal-integrity (SI) / noise repair, and antenna / manufacturability fixes after placement and CTS. Global routing assigns coarse resources; detailed routing commits wires/vias; SI and antenna agents clear electrical and process risks.

This package marker is intentionally import-light: concrete agent classes live in
nested agent directories (each with its own ``agent.py``). Importing this module
does not start HTTP servers or bind OpenROAD adapters; it only documents the
stage grouping for physical-design backend agents.
"""
