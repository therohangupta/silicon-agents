"""Assertion/Formal Agent package for the EDA chip-design agent fleet.

This package writes SVA assertions, assumptions, and cover properties and drives formal proof campaigns. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``AssertionFormalAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import AssertionFormalAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['AssertionFormalAgent']  # Public export surface for ``from assertion_formal import …``.
