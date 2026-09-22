# Agent SDK — skills (`packages/agent_sdk/src/skills/`)

This directory implements the **skill registration and invocation layer** for the Agent SDK. In fleet terminology, a **skill** is a named, callable operation an agent exposes to planners and runtimes (for example `write_scan_configuration` on a DFT agent). The HTTP task server does not hard-code those names; it loads them from `config.yaml` capabilities, binds them to Python callables, and executes them through `SkillRegistry.call`.

Silicon / EDA agents in this repo usually define skills in a sibling `tools.py` using the `@tool` decorator re-exported from `packages.agent_sdk`. The registry here is what turns YAML `callable` names into live functions at process startup.

---

## Why this directory exists

When the fleet executor (or an operator) POSTs to an agent’s `/tasks/execute`, something must:

1. Resolve which Python function implements each configured skill.
2. Merge default arguments from config with runtime kwargs.
3. Enforce per-skill timeouts and record duration for traces / telemetry.
4. Support optional hooks so the server can journal each skill call.

That logic lives here—not in individual agent directories—so every agent container shares one tested implementation.

---

## Placement in the agent process

```text
config.yaml (capabilities / skills → SkillSpec list)
        │
        ▼
AgentServer.__init__  ──►  SkillRegistry.load_from_config(...)
        │                      imports tools.py callables
        ▼
AgentRuntime (tool_loop / direct_function / codegen)
        │
        ▼
SkillRegistry.call(skill_id, **kwargs)  ──►  SkillCall + result dict
```

For **EDA domain agents**, `domains.eda.server.BoundAgentRuntime` usually bypasses the generic “run one skill” path and forwards the whole task to `EdaAgent.handle`, which internally dispatches to the same `tools.py` callables. The registry is still constructed on `AgentServer` because memory skills, telemetry hooks, and SDK runtimes expect it to exist.

---

## Files in this directory

| File | Role |
|------|------|
| `base.py` | Defines the `@tool` decorator. Marks functions with `_agent_tool`, description, and optional constraints metadata for discovery and LLM tool schemas. |
| `registry.py` | `SkillRegistry`: register specs, load modules from config, merge defaults, async `call()` with timeout, `SkillCall` tracing, capability param injection. |
| `__init__.py` | Package marker only; import from `base` / `registry` or use `from packages.agent_sdk import tool`. |
| `README.md` | This document. |

There are no subdirectories under `skills/`; all behavior is in the two modules above.

---

## `@tool` decorator (`base.py`)

Agents annotate skill functions like this:

```python
from packages.agent_sdk import tool

@tool(description="One-line planner-facing summary.")
def my_skill(candidate_ref: str = "", params: dict | None = None) -> dict:
    ...
```

The decorator:

- Sets `func._agent_tool = True` so loaders can distinguish tools from helpers.
- Stores `func._agent_tool_description` (explicit string or first line of docstring).
- Stores `func._agent_tool_constraints` (optional dict for future policy hooks).

It does **not** register the function globally. Registration happens when `SkillRegistry.load_from_config` imports the module named in each `SkillSpec` and calls `register(spec, func)`.

---

## `SkillRegistry` (`registry.py`)

### Registration

- `register(spec: SkillSpec, func)` — maps `spec.id` to `(spec, callable)`.
- `load_from_config(specs, package_root=None)` — for each spec, `importlib.import_module(spec.module)` (optionally prefixed with `package_root`), then `getattr(module, spec.callable)`.

EDA agents typically load `tools` as a dynamically injected module (`AgentServer` loads `tools.py` from the agent directory) while YAML lists `callable: write_scan_configuration` matching the function name.

### Invocation

- `call(skill_id, **kwargs)` builds `merged_args = {**spec.args_defaults, **capability_params[skill_id], **kwargs}`.
- Runs sync or async functions via `_invoke`; applies `asyncio.wait_for` when `spec.timeout_secs` is set.
- Returns a `SkillCall` model (skill id, args, result, `duration_ms`). On timeout, returns a structured error payload and re-raises after optional hook.
- `set_call_hook(fn)` — server can attach telemetry or journaling on every call.
- `accepts_argument(skill_id, name)` — used by domain adapters to pass optional `params` only when the signature allows it.
- `skill_call_trace(sc)` — wraps a call as an `ExecutionTrace` for task result payloads.

### Introspection

- `specs` — list of registered `SkillSpec` objects.
- `iter_registered()` — yields `(spec, func)` pairs for schema export or debugging.

---

## Relationship to `config.yaml`

Each agent’s manifest lists skills under `capabilities` / `skills` (exact key depends on schema version). Each entry becomes a `SkillSpec` with:

- **id** — stable skill id used in `call()`.
- **callable** — Python function name in `tools.py`.
- **module** — import path (often `tools` once the server injected the file).
- **args_defaults**, **timeout_secs**, descriptions — merged at call time.

The validator in `src/schema/` parses YAML into `AgentConfig`; `AgentServer._load_skills()` passes the resulting specs into `load_from_config`.

---

## Relationship to EDA `tools.py`

Under `agent_fleet/agents/**/tools.py`, almost every function is a thin wrapper:

- Build a payload dict (`candidate_ref`, `baseline_ref`, `hypothesis`, …).
- Return `domains.eda.eda.tool_observation(name, payload, agent_id=...)`.

Those functions are still **skills** from the SDK’s point of view: they are registered, timed, and traced the same way as a fully bound OpenROAD adapter would be. The difference is runtime behavior (stub `not_run` vs real EDA execution), not the registry mechanics.

---

## Public imports

| Import | From |
|--------|------|
| `tool` | `packages.agent_sdk` (re-export from `skills.base`) |
| `SkillRegistry` | `packages.agent_sdk.src.skills.registry` (used by `AgentServer`, tests, domain server) |

---

## Related documentation

- [`../server/README.md`](../server/README.md) — `AgentServer` constructs the registry and loads `tools.py`.
- [`../runtime/README.md`](../runtime/README.md) — runtimes that invoke `skills.call` during tool loops.
- [`../schema/README.md`](../schema/README.md) — YAML → `SkillSpec` validation.
- [`../../../../domains/eda/server.py`](../../../../domains/eda/server.py) — `BoundAgentRuntime` and `AgentService` for EDA agents.
- [`../../../../agents/README.md`](../../../../agents/README.md) — per-agent `tools.py` pattern.

---

## How to read this code as a newcomer

1. Read `base.py` (small) to see how agents mark callables.
2. Read `registry.py` `call()` and `load_from_config()` — that is the full runtime contract.
3. Open any agent’s `tools.py` and `server.py`, then `AgentServer._load_skills` in `../server/agent_server.py` to see injection + registration end to end.
4. Trace one task through `EdaAgent.handle` if you care about domain journaling rather than raw SDK tool loops.

---

## Operational notes

- **Timeouts** — configured per skill in YAML; exceeded calls produce `{"error": "timeout"}` inside the `SkillCall` before the timeout propagates.
- **Concurrency** — `AgentServer` uses a semaphore on tasks; individual skills should remain idempotent on a `candidate_ref` where possible.
- **Testing** — unit tests can construct a bare `SkillRegistry`, register mocks, and await `call()` without starting HTTP.

This package intentionally stays free of FastAPI and gRPC imports so it can be imported from runtimes and tests with minimal side effects.
