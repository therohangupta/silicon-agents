# Agent SDK — config schema (`packages/agent_sdk/src/schema/`)

Validates and normalizes each agent’s **`config.yaml`** into a typed **`AgentConfig`** ([`../models.py`](../models.py)). Used at process startup by [`AgentServer.from_yaml`](../server/agent_server.py) and domain [`AgentService`](../../../domains/) loaders loaders.

---

## Purpose in the fleet

Every agent container shares one configuration contract:

- Metadata, connection endpoints, execution mode, LLM backend
- Capabilities and skill bindings
- Memory stores, reliability, observability, deployment hints

The schema layer ensures **consistent parsing**, **environment substitution**, and **backward compatibility** with older YAML shapes (`runtime`, `taskServer`, string capabilities, global memory backend).

---

## Placement in architecture

```text
config.yaml on disk
        │
        ▼
yaml.safe_load
        │
        ▼
_expand_env()           ← ${VAR}, ${VAR:-default}, platform host_settings
        │
        ▼
_migrate_legacy_config()
        │
        ▼
AgentConfig(**data)     ← Pydantic validation (models.py)
        │
        ▼
AgentServer / AgentService
```

Invalid fields surface as Pydantic validation errors at startup (fail fast before binding ports).

---

## Files in this directory

| File | Role |
|------|------|
| [`validator.py`](validator.py) | `AgentConfigValidator`, env expansion, legacy migration |
| [`yaml_validator.py`](yaml_validator.py) | `YAMLValidator` — returns JSON dict for tooling/CLI |
| [`__init__.py`](__init__.py) | Package marker |
| [`README.md`](README.md) | This document |

There is no separate JSON Schema file on disk; **`AgentConfig`** Pydantic models are the source of truth.

---

## AgentConfigValidator

**`validate_file(path)`** — Read YAML, expand env, migrate, construct `AgentConfig`.

**`validate_dict(data)`** — Same pipeline for in-memory dicts (tests, generators).

### Environment expansion (`_expand_env`)

- Recurses dicts/lists.
- Strings: `os.path.expandvars`, then regex for `${NAME}` and `${NAME:-default}`.
- Falls back to [`packages.platform_config.host_settings`](../../../packages/platform_config/) when env unset.

Use for telemetry URLs, DSNs, and host overrides without templating entire YAML files per environment.

### Legacy migration (`_migrate_legacy_config`)

| Legacy shape | Migration behavior |
|--------------|-------------------|
| `runtime` block | Maps to `connection` + optional `execution.concurrency` |
| `backend.type: python_function` | Sets `backend.type: none`, `execution.mode: direct_function` |
| `memory.backend` + `stores` | Copies global backend type to per-store `persistence` |
| `observability.telemetry_streams` | Renamed to `observability.telemetry.streams` |
| `metadata.tags` | Becomes `metadata.labels` |
| `taskServer` | Becomes `connection`; fills metadata name |
| String `capabilities` | Converts to `{id, description}` objects |
| Missing apiVersion/kind | Sets `agentfleet/v1` / `Agent` |

Agents checked into the repo should use the modern shape; migration protects older branches.

---

## YAMLValidator

Thin wrapper: `validate_file(path) → dict` via `AgentConfig.model_dump(mode="json")`.

Use when a script needs JSON-serializable config without constructing server objects.

---

## Data and control flow

1. Operator edits agent `config.yaml` (port, skills, capabilities).
2. Container entrypoint calls `AgentServer.from_yaml("/app/config.yaml")`.
3. Validator produces `AgentConfig` bound to server, memory, telemetry, runtime.
4. Connection endpoints drive FastAPI routes (`health`, `execute`, optional `memory`).

**Skills section** — Each `SkillSpec` (`id`, `module`, `callable`) must resolve at load time or server startup raises `ImportError`.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../models.py`](../models.py) | Full config model definitions |
| [`../server/README.md`](../server/README.md) | Consumer of validated config |
| [`../../../config/platform.yaml`](../../../config/platform.yaml) | Fleet defaults referenced by models |
| [`../../../agents/backend/*/config.yaml`](../../../agents/backend/) | Examples |

---

## Newcomer reading order

1. Skim `AgentConfig` tree in [`../models.py`](../models.py)
2. Read [`validator.py`](validator.py) migration block comments
3. Open one real agent YAML (e.g. placement lead)
4. [`../server/README.md`](../server/README.md) — how config fields map to behavior

---

## Operational notes

- **Secrets** — Prefer `${DATABASE_URL}` style expansion; never commit live secrets in YAML.
- **Extra keys** — `AgentConfig` allows `extra` on selected nested models; unknown top-level keys may fail validation — keep YAML aligned with models.
- **CI** — Fleet can validate all agent YAMLs by calling `validate_file` in a lint job.
- **Breaking changes** — Add migration steps in `_migrate_legacy_config` rather than breaking existing agents silently.

No subdirectories under `schema/`; all logic is in the two validator modules.
