# Dockerfile for the Equivalence agent (synthesis/equivalence).
# Builds a slim Python image that installs the fleet package editable and runs server.py.
# EDA note: the container hosts the HTTP agent only; Yosys/OpenROAD bind via EDA_FRAMEWORK.

# Base image: CPython 3.11 slim to keep the runtime small for many parallel agents.
FROM python:3.11-slim

# Establish /app as the project root inside the container filesystem.
WORKDIR /app
# Copy the repository (build context) into /app so editable install sees packages/.
COPY . /app
# Install the agent_fleet package in editable mode without retaining pip download caches.
RUN pip install --no-cache-dir -e .

# Switch WORKDIR to this agent's directory so ``python server.py`` finds local modules.
WORKDIR /app/agents/backend/synthesis/equivalence
# Declare the HTTP port published by config.yaml connection.port for this agent.
EXPOSE 8236

# Default container command: boot the FastAPI/uvicorn AgentService entrypoint.
CMD ["python", "server.py"]
