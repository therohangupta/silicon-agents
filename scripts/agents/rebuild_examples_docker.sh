#!/bin/bash
# Formerly rebuilt physical demo agent Docker images.
# Demo images were removed; point operators at per-agent Dockerfiles instead.

# Fail on unset vars and pipeline errors (strict mode for the stub).
set -euo pipefail
# Explain that demo images are gone.
echo "The physical demo agent images have been removed." >&2
# Point to the replacement build path under agents/.
echo "Build from agents/<name>/Dockerfile instead." >&2
# Non-zero exit so automation does not treat this as success.
exit 1
