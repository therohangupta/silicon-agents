# Container image for the ATPG Campaign agent (atpg_campaign) in the dft track.
# Builds the monorepo editable install, then runs this agent's server.py.

# Slim CPython base keeps DFT/lab specialist images small; no EDA GUI bundled.
FROM python:3.11-slim

# Install context is the agent_fleet repo root copied below.
WORKDIR /app

# Copy the full tree so `pip install -e .` sees packages/, domains/, and agents/.
COPY . /app

# Editable install wires agent_sdk, domains.eda, and shared packages into PYTHONPATH.
RUN pip install --no-cache-dir -e .

# Drop into this specialist's directory so `python server.py` finds local agent.py.
WORKDIR /app/agents/dft/atpg_campaign

# Publish the agent's HTTP port (must match connection.port in config.yaml).
EXPOSE 8227

# Boot the FastAPI AgentService entrypoint for atpg_campaign.
CMD ["python", "server.py"]
