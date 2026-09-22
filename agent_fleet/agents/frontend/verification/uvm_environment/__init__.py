"""UVM Environment Agent package for the EDA chip-design agent fleet.

This package builds the SystemVerilog UVM testbench environment around the DUT interfaces. It is one specialist under
``agents/frontend/verification`` and is coordinated by the verification lead
(except when this package *is* the lead).

Importing this package re-exports ``UvmEnvironmentAgent`` so fleet loaders and tests
can discover the agent class without importing ``agent.py`` by filesystem path.
"""

from agent import UvmEnvironmentAgent  # Local agent class; agent folders are not installed dist packages.

__all__ = ['UvmEnvironmentAgent']  # Public export surface for ``from uvm_environment import …``.
