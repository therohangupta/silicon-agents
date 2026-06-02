FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "services.storage_writer.src.main"]
