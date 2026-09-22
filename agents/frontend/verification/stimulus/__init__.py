"""Stimulus Agent package for the EDA chip-design agent fleet.

This package authors directed tests and constrained-random UVM sequences for coverage-driven verification. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``StimulusAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import StimulusAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['StimulusAgent']  # Public export surface for ``from stimulus import …``.
