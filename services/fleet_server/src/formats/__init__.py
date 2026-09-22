"""
Formats package for Fleet Server planner/allocator/executor schemas.

Re-exports are intentionally minimal: callers import concrete models from
``formats.formats`` (for example ``from ..formats.formats import Plan``).
This ``__init__`` exists so ``formats`` is a proper Python package and can
carry package-level documentation for discoverability.
"""
