"""Verification Validator package for the EDA chip-design agent fleet.

This package re-reads primary reports and provenance to grade the gate without trusting the lead summary. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``VerificationValidatorAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import VerificationValidatorAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['VerificationValidatorAgent']  # Public export surface for ``from verification_validator import …``.
