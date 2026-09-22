"""Coverage Agent package for the EDA chip-design agent fleet.

This package defines covergroups, merges coverage databases, and reports uncovered requirements. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``CoverageAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import CoverageAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['CoverageAgent']  # Public export surface for ``from coverage import …``.
