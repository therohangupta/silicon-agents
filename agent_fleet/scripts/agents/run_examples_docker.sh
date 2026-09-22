#!/bin/bash
# Formerly launched physical demo agent containers (non-dev).
# The demo images/containers were removed from the fleet; this script is kept
# so old docs/CI that call it fail loudly with a clear message.

# Fail on unset vars and pipeline errors (strict mode for the stub).
set -euo pipefail
# Explain why the script no longer starts containers.
echo "The physical demo agent containers have been removed." >&2
# Non-zero exit so automation does not treat this as success.
exit 1
