# Container image for the Verification Lead in the EDA chip-design fleet.
# Builds a slim Python runtime, installs the fleet package editable, then runs
# this agent's server.py so the orchestrator can reach host:8215.
# EDA role: coordinates UVM, formal, stimulus, regression, coverage, triage, reproduction, and the independent verification gate.

# Slim base keeps image size down; 3.11 matches the fleet's Python baseline.
FROM python:3.11-slim

# Default working directory inside the image before the package is laid down.
WORKDIR /app
# Copy the build context (typically the agent_fleet tree) into /app.
COPY . /app
# Install the fleet package so domains.*, packages.*, and agent imports resolve.
RUN pip install --no-cache-dir -e .

# Switch into this specialist's directory so `python server.py` finds local agent.py.
WORKDIR /app/agents/frontend/verification/verification_lead
# Port published in config.yaml connection.port — verification_lead service.
EXPOSE 8215

# Process entry: load AgentService and serve FastAPI until the container stops.
CMD ["python", "server.py"]
