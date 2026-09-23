from __future__ import annotations

"""Module ``agent_sdk/src/skills/registry.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Skill/tool registration and base decorators for agent capabilities.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``registry.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import asyncio
import importlib
import inspect
import time
from collections.abc import Callable
from typing import Any, Optional

from ..contracts import ExecutionTrace, SkillCall
from .declarations import SkillDeclaration


class SkillRegistry:
    """``SkillRegistry``"""
    def __init__(self):
        """``SkillRegistry``"""
        self._skills: dict[str, tuple[SkillDeclaration, Callable[..., Any]]] = {}
        self._capability_params: dict[str, dict[str, Any]] = {}
        self._on_call: Optional[Callable[[SkillCall], None]] = None

    @property
    def declarations(self) -> list[SkillDeclaration]:
        """Registered skill declarations in registration order."""
        return [decl for decl, _ in self._skills.values()]

    def set_call_hook(self, hook: Callable[[SkillCall], None]) -> None:
        """``specs``"""
        self._on_call = hook

    def register(self, declaration: SkillDeclaration, func: Callable[..., Any]) -> None:
        """Bind one skill declaration to its callable implementation."""
        self._skills[declaration.id] = (declaration, func)

    def accepts_argument(self, skill_id: str, name: str) -> bool:
        """Return whether a registered callable accepts ``name``.

        Domain lifecycle adapters use this to pass optional structured context
        without guessing that every skill accepts a ``params`` argument.
        """
        if skill_id not in self._skills:
            raise KeyError(f"Unknown skill: {skill_id}")
        _, func = self._skills[skill_id]
        signature = inspect.signature(func)
        return name in signature.parameters or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )

    def set_capability_params(self, params: dict[str, dict[str, Any]]) -> None:
        """Merge capability-level skill_params: {skill_id: {arg: value}}."""
        self._capability_params = params

    def load_from_config(self, declarations: list[SkillDeclaration], package_root: str | None = None) -> None:
        """Import modules and register each declaration from agent config."""
        for declaration in declarations:
            module_name = declaration.module
            if package_root and not module_name.startswith(package_root):
                module_name = f"{package_root}.{module_name}"
            module = importlib.import_module(module_name)
            func = getattr(module, declaration.callable)
            self.register(declaration, func)

    async def call(self, skill_id: str, **kwargs: Any) -> SkillCall:
        """``call``"""
        if skill_id not in self._skills:
            # Raise ``KeyError`` to signal this failure mode to callers.
            raise KeyError(f"Unknown skill: {skill_id}")

        declaration, func = self._skills[skill_id]
        cap_defaults = self._capability_params.get(skill_id, {})
        merged_args = {**declaration.args_defaults, **cap_defaults, **kwargs}

        start = time.perf_counter()
        timeout = declaration.timeout_secs

        # Try the fallible work below.
        try:
            # Only when (timeout).
            if timeout:
                # Local ``result`` ← await asyncio.wait_for(.
                result = await asyncio.wait_for(
                    self._invoke(func, merged_args),
                    # Local ``timeout`` ← timeout,.
                    timeout=timeout,
                )
            else:
                # Local ``result`` ← await self._invoke(func, merged_args).
                result = await self._invoke(func, merged_args)
        # On except asyncio.TimeoutError: recover or re-raise as appropriate.
        except asyncio.TimeoutError:
            # Local ``duration_ms`` ← int((time.perf_counter() - start) * 1000).
            duration_ms = int((time.perf_counter() - start) * 1000)
            # Local ``sc`` ← SkillCall(.
            sc = SkillCall(
                # Local ``skill_id`` ← skill_id,.
                skill_id=skill_id,
                # Local ``args`` ← merged_args,.
                args=merged_args,
                # Local ``result`` ← {"error": "timeout"},.
                result={"error": "timeout"},
                # Local ``duration_ms`` ← duration_ms,.
                duration_ms=duration_ms,
            )
            # Only when (self._on_call).
            if self._on_call:
                # Call ``self._on_call``.
                self._on_call(sc)
            raise

        # Local ``duration_ms`` ← int((time.perf_counter() - start) * 1000).
        duration_ms = int((time.perf_counter() - start) * 1000)
        # Local ``sc`` ← SkillCall(.
        sc = SkillCall(
            # Local ``skill_id`` ← skill_id,.
            skill_id=skill_id,
            # Local ``args`` ← merged_args,.
            args=merged_args,
            # Local ``result`` ← result,.
            result=result,
            # Local ``duration_ms`` ← duration_ms,.
            duration_ms=duration_ms,
        )
        # Only when (self._on_call).
        if self._on_call:
            # Call ``self._on_call``.
            self._on_call(sc)
        # Hand ``sc`` back to the caller.
        return sc

    @staticmethod
    async def _invoke(func: Callable[..., Any], args: dict[str, Any]) -> Any:
        """``_invoke``"""
        result = func(**args)
        # Only when (inspect.isawaitable(result)).
        if inspect.isawaitable(result):
            # Local ``result`` ← await result.
            result = await result
        # Hand ``result`` back to the caller.
        return result

    def skill_call_trace(self, sc: SkillCall) -> ExecutionTrace:
        """``skill_call_trace``"""
        return ExecutionTrace(
            # Local ``trace_type`` ← "skill_call",.
            trace_type="skill_call",
            # Local ``payload`` ← sc.model_dump(mode="json"),.
            payload=sc.model_dump(mode="json"),
        )

    def iter_registered(self):
        """``iter_registered``"""
        for declaration, func in self._skills.values():
            yield declaration, func
