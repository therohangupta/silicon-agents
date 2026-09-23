#!/usr/bin/env python3
"""Run timing_debug and placement_experiment skills against real OpenSTA/OpenROAD."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_tool(module_path: Path, fn_name: str):
    spec = importlib.util.spec_from_file_location(f"{module_path.name}_tools", module_path / "tools.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return getattr(mod, fn_name)


def main() -> None:
    from domains.eda.eda import bind_eda_adapter
    from domains.eda.eda.toolchain import ToolchainAdapter

    bind_eda_adapter(ToolchainAdapter())
    params = {"design_path": "gcd.v", "top": "gcd", "recipe": "nangate45-gcd-v1"}
    run_sta = _load_tool(ROOT / "agents/backend/signoff/timing_debug", "run_sta")
    run_global_placement = _load_tool(
        ROOT / "agents/backend/placement/placement_experiment", "run_global_placement"
    )
    print(json.dumps({
        "run_sta": run_sta(params=params),
        "run_global_placement": run_global_placement(params=params),
    }, indent=2))


if __name__ == "__main__":
    main()
