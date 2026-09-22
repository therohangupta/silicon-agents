# Silicon Agents fleet

A multi-agent control plane specialized for chip design. Shared packages hold the agent process, memory stores, and context-assembly primitives. `agent_fleet/domains/eda` holds EDA record types, scope keys, write-policy defaults, and the tool adapter. `agent_fleet/agents` holds one directory per agent.

Start a subset of the fleet from the repo root:

```bash
./agent_fleet/scripts/startup.sh agent_fleet/fleets/requirements-and-rtl.yaml
```

Other fleet files live in `agent_fleet/fleets/`. Pass `--build` when agent images need to be rebuilt.

The design this fleet follows is `etched_agentic_chip_design_system_v3.md`.

## Repository tree

```text
silicon-agents/                 # repo root (this README)
├── README.md                    # you are here
├── pyproject.toml               # pointer: install from agent_fleet/
├── requirements.txt             # convenience dependency pins
└── agent_fleet/                 # installable package + Compose + docs
    ├── README.md                # package overview, architecture, quick start
    ├── pyproject.toml           # canonical Python package metadata (agentctl)
    ├── docker-compose.yml       # platform + memory-plane services
    ├── docker-compose.dev.yml   # live-reload overlay
    ├── docker-compose.agents.yml# GENERATED agent project (silicon-agents)
    ├── fleets/                  # which agents scripts/startup.sh starts
    ├── deploy/                  # config bind-mounted into Compose
    ├── docs/                    # design / runbook index
    ├── packages/                # shared Python libraries
    ├── services/                # fleet_server, gateway, telemetry, dashboard, …
    ├── agents/                  # one directory per agent
    ├── domains/                 # e.g. domains/eda fleet selection
    ├── cli/                     # agentctl
    └── scripts/                 # startup.sh, fleet_select, demos, DB helpers
```

## Documentation map

| Doc | Contents |
|-----|----------|
| [agent_fleet/README.md](agent_fleet/README.md) | Services, packages, architecture, quick start, full directory structure |
| [agent_fleet/docs/README.md](agent_fleet/docs/README.md) | Index of design docs (RUN, DESIGN, REPO_LAYOUT, telemetry, …) |
| [agent_fleet/fleets/README.md](agent_fleet/fleets/README.md) | Fleet YAML: an `agents:` list of directory paths |
| [agent_fleet/deploy/README.md](agent_fleet/deploy/README.md) | Deploy-time config snippets (e.g. OpenSearch) |
| [etched_agentic_chip_design_system_v3.md](etched_agentic_chip_design_system_v3.md) | System design the agents implement |

Inline comments also document glue files: `agent_fleet/scripts/startup.sh`, both `pyproject.toml` files, `requirements.txt`, and the `docker-compose*.yml` / `.dockerignore` files under `agent_fleet/`.
