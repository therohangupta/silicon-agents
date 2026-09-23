#!/bin/bash
# Formerly populated the fleet with physical/digital demo agent registrations.
# Demo agents were removed; fail loudly and point at registered agent YAML.

# Fail on unset vars and pipeline errors (strict mode for the stub).
set -euo pipefail
# Explain that demo agents are gone.
echo "The physical and digital demo agents have been removed." >&2
# Point operators at the registry registration path.
echo "Register a registered agent from agents/<name>/config.yaml instead." >&2
# Non-zero exit so automation does not treat this as success.
exit 1
