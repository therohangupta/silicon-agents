# Container image for the Reproduction Agent in the EDA chip-design fleet.
# Builds a slim Python runtime, installs the fleet package editable, then runs
# this agent's server.py so the orchestrator can reach host:8223.
# EDA role: shrinks failing seeds and waveforms so defects can be handed to RTL or TB owners.

# Slim base keeps image size down; 3.11 matches the fleet's Python baseline.
FROM python:3.11-slim

# Default working directory inside the image before the package is laid down.
WORKDIR /app
# Copy the build context (typically the agent_fleet tree) into /app.
COPY . /app
# Install the fleet package so domains.*, packages.*, and agent imports resolve.
RUN pip install --no-cache-dir -e .

# Switch into this specialist's directory so `python server.py` finds local agent.py.
WORKDIR /app/agents/frontend/verification/reproduction
# Port published in config.yaml connection.port — reproduction service.
EXPOSE 8223

# Process entry: load AgentService and serve FastAPI until the container stops.
CMD ["python", "server.py"]
