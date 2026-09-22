# NATS / bus consumers

Background asyncio consumers that connect the gateway to message buses.

## Contents

| File | Role |
|------|------|
| `__init__.py` | Package docstring (no auto-start) |
| `telemetry_consumer.py` | Durable `gateway-realtime` consumer on `telemetry.>`; latest-state cache + WS fan-out |

## Wiring

Started from `app.lifespan` after `NatsJetStreamBus.connect()` and
`ensure_stream("TELEMETRY", ["telemetry.>"])`. Cancelled on shutdown.

## Consumers of this package

- `routers/agent_telemetry.py` — `subscribe_ws`, `get_latest_state`, `unsubscribe_ws`
- `app.py` — `run_telemetry_consumer(bus)`
