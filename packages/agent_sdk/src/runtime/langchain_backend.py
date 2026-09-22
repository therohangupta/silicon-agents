from __future__ import annotations

"""Module ``agent_sdk/src/runtime/langchain_backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``langchain_backend.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
from typing import Any

from ..models import AgentTaskRequest, BackendConfig
from ..skills.registry import SkillRegistry


async def generate_task_code(
    backend: BackendConfig,
    skills: SkillRegistry,
    request: AgentTaskRequest,
) -> str:
    """Use LangChain LLM to generate a Python _main() for the task."""
    from .langchain_runtime import _import_llm_class, _build_system_message, _resolve_system_prompt

    # Local ``llm_cls`` ← _import_llm_class(backend.provider or "openai").
    llm_cls = _import_llm_class(backend.provider or "openai")
    # Local ``llm`` ← llm_cls(.
    llm = llm_cls(
        # Local ``model`` ← backend.model or "gpt-4o-mini",.
        model=backend.model or "gpt-4o-mini",
        # Local ``temperature`` ← backend.temperature,.
        temperature=backend.temperature,
        **(backend.config or {}),
    )

    # Local ``skill_docs`` ← "\n".join(.
    skill_docs = "\n".join(
        f"- {s.id}: {s.description}" for s in skills.specs
    )
    # Local ``prompt`` ← _build_system_message(.
    prompt = _build_system_message(
        _resolve_system_prompt(backend.system_prompt),
        request,
    )
    # Local ``human`` ← f"""Write Python code with a function `_main()` that completes th….
    human = f"""Write Python code with a function `_main()` that completes this task.
Use `_call_skill(skill_id, **kwargs)` to invoke skills.

Available skills:
{skill_docs}

Task: {request.description}

Return JSON on the last line via print(json.dumps(...)) with keys:
success, message, artifacts, replan (optional), error (optional).
"""

    from langchain_core.messages import HumanMessage, SystemMessage

    # Local ``messages`` ← [].
    messages = []
    # Only when (prompt).
    if prompt:
        # Call ``messages.append``.
        messages.append(SystemMessage(content=prompt))
    # Call ``messages.append``.
    messages.append(HumanMessage(content=human))

    # Local ``response`` ← await llm.ainvoke(messages).
    response = await llm.ainvoke(messages)
    # Local ``text`` ← response.content if hasattr(response, "content") else str(respons….
    text = response.content if hasattr(response, "content") else str(response)

    # Only when ("```python" in text).
    if "```python" in text:
        # Local ``text`` ← text.split("```python", 1)[1].split("```", 1)[0].
        text = text.split("```python", 1)[1].split("```", 1)[0]
    elif "```" in text:
        # Local ``text`` ← text.split("```", 1)[1].split("```", 1)[0].
        text = text.split("```", 1)[1].split("```", 1)[0]

    # Hand ``text.strip()`` back to the caller.
    return text.strip()
