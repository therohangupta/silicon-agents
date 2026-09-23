# EDA domain (`domains/eda`)

Chip-design agents under `agents/eda/` share this package. It is split by concern so nothing sits in a flat pile or a nested `eda/eda/` tree.

## Layout

| Package | Responsibility |
|---------|----------------|
| [`config/`](config/) | `EDAAgentConfig`, YAML loading, roles and operations |
| [`schemas/`](schemas/) | Tasks, messages, memory envelopes, enums |
| [`memory/`](memory/) | Engineering memory stores, placements, policy |
| [`runtime/`](runtime/) | `EDAAgent`, `AgentService`, `ContextService`, lead `build_workflow` |
| [`fleet/`](fleet/) | Registry (`registry`), compose selection (`compose`), workflow intake (`workflow`), deploy env (`platform_config`) |
| [`adapters/`](adapters/) | EDA framework bindings (`EdaAdapter`, toolchain, no-op default) |

Root files: `platform.yaml`, `toolchain.yaml` (host profiles — not Python modules).

## Typical imports

```python
from domains.eda import EDAAgent, AgentService, EDAAgentConfig
from domains.eda.adapters import tool_observation
from domains.eda.fleet import select_agents, get_config, to_fleet_workflow
from domains.eda.schemas import TaskBrief, WorkflowProposal
```

See [`runtime/README`](runtime/) (via module docstrings), [`schemas/README.md`](schemas/README.md), and [`adapters/README.md`](adapters/README.md) for detail.
