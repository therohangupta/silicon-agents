# domains

First-party **domain packages** specialize the generic agent SDK (`packages/agent_sdk`) and memory kit (`packages/memory`) for a concrete engineering discipline. Domains do not replace those kits; they add vocabulary, policy, and facades so fleet services and HTTP agents share one contract.

Today the tree contains a single production domain:

| Package | Purpose |
|---------|---------|
| [`eda/`](eda/README.md) | Chip-design (EDA) agents: task lifecycle, engineering memory, schemas, catalog, fleet selection, framework adapters |

Additional domains (for example physical design-only policy or a separate verification fleet) would sit as sibling directories under `domains/` with the same pattern: a top-level README, a public `__init__.py` that documents intent, and subpackages for schemas, memory, and adapters.

## Why a domains layer exists

The fleet HTTP stack (`AgentServer`, gateway, telemetry) speaks generic **AgentTaskRequest** / **AgentTaskResult** envelopes. Silicon agents need richer semantics:

- Design scope (project, revision, subsystem, block, stage)
- Role-based tool permissions (lead vs worker vs validator)
- Versioned memory records with validation state and evidence
- Context assembly driven by per-agent `config.yaml` policy

Putting that logic in every agent under `agents/` would duplicate invariants. The EDA domain centralizes them so each concrete agent is mostly `eda_config` + `tools.py` + thin subclass glue.

## Import conventions

- Import concrete types from **`domains.eda`** or deeper submodules (`domains.eda.schemas`, `domains.eda.memory`, …).
- Do **not** treat **`domains`** itself as a barrel export; `domains/__init__.py` is a package marker only.
- Run Python from **repo root** (or install the package editable) so `domains.*` resolves consistently with scripts and tests.

## Relationship to other trees

```text
packages/agent_sdk   → HTTP lifecycle, skills registry, task transport models
packages/memory      → Generic stores, context assembler, write-policy kit
domains/eda          → EDA TaskBrief, MemoryRecord, EDAAgent, EngineeringMemory
agents/<path>/       → One catalog agent per directory (config.yaml + agent.py + tools.py)
fleets/*.yaml        → Which agent directories startup.sh / fleet_select render into Compose
```

Fleet YAML and platform config (`config/platform.yaml`) are not under `domains/`, but **`domains.eda.fleet`** reads them when rendering agent services.

## Layout

```text
domains/
├── __init__.py
├── README.md
└── eda/                 # Chip-design domain (see eda/README.md)
    ├── config/          # EDAAgentConfig + YAML loader
    ├── schemas/         # Pydantic contracts
    ├── memory/          # EngineeringMemory + stores
    ├── runtime/         # EDAAgent, AgentService, ContextService, planning
    ├── fleet/           # Catalog, compose selection, workflow intake
    ├── adapters/        # EDA framework bindings (was eda/eda/)
    ├── platform.yaml
    └── toolchain.yaml
```

## Adding a new domain (sketch)

1. Create `domains/<name>/` with `schemas/`, optional `memory/` overrides, and an agent base class if the lifecycle differs from EDA.
2. Document public imports in `<name>/__init__.py` and a root `<name>/README.md`.
3. Wire catalog validation and fleet selection only if that domain owns its own agent tree; otherwise extend EDA.

For EDA-specific depth—**EDAAgent** lifecycle, **EngineeringMemory**, and **schemas**—start at [`eda/README.md`](eda/README.md) and the nested READMEs under `eda/schemas/`, `eda/memory/`, and `eda/eda/`.

## Related documentation

| Document | Topic |
|----------|--------|
| [`../agents/README.md`](../agents/README.md) | Per-agent directory layout |
| [`../fleets/README.md`](../fleets/README.md) | Fleet YAML format |
| [`../docs/DESIGN.md`](../docs/DESIGN.md) | Control-plane architecture |
| [`../packages/agent_sdk/src/skills/README.md`](../packages/agent_sdk/src/skills/README.md) | Skill registry and tools loading |

## Testing and validation touchpoints

Domain behavior is covered primarily in **`tests/test_silicon.py`** and memory/context modules. Catalog shape is enforced by **`scripts/check_agents.py`** and **`tests/contract/`**. When you change publish policy or **`ROLE_ACTIONS`**, run both unit and contract suites — gateway embodiment scans do not re-validate memory rules.
