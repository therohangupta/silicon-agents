#!/usr/bin/env bash
# =============================================================================
# startup.sh — brings up the local silicon stack.
# Lives at scripts/startup.sh.
#
# What this script starts (always, unless a step fails):
#   1. The macOS-host EDA toolchain service (Yosys, embedded OpenSTA, OpenROAD,
#      and KLayout), which agents reach at host.docker.internal:8090.
#   2. Platform Compose project (compose/docker-compose.platform.generated.yml):
#      Postgres, fleet-server, gateway, telemetry, NATS, memory-plane stores, etc.
#   3. Agent Compose project "silicon-agents" (compose/docker-compose.agents.yml),
#      whose service list is *generated* from the fleet YAML you pass in.
#   4. Dashboard Vite process on the host (http://127.0.0.1:5173), if not already up.
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

# Startup needs PyYAML to render deployment manifests. Prefer an explicit
# interpreter, then common local installations, and fail before starting
# anything if none can load the repository's Python dependencies.
PYTHON_BIN=""
for candidate in "${PYTHON_BIN_OVERRIDE:-}" python3 python "${HOME}/miniconda3/bin/python"; do
  [[ -n "${candidate}" && -x "$(command -v "${candidate}" 2>/dev/null || true)" ]] || continue
  if "${candidate}" -c 'import yaml' >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v "${candidate}")"
    break
  fi
done
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "No Python runtime with PyYAML found; set PYTHON_BIN_OVERRIDE." >&2
  exit 1
fi

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
eval "$("${PYTHON_BIN}" scripts/render_platform_compose.py --shell)"

# Complete platform deployment manifest rendered from config/platform.yaml.
# Kept beside the template so all relative build and volume paths stay valid.
PLATFORM_COMPOSE_FILE="${APP}/compose/docker-compose.platform.generated.yml"
"${PYTHON_BIN}" scripts/render_platform_compose.py \
  --template "${APP}/compose/docker-compose.yml" \
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
COMPOSE_FILE="${APP}/compose/docker-compose.agents.yml"

# Host-side scratch dir for dashboard logs/pid and other runtime data mounts
# (also used by docker-compose.yml for nats/telemetry/git bind mounts).
mkdir -p "${APP}/.data"

# --- Host EDA toolchain -------------------------------------------------------
# EDA execution runs on macOS because this is where the locally built OpenROAD
# toolchain lives. Agents use the Docker Desktop host alias from the domain
# config, while this process binds only to loopback.
IFS='|' read -r \
  EDA_BIND_HOST EDA_PORT EDA_AGENT_HOST \
  EDA_PDK_ROOT EDA_DESIGN_ROOT EDA_WORKSPACE_ROOT EDA_ORFS_ROOT \
  EDA_YOSYS_BIN EDA_STA_BIN EDA_OPENROAD_BIN EDA_KLAYOUT_CMD < <(
  "${PYTHON_BIN}" - <<'PY'
import os
from pathlib import Path

import yaml

from domains.eda.platform_config import load_eda_platform

toolchain = load_eda_platform()["toolchain"]
profile = yaml.safe_load((Path("domains/eda/toolchain.yaml")).read_text())
provider_config = profile["provider"]["config"]
root = Path.cwd()

def path(value: str) -> str:
    candidate = Path(value).expanduser()
    return str(candidate if candidate.is_absolute() else root / candidate)

def command(value: str) -> str:
    return os.path.expanduser(value)

print("|".join((
    str(toolchain["bind_host"]),
    str(toolchain["port"]),
    str(toolchain["agent_host"]),
    path(provider_config["paths"]["pdk_root"]),
    path(provider_config["paths"]["design_root"]),
    path(provider_config["paths"]["workspace_root"]),
    path(provider_config["paths"]["orfs_root"]),
    command(provider_config["binaries"]["yosys"]),
    command(provider_config["binaries"]["opensta"]),
    command(provider_config["binaries"]["openroad"]),
    command(provider_config["binaries"]["klayout_command"]),
)))
PY
)
EDA_HEALTH_URL="http://${EDA_BIND_HOST}:${EDA_PORT}/healthz"

