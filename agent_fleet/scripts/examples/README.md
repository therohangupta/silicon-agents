# Legacy example population scripts

This directory held helpers that registered **physical/digital demo agents** into an older fleet layout. Those agent packages were removed when the repository standardized on the EDA **catalog** under **`agent_fleet/agents/`**.

## Current state

**`populate_fake.sh`** (if present) exits with a removal notice. It no longer mutates fleet registration state or starts containers.

Do not add new “fake” agents here — they would bypass **`domains.eda.registry.validate_catalog`** and drift from contract tests.

## Register a real catalog agent instead

1. Choose or create an agent directory with **`config.yaml`**, **`agent.py`**, **`tools.py`**, **`server.py`**, and **`Dockerfile`**.
2. Validate the tree:

   ```bash
   cd agent_fleet
   python scripts/check_agents.py
   ```

3. Register with the fleet manager when gRPC fleet-server is up:

   ```bash
   agentctl register agents/<domain>/<stage>/<name>/config.yaml
   ```

4. Or include the agent path in a **fleet YAML** and run **`scripts/startup.sh`**.

See [`../../agents/README.md`](../../agents/README.md) for directory conventions and [`../../cli/README.md`](../../cli/README.md) for **`agentctl`** commands.

## Testing without fake population

- **Unit tests** use in-memory or file **`EngineeringMemory`** backends — no registration script required.
- **Contract tests** under **`tests/contract/`** parametrize over real agent directories.
- **Live mesh tests** require Compose + **`SILICON_PLANE_TEST=1`** (see [`../../tests/README.md`](../../tests/README.md)).

## Related

| Path | Topic |
|------|--------|
| [`../agents/README.md`](../agents/README.md) | Removed demo Docker helpers |
| [`../README.md`](../README.md) | Supported maintainer scripts |
| [`../../fleets/README.md`](../../fleets/README.md) | Declarative agent sets for startup |

## Minimal fleet snippet (replacement for fake population)

```yaml
# agent_fleet/fleets/my-dev.yaml
agents:
  - agents/frontend/architecture/requirements
  - agents/frontend/rtl/rtl_implementation
```

Then:

```bash
./agent_fleet/scripts/startup.sh agent_fleet/fleets/my-dev.yaml
```

This declares exactly which catalog agents get Compose services — the same outcome the old populate script attempted, but validated by **`fleet.select_agents`** and **`check_agents.py`**.

## FAQ

**Q: Can I register agents without Compose?**  
A: Yes — use **`agentctl register`** against fleet-server when it is running; see [`../../cli/README.md`](../../cli/README.md).

**Q: Do I need fake data in Postgres first?**  
A: No — engineering memory for agents uses the plane/file backends; Postgres holds fleet control-plane state. Seed via normal goal/task flows or tests.

**Q: Why was populate_fake removed?**  
A: It bypassed catalog validation and duplicated agents already defined under **`agents/`**, breaking contract and embodiment tests.

## CI alignment

Pipelines should call **`check_agents.py`** and **`pytest tests/contract/`** instead of any populate script. That ensures the same agent set documented in fleet YAML matches what gateway embodiment and package contracts expect — something fake registration could desynchronize silently.

## Directory contents

| File | Status |
|------|--------|
| **`README.md`** | This guide |
| **`populate_fake.sh`** | Stub exit only — do not extend |

No Python modules live here; keep it that way so **`scripts/README.md`** remains an accurate index.
