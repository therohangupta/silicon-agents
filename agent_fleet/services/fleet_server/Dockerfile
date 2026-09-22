# =============================================================================
# Fleet Server Dockerfile
# =============================================================================
# Build context MUST be the agent_fleet workspace root (parent of services/),
# because this image copies the whole tree and installs the editable package.
# Example (from agent_fleet/):
#   docker build -f services/fleet_server/Dockerfile -t fleet-server .
# =============================================================================

# Use a slim CPython 3.11 image to keep the runtime image small while matching
# the project's declared Python version for gRPC / asyncio / SQLAlchemy stack.
FROM python:3.11-slim

# Set the working directory inside the container to /app so subsequent COPY/RUN
# and the default CMD resolve relative paths against a known root.
WORKDIR /app

# Copy the entire build context (agent_fleet workspace) into /app.
# This includes packages/, services/, proto stubs, and pyproject/setup metadata
# required for `pip install -e .`.
COPY . .

# Install the workspace as an editable package without pip's download cache
# to reduce final image layer size. Editable install keeps import paths like
# `services.fleet_server.src` and `packages.*` working as in local dev.
RUN pip install --no-cache-dir -e .

# Force stdout/stderr to be line-buffered/unbuffered so container logs show
# gRPC and planner/allocator progress immediately (no delayed buffering).
ENV PYTHONUNBUFFERED=1

# Document that the Fleet Manager gRPC server listens on 50051 (insecure).
# Actual bind happens in serve(); this EXPOSE is metadata for orchestrators.
EXPOSE 50051

# Start the Fleet Manager via the package's __main__ module with verbose logs.
# Module path matches `python -m services.fleet_server.src` from workspace root.
CMD ["python", "-m", "services.fleet_server.src", "-v"]
