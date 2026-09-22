"""Backend signoff agent package.

This package groups physical-design **signoff** workers and leads: parasitic extraction,
MMMC static timing, timing debug, power analysis, IR/EM, thermal/reliability, DRC/LVS,
ECO planning, and independent signoff validation.

It is a namespace package for discovery and documentation. Importing this module does not
start HTTP servers, bind ``EDA_FRAMEWORK``, or execute OpenROAD/OpenSTA/licensed tools.
Concrete agents live in child directories (for example ``drc_lvs``, ``sta_lead``) each with
their own ``agent.py``, ``tools.py``, ``server.py``, and ``config.yaml``.
"""
