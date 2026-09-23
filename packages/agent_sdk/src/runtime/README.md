# Agent SDK — execution runtimes (`packages/agent_sdk/src/runtime/`)

Runtimes implement **`AgentRuntime.execute(request) → AgentTaskResult`**. [`AgentServer`](../server/agent_server.py) picks one implementation from `AgentConfig.execution.mode` and delegates each HTTP task to it.

This layer sits between the transport (`AgentTaskRequest`) and agent logic (`tools.py`, LLM, or generated code).

---

## Purpose in the fleet

Different agents need different execution models:

| Need | Runtime mode |
|------|----------------|
| Deterministic tools, `domain handler`-style handlers | `direct_function` |
| LLM chooses among registered skills | `tool_loop` (LangChain inside) |
| Model writes Python executed in-container | `codegen` |
| Reserved / same as direct today | `custom` |

Runtimes share **`SkillRegistry`** and **`MemoryManager`** from [`../skills/`](../skills/README.md) and [`../memory/`](../memory/README.md).

---

## Placement in architecture

```text
AgentServer._make_runtime()
        │
        ├── execution.mode == codegen
        │         └── CodegenRuntime ──► CodeExecutionRunner
        ├── execution.mode == tool_loop
        │         └── ToolLoopRuntime ──► LangChainRuntime
        └── execution.mode in (direct_function, custom)
                  └── DirectFunctionRuntime ──► tools.execute(request)
```

LangChain stack also includes [`langchain_backend.py`](langchain_backend.py) helpers used by [`langchain_runtime.py`](langchain_runtime.py).

---

## Complete file table

| Module | Class / symbol | Role |
|--------|----------------|------|
| [`base.py`](base.py) | `AgentRuntime` | ABC with `skills`, `memory`, `execute()` |
| [`direct_function_runtime.py`](direct_function_runtime.py) | `DirectFunctionRuntime` | Calls `execute` in loaded tools module |
| [`tool_loop_runtime.py`](tool_loop_runtime.py) | `ToolLoopRuntime` | Wraps LangChain; normalizes traces |
| [`langchain_runtime.py`](langchain_runtime.py) | `LangChainRuntime` | LLM + tools loop, providers, prompts |
| [`langchain_backend.py`](langchain_backend.py) | Helpers | Backend-specific LangChain wiring |
| [`codegen_runtime.py`](codegen_runtime.py) | `CodegenRuntime` | LLM/code path + artifact handling |
| [`codegen_runner.py`](codegen_runner.py) | `CodeExecutionRunner` | Subprocess/isolated execution of generated code |
| [`__init__.py`](__init__.py) | Package marker | |
| [`README.md`](README.md) | This document | |

---

## DirectFunctionRuntime

- Loads agent `tools` module (unique name when started via `AgentServer`).
- Requires **`execute(request)`** on that module (sync or async).
- Accepts return types: `AgentTaskResult`, `dict` (kwargs for result model), or any value (wrapped as success + `artifacts.result`).

**Typical default** — Most backend agents use this mode indirectly: domain server forwards to `domain handler.handle`, but standalone SDK agents use `tools.execute` the same way.

---

## ToolLoopRuntime and LangChainRuntime

- `ToolLoopRuntime` delegates to `LangChainRuntime` then attaches `ExecutionTrace` entries for skill calls and memory ops from the result.
- `LangChainRuntime` builds chat model from `BackendConfig` (`provider`, `model`, `temperature`, `system_prompt`).
- Supported providers (see `_PROVIDER_CLASSES`): OpenAI, Anthropic, Ollama, Azure, Google — each needs optional pip package.
- System prompt may be inline or path ending in `.prompt`, `.txt`, `.md`.
- Binds registry tools as LangChain tools; records `SkillCall`, `MemoryOp` on result.

Use for exploratory agents; production tools often stay direct for determinism.

---

## CodegenRuntime and CodeExecutionRunner

- Uses `BackendConfig` for code generation when request does not include prebuilt code.
- `ExecutionConfig`: `work_dir`, `runner`, template prefix/suffix files, import paths from agent directory.
- `CodeExecutionRunner` executes Python with timeout from `ReliabilityConfig.task_timeout_secs`.
- Traces include `code_execution` payloads; may publish workspace artifacts via skills inside runner.

Relevant for agents that emit scripts to orchestrate external toolchains or batch checks.

---

## Data and control flow

1. Server sets capability params on registry from request.
2. Runtime `execute(request)` runs domain work.
3. Result includes success, message, artifacts, optional `artifact_refs`, traces.
4. Server emits telemetry from traces and task lifecycle events.

**Inputs** — Runtimes read `request.description`, `request.inputs`, `request.context` (plan summary, artifacts). Workspace helpers typically live in `tools.execute` or LangChain tool wrappers, not in base runtime.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../server/agent_server.py`](../server/agent_server.py) | `_make_runtime()` |
| [`../models.py`](../models.py) | `ExecutionConfig`, `BackendConfig`, traces |
| [`../skills/README.md`](../skills/README.md) | Tool registration |
| [`../../README.md`](../../README.md) | Package overview |

---

## Newcomer reading order

1. [`base.py`](base.py)
2. [`direct_function_runtime.py`](direct_function_runtime.py) — match most Domain agents
3. [`../server/README.md`](../server/README.md) — mode selection
4. [`langchain_runtime.py`](langchain_runtime.py) — only if using LLM mode
5. [`codegen_runtime.py`](codegen_runtime.py) + [`codegen_runner.py`](codegen_runner.py) — codegen path

---

## Operational notes

- **Unsupported mode** — `_make_runtime` raises `ValueError`; fix YAML before deploy.
- **Missing execute** — Direct runtime returns `success=False`, `error=missing_execute`.
- **Provider imports** — LangChain modes fail fast with install hints if provider package missing.
- **Timeouts** — Codegen runner and server task stream use `reliability.task_timeout_secs` / `TASK_DURATION` env.
- **Concurrency** — Runtime does not own semaphore; server limits parallel tasks via `execution.concurrency.max_tasks`.

Extending the fleet with a new mode requires a new `AgentRuntime` subclass and a branch in `AgentServer._make_runtime`.
