# adapters (framework bindings)

EDA / verification tool bindings live at `domains/eda/adapters/`. Import **`domains.eda.adapters`** — there is no nested `eda/eda/` directory.

Agent **`tools.py`** modules call named operations through an **`EdaAdapter`** instead of shelling out to OpenROAD, Yosys, OpenSTA, licensed signoff tools, or RTL simulators. That keeps scheduling, licensing, sandboxing, and observability in one place once real bindings exist.

## Why adapters exist

| Without adapters | With adapters |
|------------------|---------------|
| Each agent embeds CLI strings and parses logs | One **`invoke(operation, params)`** contract |
| Hard to swap no-op vs real tools in tests | **`bind_eda_adapter`** at process startup |
| Observations inconsistent across agents | Uniform **`ToolObservation`** for memory and gates |

Until production bindings ship, the default **`NoOpEdaAdapter`** keeps the fleet runnable: tools return structured **`not_run`** observations rather than failing import or exec.

## Global registry (`__init__.py`)

Process-global singleton pattern (test helpers included):

| Function | Behavior |
|----------|----------|
| **`bind_eda_adapter(adapter)`** | Install implementation for this process |
| **`get_eda_adapter()`** | Return current binding (defaults to no-op) |
| **`reset_eda_adapter()`** | Restore no-op (tests) |
| **`tool_observation(...)`** | Helper to build **`ToolObservation`** from tool code |

Call **`bind_eda_adapter`** before treating tool metrics as engineering evidence or promotion input.

## EdaAdapter protocol (`base.py`)

Structural protocol — any object with:

- **`framework: str`** — short name stamped on observations (e.g. `openroad`, `yosys`)
- **`invoke(operation, params, *, agent_id="") -> ToolObservation`**

**`operation`** is tool-specific (`place_design`, `synth`, `sta_report`, …). **`params`** is the conventional dict agents pass from task context and skill arguments.

Implementations may submit cluster jobs, write intermediate files, or (for no-op) only construct the model.

## NoOpEdaAdapter (`noop.py`)

Default binding when nothing else is registered:

- Returns observations with **`status=not_run`**
- Must **not** be treated as signoff-grade evidence
- **`EDAAgent`** worker path maps this to **`PARTIALLY_COMPLETED`** / **`FRAMEWORK_UNBOUND`** style outcomes

Leads and validators still run through the same adapter for declared operations; validator gates remain **provisional** until a real framework grades candidates.

## Named factories (`frameworks.py`)

Unbound placeholders for future work:

| Factory | Intended framework |
|---------|-------------------|
| **`openroad_adapter`** | OpenROAD P&R |
| **`yosys_adapter`** | Yosys synthesis |
| **`opensta_adapter`** | OpenSTA timing |
| **`rtl_eval_adapter`** | RTL simulation / eval |

Each factory currently raises **`NotImplementedError`** until wired to containers, licenses, or remote executors. Production startup should **`bind_eda_adapter`** with a composite or per-tool implementation rather than calling these factories directly from agents.

## Typical tool module pattern

```python
from domains.eda.adapters import get_eda_adapter

def run_place(params: dict) -> ToolObservation:
    return get_eda_adapter().invoke("place_design", params, agent_id=params.get("agent_id", ""))
```

Skills register these callables via the agent SDK **`SkillRegistry`**; **`EDAAgent._invoke_declared_tools`** enforces **`ToolAction`** permissions before invocation.

## Testing strategy

1. **`reset_eda_adapter()`** in test teardown.
2. Install a fake adapter that records **`operation`** / **`params`** and returns deterministic **`ToolObservation`**.
3. Keep integration tests that need real tools behind separate markers and infrastructure.

## Related

| Path | Topic |
|------|--------|
| [`../agent.py`](../agent.py) | **`execute_tools`**, **`_invoke_declared_tools`** |
| [`../schemas/messages.py`](../schemas/messages.py) | **`ToolObservation`** schema |
| [`../../../agents/backend/`](../../../agents/backend/) | registered agents that declare EDA operations in `config.yaml` |
| [`../README.md`](../README.md) | Full **`EDAAgent`** lifecycle |
