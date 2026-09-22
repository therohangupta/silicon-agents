#!/usr/bin/env python3
"""Render the platform deployment manifest from ``config/platform.yaml``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.platform_config import PlatformConfigError, render_compose_template, shell_exports


def main() -> int:
    """Render a complete Compose manifest or startup-only shell exports."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default=ROOT / "docker-compose.yml", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--shell", action="store_true")
    args = parser.parse_args()
    if args.shell == (args.out is not None):
        parser.error("provide exactly one of --shell or --out")
    try:
        if args.shell:
            print(shell_exports(), end="")
        else:
            print(render_compose_template(args.template, args.out))
    except PlatformConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
