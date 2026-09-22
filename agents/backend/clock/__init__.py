"""Backend clock agents package

Groups clock-tree synthesis (CTS) and independent clock validation. CTS builds the buffered clock network (skew, transition, insertion delay); validation re-checks reachability, generated clocks, gating, pulse width, and mode coverage before routing proceeds.

This package marker is intentionally import-light: concrete agent classes live in
nested agent directories (each with its own ``agent.py``). Importing this module
does not start HTTP servers or bind OpenROAD adapters; it only documents the
stage grouping for physical-design backend agents.
"""
