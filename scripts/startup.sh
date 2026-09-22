#!/usr/bin/env bash
# =============================================================================
# startup.sh — brings up the local silicon stack.
# Lives at scripts/startup.sh.
#
# What this script starts (always, unless a step fails):
#   1. Platform Compose project (docker-compose.yml): Postgres,
#      fleet-server, gateway, telemetry, NATS, memory-plane stores, etc.
#   2. Agent Compose project "silicon-agents" (docker-compose.agents.yml),
#      whose service list is *generated* from the fleet YAML you pass in.
#   3. Dashboard Vite process on the host (http://127.0.0.1:5173), if not already up.
#
# Usage examples:
#   ./scripts/startup.sh fleets/frontend.yaml
#   ./scripts/startup.sh fleets/architecture.yaml
#   ./scripts/startup.sh fleets/requirements-and-rtl.yaml
#   ./scripts/startup.sh fleets/requirements-and-rtl.yaml --build
#
# The YAML lists agent directories under agents:. See fleets/.
# =============================================================================

# Exit on first failing command (-e), treat unset vars as errors (-u), and fail
# pipelines if any stage fails (-o pipefail). Keeps partial startups from looking "ok".
set -euo pipefail

# This file lives at scripts/startup.sh. APP and ROOT are the repo root. Relative fleet paths resolve under ROOT.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT="${APP}"

# First positional argument: path to a fleet YAML (required). Empty until we check.
FLEET="${1:-}"

# BUILD flag: 0 = reuse images (--no-build); 1 = rebuild platform/agents (--build).
BUILD=0

# If no fleet path, or the user asked for help, print usage to stderr and exit 2
# (conventional for CLI usage errors).
if [[ -z "${FLEET}" || "${FLEET}" == "-h" || "${FLEET}" == "--help" ]]; then
  echo "usage: ./scripts/startup.sh fleets/<fleet>.yaml [--build]" >&2
  exit 2
fi

# Consume the fleet path from "$@"; remaining args are optional flags only.
shift

# Walk remaining arguments. Only --build is recognized; anything else is fatal.
for arg in "$@"; do
  if [[ "${arg}" == "--build" ]]; then
    # Force image rebuilds for platform and (later) agent Compose projects.
    BUILD=1
  else
    echo "Unknown argument ${arg}" >&2
    exit 2
  fi
done

