"""Domain packages that specialize the generic agent and memory kits.

This package is the root of first-party domain code at the repository root.
Each subdirectory is a vertical domain that takes the reusable building
blocks in ``packages`` (agent SDK, generic memory stores, context assembly)
and binds them to a specific engineering vocabulary and policy.

The EDA domain (``domains.eda``) is the chip-design specialization. It
defines design scope, record types, role-based tool actions, engineering
memory envelopes, context policies, agent specs loaded from ``config.yaml``,
and the ``EDAAgent`` base class that every silicon agent subclasses.

Nothing in this ``__init__`` module re-exports symbols. Callers import from
``domains.eda`` (or a deeper submodule) when they need concrete types. The
module exists so ``domains`` is a proper Python package and so documentation
can describe the layering: packages are generic; domains are specialized.
"""
