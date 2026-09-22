"""Backend placement agents package

Groups the placement lead, experiment workers, multi-corner evaluator, and cross-partition boundary coordinator. Placement positions standard cells after floorplan and before CTS/routing; experiments stay isolated until a lead recommends advancement.

This package marker is intentionally import-light: concrete agent classes live in
nested agent directories (each with its own ``agent.py``). Importing this module
does not start HTTP servers or bind OpenROAD adapters; it only documents the
stage grouping for physical-design backend agents.
"""