# If FLEET is a relative path (does not start with /), make it absolute under ROOT
# so later tools work regardless of the caller's cwd.
if [[ "${FLEET}" != /* ]]; then
  FLEET="${ROOT}/${FLEET}"
fi

# Fail fast if the fleet file is missing (typo or wrong path).
if [[ ! -f "${FLEET}" ]]; then
  echo "Fleet file not found: ${FLEET}" >&2
  exit 1
fi

# All subsequent relative paths / docker compose defaults are relative to repo root.
cd "${APP}"

# Startup variables come directly from config/platform.yaml. The repository
# .env is never generated or sourced here; it stays operator-owned secrets.
eval "$(python3 scripts/render_platform_compose.py --shell)"

# Complete platform deployment manifest rendered from config/platform.yaml.
# Kept beside the template so all relative build and volume paths stay valid.
PLATFORM_COMPOSE_FILE="${APP}/docker-compose.platform.generated.yml"
python3 scripts/render_platform_compose.py \
  --template "${APP}/docker-compose.yml" \
  --out "${PLATFORM_COMPOSE_FILE}" >/dev/null

# The root .env is user-owned secrets only. Compose expands its placeholders
# while reading the generated manifests; startup never generates that file.
SECRETS_FILE="${ROOT}/.env"
if [[ ! -f "${SECRETS_FILE}" ]]; then
  echo "Secret file not found: ${SECRETS_FILE}. Copy .env.example and provide its values." >&2
  exit 1
fi

# Destination for the *generated* agent Compose file. Overwritten every run by
# scripts/fleet_select.py render. Compose project name is set inside that YAML.
COMPOSE_FILE="${APP}/docker-compose.agents.yml"

# Host-side scratch dir for dashboard logs/pid and other runtime data mounts
# (also used by docker-compose.yml for nats/telemetry/git bind mounts).
mkdir -p "${APP}/.data"

# --- Fleet selection ---------------------------------------------------------
echo "Selecting agents from ${FLEET}"

# Render selected agents into docker-compose.agents.yml. stdout discarded; the
# file on disk is the artifact Compose will consume.
python3 scripts/fleet_select.py render "${FLEET}" --out "${COMPOSE_FILE}" >/dev/null

# How many agent services the fleet selected (0 is valid: platform-only fleets).
COUNT="$(python3 scripts/fleet_select.py count "${FLEET}")"

# Print selected agent names to the terminal for operator visibility.
python3 scripts/fleet_select.py names "${FLEET}"

# --- Platform Compose (default project; uses docker-compose.yml) -------------
echo "Starting platform containers"

# Bring up platform services detached (-d), wait for health (--wait), allow up to
# 240s for slow first boots (Cassandra/OpenSearch). --build vs --no-build follows
# the BUILD flag from the CLI.
if [[ "${BUILD}" == "1" ]]; then
  docker compose --env-file "${SECRETS_FILE}" -f "${PLATFORM_COMPOSE_FILE}" up -d --build --wait --wait-timeout "${PLATFORM_WAIT_TIMEOUT}"
else
  docker compose --env-file "${SECRETS_FILE}" -f "${PLATFORM_COMPOSE_FILE}" up -d --no-build --wait --wait-timeout "${PLATFORM_WAIT_TIMEOUT}"
fi

# --- Agent Compose project "silicon-agents" ----------------------------------
if [[ "${COUNT}" == "0" ]]; then
  # Platform-only fleet: tear down any leftover agent containers/networks from a
  # previous run so Docker Desktop does not show stale agent services.
  echo "Fleet file selects no agents; stopping the agent project"
  docker compose --env-file "${SECRETS_FILE}" -p "${AGENT_COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
else
  # Ensure the shared agent image exists and contains the selected agent package
  # directories. Rebuild when --build was passed, the image is missing, or selected
  # working_dir paths are absent inside the image.
  if [[ "${BUILD}" == "1" ]] || ! docker image inspect "${AGENT_IMAGE}" >/dev/null 2>&1; then
    echo "Building the agent image"
    docker compose --env-file "${SECRETS_FILE}" -p "${AGENT_COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" build
  else
    # Collect host-side working_dir paths for each selected agent by loading the
    # fleet YAML through domains.eda.fleet.select_agents (run from APP cwd).
    DIRS=()
    while IFS= read -r dir; do
      DIRS+=("${dir}")
    done < <(python3 - "${FLEET}" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, ".")
import yaml
from domains.eda.fleet import select_agents
agents = select_agents(yaml.safe_load(Path(sys.argv[1]).read_text()))
for agent in agents:
    print(agent.working_dir)
PY
)

    # Probe the existing image: print any selected working_dir paths that are not
    # directories inside the image. Non-empty MISSING means the image is stale.
    MISSING="$(docker run --rm --entrypoint python "${AGENT_IMAGE}" -c \
      'import os,sys; print(" ".join(p for p in sys.argv[1:] if not os.path.isdir(p)))' \
      "${DIRS[@]}")"
    if [[ -n "${MISSING}" ]]; then
      echo "Agent image is missing selected packages; rebuilding"
      docker compose --env-file "${SECRETS_FILE}" -p "${AGENT_COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" build
    fi
  fi

  # Start (or recreate) only the selected agent services. --remove-orphans drops
  # agents that were in a previous fleet but not this one. --no-build: image was
  # already ensured above.
  echo "Starting ${COUNT} agent container(s)"
  docker compose --env-file "${SECRETS_FILE}" -p "${AGENT_COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" up -d --remove-orphans --no-build

  # Block until selected agents report healthy.
  python3 scripts/fleet_select.py wait "${FLEET}" --timeout "${AGENT_HEALTH_TIMEOUT}"
fi

# --- Dashboard (host Vite, not a Compose service) ----------------------------
DASHBOARD="${APP}/services/dashboard-web"

# If something already answers on 5173, reuse it (idempotent re-runs).
if curl -sf -o /dev/null "http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"; then
  echo "Dashboard already listening on http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"
else
  # Dashboard is a local Node app; refuse to continue without npm.
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is not installed, so the dashboard was not started" >&2
    exit 1
  fi

  # First-time install of frontend dependencies into node_modules.
  if [[ ! -d "${DASHBOARD}/node_modules" ]]; then
    echo "Installing dashboard dependencies"
    (cd "${DASHBOARD}" && npm install)
  fi

  echo "Starting dashboard"
  (
    # Run Vite bound to loopback only; log to .data/dashboard.log; record PID for
    # later stop/debug. nohup + background so this shell can exit while Vite lives.
    cd "${DASHBOARD}"
    nohup node node_modules/vite/bin/vite.js --host "${DASHBOARD_HOST}" --port "${DASHBOARD_PORT}" \
      > "${APP}/.data/dashboard.log" 2>&1 &
    echo $! > "${APP}/.data/dashboard.pid"
  )

  # Poll up to ~60s for the Vite listener before declaring failure.
  ready=0
  for _ in $(seq 1 "${DASHBOARD_READY_ATTEMPTS}"); do
    if curl -sf -o /dev/null "http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "${ready}" != "1" ]]; then
    echo "Dashboard did not listen on port ${DASHBOARD_PORT}. See ${APP}/.data/dashboard.log" >&2
    exit 1
  fi
fi

# Final operator summary: where to point browsers / Compose project name for agents.
echo "Platform:  http://${PROCESS_HOST}:${GATEWAY_PUBLISHED_PORT}"
echo "Dashboard: http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"
echo "Agents:    ${COUNT} in Compose project ${AGENT_COMPOSE_PROJECT}"
