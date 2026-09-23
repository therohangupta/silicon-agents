#!/usr/bin/env python3
"""Render Compose manifests from platform YAML.

Generic values come from ``config/platform.yaml`` via ``packages.platform_config``.
EDA toolchain placeholders come from ``domains/eda/platform.yaml`` when the
template references ``EDA_TOOLCHAIN_*`` or when ``--with-eda`` is passed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.platform_config import PlatformConfigError, compose_values, render_compose_template

_EDA_PLACEHOLDER = re.compile(r"\$\{EDA_[A-Z0-9_]+:")


def compose_values_for_render(template: Path, with_eda: bool) -> dict[str, str]:
    values = compose_values()
    template_text = template.read_text()
    needs_eda = with_eda or _EDA_PLACEHOLDER.search(template_text) is not None
    if not needs_eda:
        return values
    try:
        from domains.eda.fleet.platform_config import EdaPlatformConfigError, extend_compose_values

        extend_compose_values(values)
    except ImportError as exc:
        raise PlatformConfigError(
            "Template requires EDA toolchain placeholders but domains.eda.fleet.platform_config "
            "is not importable"
        ) from exc
    except EdaPlatformConfigError as exc:
        raise PlatformConfigError(str(exc)) from exc
    return values


def main() -> int:
    """Render a complete Compose manifest or startup-only shell exports."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default=ROOT / "compose" / "docker-compose.yml", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--shell", action="store_true")
    parser.add_argument(
        "--with-eda",
        action="store_true",
        help="Merge domains/eda/platform.yaml toolchain placeholders",
    )
    args = parser.parse_args()
    if args.shell == (args.out is not None):
        parser.error("provide exactly one of --shell or --out")
    try:
        merged = compose_values_for_render(args.template, with_eda=args.with_eda)
        if args.shell:
            import shlex

            print("".join(f"export {k}={shlex.quote(v)}\n" for k, v in merged.items()), end="")
        else:
            print(render_compose_template(args.template, args.out, values=merged))
    except PlatformConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
