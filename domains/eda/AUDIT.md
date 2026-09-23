# Domain vs generic building blocks

## Configuration hierarchy

| Layer | Type | Location |
|-------|------|----------|
| Runtime HTTP/skills | `AgentConfig` | `packages/agent_sdk/src/models.py` |
| Generic declarations | `ParameterDeclaration`, `SkillDeclaration`, `RoleDeclaration`, `OperationDeclaration` | `packages/agent_sdk/src/models.py` |
| EDA specialization | `EDAAgentConfig(AgentConfig)`, `EDAAgentSkill(SkillDeclaration)` | `domains/eda/config/models.py` |

One loader: `load_eda_agent_config()` → single `EDAAgentConfig` for both `AgentService` and `EDAAgent`.

## Generic (`packages/`)

| Building block | Purpose |
|-----|-----|
| `ParameterDeclaration` | Named input accepted by any skill |
| `SkillDeclaration` | Executable callable, parameters, timeout, and default arguments |
| `RoleDeclaration` | Domain-defined role represented without imposed categories |
| `OperationDeclaration` | Domain-defined operation represented without imposed semantics |

## Stays EDA-only (`domains/eda/`)

| Area | Why |
|------|-----|
| `schemas/enums.py` | `RecordType`, `TaskOutcome`, chip memory trust |
| `schemas/messages.py`, `task.py`, `memory.py`, `artifact.py` | Workflow proposals, task briefs, memory envelopes |
| `context.py` | `INCLUDE_TYPES` → `RecordType` mapping |
| `memory/service.py`, placements | Engineering memory policy |
| `config/models.py` | EDA roles, EDA operations, signoff authority, and EDA delegation |
| `runtime/planning.py` | `WorkflowProposal` from an EDA lead delegation plan |
| `adapters/toolchain.py` | OSS EDA host adapter |
| `fleet/registry.py` | fleet registry validation over `agents/eda/**` |
| `fleet/compose.py` | Fleet YAML → compose services |
| `fleet/workflow.py` | Lead proposal → fleet SDK planner |
| `platform.yaml`, `toolchain.yaml` | EDA host + ORFS profile |

## Agent tree

Implementations live under **`agents/eda/`** (mirrors **`domains/eda/`**).
