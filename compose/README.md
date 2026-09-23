# Docker Compose manifests

All Compose files live here so the repo root stays uncluttered. Paths inside these YAML files are relative to this directory (typically `..` for the repo root).

| File | Role |
|------|------|
| `docker-compose.yml` | Platform / memory-plane template (rendered before use) |
| `docker-compose.platform.generated.yml` | Rendered from `config/platform.yaml` — used by `scripts/startup.sh` |
| `docker-compose.dev.yml` | Live-reload overlay for gateway, fleet-server, telemetry |
| `docker-compose.agents.yml` | Generated agent project (`silicon-agents`) |

The EDA toolchain is a macOS host process, not a Compose sidecar. `scripts/startup.sh`
starts it and makes it available to agent containers as `host.docker.internal:8090`.
Stage Nangate45 + GCD once (requires `external/OpenROAD-flow-scripts`):

```bash
./scripts/stage_nangate45_gcd.sh
```

Examples (from repo root; pass secrets via the repo `.env`):

```bash
docker compose --env-file .env -f compose/docker-compose.platform.generated.yml up -d
./scripts/startup.sh fleets/requirements-and-rtl.yaml
```

Render manifests after editing YAML:

```bash
# Generic platform (config/platform.yaml only)
python scripts/render_platform_compose.py --out compose/docker-compose.platform.generated.yml
```
