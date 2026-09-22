# Shared image for silicon agents. Compose sets the working directory to one agent package.
# Build context is the agent_fleet repo root.
# Slim Python 3.11 matches fleet_server / telemetry / storage_writer images.
FROM python:3.11-slim

# Install root so editable package imports (packages.*, domains.*, agents.*) resolve.
WORKDIR /app
# Copy full repo context passed to docker build.
COPY . .
# Editable install of the agent_fleet distribution.
RUN pip install --no-cache-dir -e .

# Immediate log flushing under Docker.
ENV PYTHONUNBUFFERED=1
# Ensure /app is on sys.path even before site-packages links settle.
ENV PYTHONPATH=/app
