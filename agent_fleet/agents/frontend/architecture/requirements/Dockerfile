# Dockerfile for Requirements Agent (`requirements`).
# Builds a slim Python image that serves this agent's server.py on port 8202.
# The container does not bundle licensed EDA tools; tools.py returns not_run until EDA_FRAMEWORK is bound.

FROM python:3.11-slim
# Base image: CPython 3.11 on Debian slim — enough for FastAPI/uvicorn without CAD GUI libs.

WORKDIR /app
# Repository root inside the image; editable install expects packages/ at this level.

COPY . /app
# Copy the built agent_fleet context (compose build context) into /app.

RUN pip install --no-cache-dir -e .
# Install the fleet packages in editable mode so domains/, packages/, and agents resolve.

WORKDIR /app/agents/frontend/architecture/requirements
# Switch into this agent's directory so `python server.py` finds local agent.py and config.yaml.

EXPOSE 8202
# Document the HTTP port peers use (must match config.yaml connection.port).

CMD ["python", "server.py"]
# Default process: start AgentService (uvicorn) for /health and /tasks/execute.
