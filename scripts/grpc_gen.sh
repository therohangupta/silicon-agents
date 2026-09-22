#!/bin/bash
# Generate Python gRPC stubs from all .proto files in packages/proto/.
# Usage: bash grpc_gen.sh
#
# Runs grpc_tools.protoc for fleet_manager and telemetry, then rewrites the
# generated *_pb2_grpc.py imports to relative form (`from . import …`) so the
# packages.proto package imports correctly under the editable install.

# Abort on first failing command so partial generation is obvious.
set -e

# Directory that holds .proto sources and generated *_pb2*.py outputs.
PROTO_DIR="$(dirname "$0")/../packages/proto"
# Write stubs next to the .proto files (in-tree generation).
OUT_DIR="$PROTO_DIR"

# --- fleet_manager.proto ---
# Compile fleet_manager messages + FleetManager service stubs.
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR/fleet_manager.proto"

# Fix absolute import emitted by protoc into a package-relative import (macOS sed -i '').
sed -i '' 's/import fleet_manager_pb2 as fleet__manager__pb2/from . import fleet_manager_pb2 as fleet__manager__pb2/' \
  "$OUT_DIR/fleet_manager_pb2_grpc.py"

# Confirm fleet_manager generation to the operator.
echo "Generated: fleet_manager_pb2.py, fleet_manager_pb2_grpc.py"

# --- telemetry.proto ---
# Compile telemetry messages + TelemetryIngestion service stubs.
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR/telemetry.proto"

# Same relative-import fix for telemetry grpc stub.
sed -i '' 's/import telemetry_pb2 as telemetry__pb2/from . import telemetry_pb2 as telemetry__pb2/' \
  "$OUT_DIR/telemetry_pb2_grpc.py"

# Confirm telemetry generation.
echo "Generated: telemetry_pb2.py, telemetry_pb2_grpc.py"
# Final summary with output directory path.
echo "All gRPC stubs generated in $OUT_DIR"
