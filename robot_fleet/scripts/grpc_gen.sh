#!/bin/bash
# Generate Python gRPC stubs from all .proto files in packages/proto/.
# Usage: bash grpc_gen.sh

set -e

PROTO_DIR="$(dirname "$0")/../packages/proto"
OUT_DIR="$PROTO_DIR"

# --- fleet_manager.proto ---
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR/fleet_manager.proto"

sed -i '' 's/import fleet_manager_pb2 as fleet__manager__pb2/from . import fleet_manager_pb2 as fleet__manager__pb2/' \
  "$OUT_DIR/fleet_manager_pb2_grpc.py"

echo "Generated: fleet_manager_pb2.py, fleet_manager_pb2_grpc.py"

# --- telemetry.proto ---
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR/telemetry.proto"

sed -i '' 's/import telemetry_pb2 as telemetry__pb2/from . import telemetry_pb2 as telemetry__pb2/' \
  "$OUT_DIR/telemetry_pb2_grpc.py"

echo "Generated: telemetry_pb2.py, telemetry_pb2_grpc.py"
echo "All gRPC stubs generated in $OUT_DIR"