start_eda_toolchain() {
  if curl -sf "${EDA_HEALTH_URL}" >/dev/null; then
    echo "EDA toolchain already listening on ${EDA_HEALTH_URL}"
    return
  fi

  local toolchain_python=""
  local candidate
  for candidate in "${EDA_TOOLCHAIN_PYTHON:-}" python3 python "${HOME}/miniconda3/bin/python"; do
    [[ -n "${candidate}" && -x "$(command -v "${candidate}" 2>/dev/null || true)" ]] || continue
    if "${candidate}" -c 'import uvicorn' >/dev/null 2>&1; then
      toolchain_python="$(command -v "${candidate}")"
      break
    fi
  done
  if [[ -z "${toolchain_python}" ]]; then
    echo "No Python runtime with uvicorn found; set EDA_TOOLCHAIN_PYTHON." >&2
    exit 1
  fi

  local yosys_bin="${YOSYS_BIN:-${EDA_YOSYS_BIN}}"
  local openroad_bin="${OPENROAD_BIN:-${EDA_OPENROAD_BIN}}"
  if [[ ! -x "${openroad_bin}" ]]; then
    openroad_bin="$(command -v openroad 2>/dev/null || true)"
  fi
  if [[ ! -x "${yosys_bin}" ]]; then
    yosys_bin="$(command -v "${yosys_bin}" 2>/dev/null || true)"
  fi
  local sta_bin="${STA_BIN:-${EDA_STA_BIN}}"
  if [[ ! -x "${sta_bin}" ]]; then
    sta_bin="${openroad_bin}"
  fi
  local klayout_cmd="${KLAYOUT_CMD:-${EDA_KLAYOUT_CMD}}"
  local klayout_bin="${klayout_cmd%% *}"
  if [[ -z "${yosys_bin}" || ! -x "${yosys_bin}" ]]; then
    echo "Yosys is not executable; set YOSYS_BIN." >&2
    exit 1
  fi
  if [[ -z "${openroad_bin}" || ! -x "${openroad_bin}" ]]; then
    echo "OpenROAD is not executable; set OPENROAD_BIN." >&2
    exit 1
  fi
  if [[ ! -x "${klayout_bin}" ]]; then
    echo "KLayout is not installed; set KLAYOUT_CMD or install KLayout." >&2
    exit 1
  fi

  echo "Starting macOS EDA toolchain on ${EDA_HEALTH_URL}"
  nohup env \
    PDK_ROOT="${EDA_PDK_ROOT}" \
    DESIGN_ROOT="${EDA_DESIGN_ROOT}" \
    WORKSPACE_ROOT="${EDA_WORKSPACE_ROOT}" \
    ORFS_ROOT="${EDA_ORFS_ROOT}" \
    YOSYS_BIN="${yosys_bin}" \
    STA_BIN="${sta_bin}" \
    OPENROAD_BIN="${openroad_bin}" \
    KLAYOUT_CMD="${klayout_cmd}" \
    "${toolchain_python}" -m uvicorn services.eda_toolchain.main:app \
      --host "${EDA_BIND_HOST}" --port "${EDA_PORT}" \
      > "${APP}/.data/eda-toolchain.log" 2>&1 &
  echo $! > "${APP}/.data/eda-toolchain.pid"

  local ready=0
  for _ in $(seq 1 30); do
    if curl -sf "${EDA_HEALTH_URL}" >/dev/null; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "${ready}" != "1" ]]; then
    echo "EDA toolchain did not listen on ${EDA_HEALTH_URL}. See ${APP}/.data/eda-toolchain.log" >&2
    exit 1
  fi
}

start_eda_toolchain

# --- Fleet selection ---------------------------------------------------------
echo "Selecting agents from ${FLEET}"

# Render selected agents into docker-compose.agents.yml. stdout discarded; the
# file on disk is the artifact Compose will consume.
"${PYTHON_BIN}" scripts/fleet_select.py render "${FLEET}" --out "${COMPOSE_FILE}" >/dev/null

# How many agent services the fleet selected (0 is valid: platform-only fleets).
COUNT="$("${PYTHON_BIN}" scripts/fleet_select.py count "${FLEET}")"

# Print selected agent names to the terminal for operator visibility.
"${PYTHON_BIN}" scripts/fleet_select.py names "${FLEET}"

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
    done < <("${PYTHON_BIN}" - "${FLEET}" <<'PY'
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
  "${PYTHON_BIN}" scripts/fleet_select.py wait "${FLEET}" --timeout "${AGENT_HEALTH_TIMEOUT}"
fi

# --- Dashboard (host Vite, not a Compose service) ----------------------------
DASHBOARD="${APP}/services/dashboard-web"

# If a dashboard process already owns its port, reuse it. Vite can return 404
# while its client assets are still initializing, so a TCP listener is the
# correct liveness check here.
if nc -z "${DASHBOARD_HOST}" "${DASHBOARD_PORT}" >/dev/null 2>&1; then
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
    nohup node node_modules/vite/bin/vite.js --host "${DASHBOARD_HOST}" --port "${DASHBOARD_PORT}" --strictPort \
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
echo "EDA tools: http://${EDA_AGENT_HOST}:${EDA_PORT} (host runtime)"
echo "Dashboard: http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"
echo "Agents:    ${COUNT} in Compose project ${AGENT_COMPOSE_PROJECT}"
