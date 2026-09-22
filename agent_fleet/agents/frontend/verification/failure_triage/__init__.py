"""Failure-Triage Agent package for the EDA chip-design agent fleet.

This package groups failing simulations by signature and routes clusters to RTL, TB, or infrastructure owners. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``FailureTriageAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import FailureTriageAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['FailureTriageAgent']  # Public export surface for ``from failure_triage import …``.
