"""Reproduction Agent package for the EDA chip-design agent fleet.

This package shrinks failing seeds and waveforms so defects can be handed to RTL or TB owners. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``ReproductionAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import ReproductionAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['ReproductionAgent']  # Public export surface for ``from reproduction import …``.
