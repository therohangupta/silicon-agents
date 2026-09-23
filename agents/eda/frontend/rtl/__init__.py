"""Frontend RTL agent package.

Groups the register-transfer-level specialists used after architecture and before (or alongside)
functional verification: lead coordination, bounded RTL edits, clock/reset checks, CDC/RDC,
lint, low-power UPF, and block integration.

Importing this package does not register or start agents; each subdirectory is a separate
container entrypoint via its own `server.py`.
"""
