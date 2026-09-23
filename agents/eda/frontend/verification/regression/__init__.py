"""Regression Agent package for the EDA chip-design agent fleet.

This package schedules seed/test manifests on the simulator farm and collects pass/fail results. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``RegressionAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import RegressionAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['RegressionAgent']  # Public export surface for ``from regression import …``.
