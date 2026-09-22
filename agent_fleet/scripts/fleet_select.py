#!/usr/bin/env python3
"""Resolve a fleet YAML file and render the agent Compose project.

Subcommands:

- ``render`` — write a Compose file for the selected agents
- ``count`` — print how many agents the fleet selects
- ``names`` — print ``agent_id\\thost_port`` lines
- ``wait`` — poll each agent's ``/health`` until healthy or timeout

Selection rules live in ``domains.eda.fleet.select_agents``; this script is
the CLI wrapper used by startup flows and tests (see ``tests/test_fleet_select.py``).
"""

from __future__ import annotations

# argparse for subcommands (render/count/names/wait).
import argparse
# stderr for FleetError messages; exit codes via SystemExit.
import sys
# Deadline-based health waiting.
import time
# HTTP health checks without adding httpx as a script dependency.
import urllib.error
import urllib.request
from pathlib import Path

# Parse fleet YAML documents.
import yaml

# agent_fleet root for imports.
ROOT = Path(__file__).resolve().parents[1]
# Ensure domains.* resolves when run as a loose script.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Fleet selection + Compose rendering + typed errors.
from domains.eda.fleet import FleetError, render_compose, select_agents
from packages.platform_config import load_platform


def _load(path: str):
    """Load a fleet YAML file and return the selected agent list.

    Raises ``FleetError`` when the path is missing or the document fails
    selection validation. Returns the list from ``select_agents``.
    """
    # Resolve the fleet file path.
    file = Path(path)
    # Missing files are operator errors, not empty fleets.
    if not file.is_file():
        raise FleetError(f"Fleet file not found: {file}")
    # Parse a path-only fleet YAML document with its required agents list.
    document = yaml.safe_load(file.read_text())
    # Apply catalog selection rules.
    return select_agents(document)


def _render(path: str, out: str) -> int:
    """Render Compose YAML for the fleet file to *out*; return agent count.

    Creates parent directories for *out* as needed. Writes the full Compose
    document from ``render_compose`` and returns ``len(agents)`` for the
    caller to print.
    """
    # Select agents from the fleet document.
    agents = _load(path)
    # Destination Compose file path.
    target = Path(out)
    # Ensure parent dirs exist (e.g. .generated/).
    target.parent.mkdir(parents=True, exist_ok=True)
    # Write the Compose project text.
    target.write_text(render_compose(agents))
    # Return count so the CLI can print it.
    return len(agents)


def _wait(path: str, timeout: float) -> None:
    """Block until every selected agent's host health endpoint returns 200.

    Polls ``http://127.0.0.1:{host_port}/health`` once per second until all
    agents succeed or *timeout* seconds elapse. Raises ``FleetError`` naming
    the agents that never became healthy.
    """
    # Agents to wait on (id + published host port).
    agents = _load(path)
    # Absolute deadline from now.
    deadline = time.time() + timeout
    # Mutable map of still-pending agent_id -> host_port.
    pending = {agent.agent_id: agent.host_port for agent in agents}
    # Poll until empty or deadline.
    while pending and time.time() < deadline:
        for agent_id, port in list(pending.items()):
            try:
                # Hit the published host port health endpoint.
                platform = load_platform()
                health = f"{platform['http_scheme']}://{platform['process_host']}:{port}/health"
                with urllib.request.urlopen(health, timeout=2) as response:
                    # Only 200 removes the agent from pending.
                    if response.status == 200:
                        del pending[agent_id]
            except (urllib.error.URLError, TimeoutError, OSError):
                # Not up yet; try again next loop.
                continue
        # Brief pause between full sweeps when still pending.
        if pending:
            time.sleep(1)
    # Fail the command if anyone timed out.
    if pending:
        names = ", ".join(sorted(pending))
        raise FleetError(f"Agents did not become healthy: {names}")


def main() -> int:
    """Parse subcommands and dispatch; return process exit code (0 or 1).

    ``FleetError`` becomes a stderr message and exit 1; other exceptions
    propagate. Successful commands return 0.
    """
    # Top-level parser describing the tool.
    parser = argparse.ArgumentParser(description="Select agents from a fleet YAML file")
    # Require exactly one subcommand.
    sub = parser.add_subparsers(dest="command", required=True)

    # render fleet --out path
    render = sub.add_parser("render")
    render.add_argument("fleet")
    render.add_argument("--out", required=True)

    # count fleet
    count = sub.add_parser("count")
    count.add_argument("fleet")

    # names fleet
    names = sub.add_parser("names")
    names.add_argument("fleet")

    # wait fleet [--timeout N]
    wait = sub.add_parser("wait")
    wait.add_argument("fleet")
    wait.add_argument("--timeout", type=float, default=None)

    # Parse argv into Namespace.
    args = parser.parse_args()
    try:
        if args.command == "render":
            # Write Compose and print agent count.
            total = _render(args.fleet, args.out)
            print(total)
        elif args.command == "count":
            # Print selection size only.
            print(len(_load(args.fleet)))
        elif args.command == "names":
            # One TSV line per agent for scripting.
            for agent in _load(args.fleet):
                print(f"{agent.agent_id}\t{agent.host_port}")
        else:
            # Default branch is wait (required subparsers).
            timeout = args.timeout
            if timeout is None:
                timeout = float(load_platform()["startup"]["agent_health_timeout_seconds"])
            _wait(args.fleet, timeout)
    except FleetError as exc:
        # Operator-facing selection/wait failures.
        print(exc, file=sys.stderr)
        return 1
    # Success.
    return 0


# Standard script guard returning SystemExit code.
if __name__ == "__main__":
    raise SystemExit(main())
