# Gateway service

HTTP/WebSocket edge for the Agent Fleet dashboard and operators.

## Role

The gateway is a FastAPI application that:

- Exposes REST under `/api` for agents, goals, plans, tasks, embodiments, methods, strategies, metrics, and telemetry.
- Bridges those calls to the fleet manager over gRPC (`GRPCBridge`).
- Fans real-time invalidation and telemetry to browsers over WebSockets.
- Optionally consumes NATS JetStream `telemetry.>` for live agent telemetry.
- Proxies agent health from the Telemetry service and blob reads from local or S3 storage.

## Layout

| Path | Purpose |
|------|---------|
| `Dockerfile` | Container image: install repo editable, run uvicorn on port 8000 |
| `src/` | Application package (`main` → `app` → routers/services) |

## Runtime entry

```bash
# From services/gateway (module path used in Docker)
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Key env (via `packages.config`): `GRPC_SERVER_ADDRESS`, `DATABASE_URL`, `NATS_URL`, `TELEMETRY_URL`, `CORS_ORIGINS`, blob storage settings.

## Health

`GET /health` returns `{ "status": "healthy", "service": "agent-fleet-dashboard" }` for load balancers.
