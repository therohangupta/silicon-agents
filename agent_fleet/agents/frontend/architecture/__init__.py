"""Frontend architecture agent package.

Groups the early-architecture specialists that precede detailed RTL: lead coordination,
requirements elicitation, interface contracts, performance modeling, power/area estimation,
and security/reliability obligations.

Importing this package does not register or start agents; each subdirectory is a separate
container entrypoint via its own `server.py`.
"""
