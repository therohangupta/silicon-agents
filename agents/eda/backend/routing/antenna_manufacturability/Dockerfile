# Base image: slim CPython 3.11 for a small agent runtime without full EDA tools baked in.
FROM python:3.11-slim

# Container workdir for installing the agent_fleet editable package from the build context.
WORKDIR /app
# Copy the build context (typically the agent_fleet tree) into /app.
COPY . /app
# Install the fleet package and dependencies in editable mode; no pip cache to keep layers small.
RUN pip install --no-cache-dir -e .

# Switch into this agent's directory so ``python server.py`` finds local agent/tools modules.
WORKDIR /app/agents/backend/routing/antenna_manufacturability
# Document the HTTP port from config.yaml connection.port (8253) for Antenna and Manufacturability Agent.
EXPOSE 8253

# Default process: run the FastAPI/uvicorn agent server for AntennaManufacturabilityAgent.
CMD ["python", "server.py"]
