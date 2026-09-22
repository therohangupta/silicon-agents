# Silicon Agents fleet

A multi-agent control plane specialized for chip design. Shared packages hold the agent process, memory stores, and context-assembly primitives. `domains/eda` holds EDA record types, scope keys, write-policy defaults, and the tool adapter. `agents` holds one directory per agent.

Start a subset of the fleet from the repo root:

```bash
./scripts/startup.sh fleets/requirements-and-rtl.yaml
```

Other fleet files live in `fleets/`. Pass `--build` when agent images need to be rebuilt.

The design this fleet follows is `etched_agentic_chip_design_system_v3.md`.

## Repository tree

```text
silicon-agents/                  # repo root (this README)
├── README.md
├── pyproject.toml               # canonical Python package (pip install -e .)
├── requirements.txt             # convenience dependency pins
├── docker-compose.yml           # platform + memory-plane services
├── docker-compose.dev.yml       # live-reload overlay
├── docker-compose.agents.yml    # GENERATED agent project (silicon-agents)
├── fleets/                      # which agents scripts/startup.sh starts
├── deploy/                      # config bind-mounted into Compose
├── docs/                        # design / runbook index
├── packages/                    # shared Python libraries
├── services/                    # fleet_server, gateway, telemetry, dashboard, …
├── agents/                      # one directory per agent
├── domains/                     # e.g. domains/eda fleet selection
├── cli/                         # agentctl
└── scripts/                     # startup.sh, fleet_select, demos, DB helpers
```

## Documentation map

| Doc | Contents |
|-----|----------|
| [docs/README.md](docs/README.md) | Index of design docs (RUN, DESIGN, REPO_LAYOUT, telemetry, …) |
| [fleets/README.md](fleets/README.md) | Fleet YAML: an `agents:` list of directory paths |
| [deploy/README.md](deploy/README.md) | Deploy-time config snippets (e.g. OpenSearch) |
| [etched_agentic_chip_design_system_v3.md](etched_agentic_chip_design_system_v3.md) | System design the agents implement |

Install and run details: [docs/RUN.md](docs/RUN.md). Inline comments document glue files (`scripts/startup.sh`, `pyproject.toml`, `requirements.txt`, `docker-compose*.yml`, `.dockerignore`).
