# Base image: slim CPython 3.11 for a small signoff worker footprint (no GUI EDA tools baked in).
FROM python:3.11-slim

# Default working directory for the editable agent_fleet install at the repo root inside the image.
WORKDIR /app
# Copy the full build context (agent_fleet package + this agent) into /app for pip install.
COPY . /app
# Install the fleet package editable so ``domains.eda`` and ``packages.agent_sdk`` import cleanly.
# --no-cache-dir keeps the image smaller; signoff tool binaries are NOT installed here.
RUN pip install --no-cache-dir -e .

# Switch into this agent's directory so ``python server.py`` finds local agent/tools modules.
WORKDIR /app/agents/backend/signoff/power_analysis
# Publish the AgentService HTTP port for Power-Analysis Agent (vector-based and vectorless power estimation).
EXPOSE 8257

# Launch the FastAPI AgentService; orchestrator will hit /health and /tasks/execute.
CMD ["python", "server.py"]
