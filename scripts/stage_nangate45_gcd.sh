#!/usr/bin/env bash
# Stage Nangate45 + GCD collateral from the pinned ORFS checkout for local demos.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ORFS="${ROOT}/external/OpenROAD-flow-scripts/flow"
PDK="${ROOT}/tmp/pdk/nangate45"
GCD="${ROOT}/tmp/gcd"

if [[ ! -d "${ORFS}/platforms/nangate45" ]]; then
  echo "Missing ${ORFS}/platforms/nangate45 — clone OpenROAD-flow-scripts under external/ first." >&2
  exit 1
fi

mkdir -p "${PDK}/lib" "${PDK}/lef" "${GCD}"
cp "${ORFS}/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib" "${PDK}/lib/"
cp "${ORFS}/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef" "${PDK}/lef/"
cp "${ORFS}/platforms/nangate45/lef/NangateOpenCellLibrary.macro.lef" "${PDK}/lef/"
cp "${ORFS}/designs/src/gcd/gcd.v" "${GCD}/gcd.v"
cp "${ORFS}/designs/nangate45/gcd/constraint.sdc" "${GCD}/constraint.sdc"
cp "${ORFS}/designs/nangate45/gcd/grid_strategy-M1-M4-M7.tcl" "${GCD}/grid_strategy-M1-M4-M7.tcl"
cat > "${GCD}/README.md" <<EOF
# Nangate45 GCD (OpenROAD-flow-scripts)

RTL: \`external/OpenROAD-flow-scripts/flow/designs/src/gcd/gcd.v\`
SDC: \`external/OpenROAD-flow-scripts/flow/designs/nangate45/gcd/constraint.sdc\`
PDN: \`external/OpenROAD-flow-scripts/flow/designs/nangate45/gcd/grid_strategy-M1-M4-M7.tcl\`
PDK: \`tmp/pdk/nangate45\` (lib + lef copied from ORFS nangate45 platform)

Regenerate: \`./scripts/stage_nangate45_gcd.sh\`
EOF
echo "Staged PDK under tmp/pdk/nangate45 and GCD under tmp/gcd"
