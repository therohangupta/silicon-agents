# =============================================================================
# Agent Fleet Gateway container image
# =============================================================================
# Build from the agent_fleet (or monorepo) root so COPY can see packages/,
# services/, and the editable install layout expected by pip install -e .
# Example:
#   docker build -f services/gateway/Dockerfile -t gateway .
# =============================================================================

# Base image: slim Python 3.11 keeps the runtime small while matching the
# project's declared Python version for FastAPI/uvicorn and gRPC stubs.
FROM python:3.11-slim

# Establish the install root inside the container; subsequent COPY/RUN steps
# treat this as the project root where pyproject/setup expects to live.
WORKDIR /app

# Copy the full build context (repo contents passed to docker build) so the
# editable install can resolve packages.* and services.* imports at runtime.
COPY . .

# Install the project in editable mode without caching wheels on the image
# layer, which keeps the image leaner and always picks up local package code.
RUN pip install --no-cache-dir -e .

# Force Python stdout/stderr to flush immediately so container logs show
# request and lifecycle messages without buffering delays.
ENV PYTHONUNBUFFERED=1

# Switch into the gateway service directory so the uvicorn module path
# `src.main:app` resolves relative to this WORKDIR.
WORKDIR /app/services/gateway

# Document that the HTTP API (and WebSocket upgrade) listens on port 8000;
# orchestration layers should publish/map this port to the host or mesh.
EXPOSE 8000

# Default process: run the FastAPI app factory export from src.main via uvicorn,
# binding all interfaces so the container is reachable from outside localhost.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
