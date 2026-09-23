"""Backend synthesis stage package.

This package contains the lead and worker agents that own the RTL-to-netlist
portion of the chip-design backend flow: constraint generation (SDC), isolated
synthesis experiments, retiming/mapping exploration, logical and sequential
equivalence checking, and netlist structural quality audits.

Importing this package does not start any agent HTTP servers. Each nested
agent directory is its own microservice booted via that directory's server.py.
"""
