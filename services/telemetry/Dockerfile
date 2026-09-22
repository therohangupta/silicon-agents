# Build from repo root: docker build -f services/telemetry/Dockerfile -t telemetry .
# Slim Python base keeps the image small while matching project Python 3.11.
FROM python:3.11-slim

# Install and run from /app so editable package layout matches Compose.
WORKDIR /app
# Copy the full agent_fleet build context (packages/, services/, pyproject).
COPY . .
# Editable install so `services.telemetry.src.main:app` imports resolve.
RUN pip install --no-cache-dir -e .

# Flush stdout/stderr immediately in container logs.
ENV PYTHONUNBUFFERED=1
# Document the HTTP port Compose publishes.
EXPOSE 9000

# Serve the FastAPI app on all interfaces at port 9000.
CMD ["uvicorn", "services.telemetry.src.main:app", "--host", "0.0.0.0", "--port", "9000"]
