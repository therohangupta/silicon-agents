"""Reference Model Agent package for the EDA chip-design agent fleet.

This package authors the golden behavioral model used for transaction-level checking. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``ReferenceModelAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import ReferenceModelAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['ReferenceModelAgent']  # Public export surface for ``from reference_model import …``.
