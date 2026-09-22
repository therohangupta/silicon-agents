# Application package (`src`)

Python package that implements the Agent Fleet gateway ASGI service.

## Modules

| File | Responsibility |
|------|----------------|
| `__init__.py` | Package docstring |
| `main.py` | uvicorn entry (`app` re-export) |
| `app.py` | FastAPI factory, CORS, metrics middleware, lifespan |
| `config.py` | Re-exports from `packages.config` |
| `dependencies.py` | Singleton `GRPCBridge` for `Depends()` |
| `grpc_bridge.py` | Fleet manager gRPC client + dict adapters + DB plan extras |

## Subpackages

- `routers/` — HTTP and WebSocket route handlers
- `services/` — health, YAML scan, ports, telemetry HTTP client
- `models/` — Pydantic request/response models
- `consumers/` — NATS JetStream telemetry consumer

## Import path

With cwd `services/gateway` (or Docker WORKDIR), use `src.main:app`. The repo
must be installed editable so `packages.*` resolves.
