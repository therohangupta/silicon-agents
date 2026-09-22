# Build from repo root: docker build -f services/storage_writer/Dockerfile -t storage-writer .
# Slim Python 3.11 matches the rest of the fleet images.
FROM python:3.11-slim

# Project root inside the container for editable install imports.
WORKDIR /app
# Copy full agent_fleet context (packages/, services/, pyproject).
COPY . .
# Install the distribution so `python -m services.storage_writer.src.main` works.
RUN pip install --no-cache-dir -e .

# Unbuffered logs for Docker logging drivers.
ENV PYTHONUNBUFFERED=1

# Default command: connect to NATS and run writer + compaction.
CMD ["python", "-m", "services.storage_writer.src.main"]
