"""Backend floorplan stage package.

This package contains the lead and worker agents that own partition floorplanning
before standard-cell placement: macro placement, pin assignment, power-grid (PDN)
construction, and early congestion/timing estimation from trial global place/route.

Importing this package does not start any agent HTTP servers. Each nested
agent directory is its own microservice booted via that directory's server.py.
"""
