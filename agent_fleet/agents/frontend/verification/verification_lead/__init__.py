"""Verification Lead package for the EDA chip-design agent fleet.

This package coordinates UVM, formal, stimulus, regression, coverage, triage, reproduction, and the independent verification gate. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``VerificationLeadAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import VerificationLeadAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['VerificationLeadAgent']  # Public export surface for ``from verification_lead import …``.
