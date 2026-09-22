# fleets/

Fleet YAML files tell `scripts/startup.sh` (via `scripts/fleet_select.py`) **which
agent containers** to render into `docker-compose.agents.yml`.

Platform services (`docker-compose.yml`) always start; the fleet file only
selects agents. An empty selection (`agents: []`) is valid and starts no agents.

## The only key

A fleet document is a mapping with one key, `agents`. Each entry is a path
to an agent directory, or to that directory's `config.yaml`. Paths may be
written as `agents/frontend/architecture/requirements` or as
`frontend/architecture/requirements`.

```yaml
agents:
  - agents/frontend/architecture/requirements
  - agents/frontend/rtl/rtl_implementation
```

Selection logic lives in `domains/eda/fleet.py` (`select_agents`).

## Files in this directory

| File | What it starts |
|------|----------------|
| [platform-only.yaml](platform-only.yaml) | No agents (`agents: []`) — platform + dashboard only |
| [architecture.yaml](architecture.yaml) | Every agent under `agents/frontend/architecture/` |
| [frontend.yaml](frontend.yaml) | Every agent under `agents/frontend/` |
| [requirements-and-rtl.yaml](requirements-and-rtl.yaml) | `requirements` and `rtl_implementation` |

## Usage

From the repo root:

```bash
./agent_fleet/scripts/startup.sh agent_fleet/fleets/frontend.yaml
./agent_fleet/scripts/startup.sh agent_fleet/fleets/platform-only.yaml
./agent_fleet/scripts/startup.sh agent_fleet/fleets/requirements-and-rtl.yaml --build
```

Inspect a fleet without starting Compose:

```bash
cd agent_fleet
python3 scripts/fleet_select.py names fleets/frontend.yaml
python3 scripts/fleet_select.py count fleets/frontend.yaml
```
