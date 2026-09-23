# Container image for the Chip Flow Lead agent (chip_flow_lead) in the chip_flow track.
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
WORKDIR /app/agents/chip_flow_lead

# Publish the agent's HTTP port (must match connection.port in config.yaml).
EXPOSE 8201

# Boot the FastAPI AgentService entrypoint for chip_flow_lead.
CMD ["python", "server.py"]
