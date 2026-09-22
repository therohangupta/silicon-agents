from __future__ import annotations

"""Module ``agent_sdk/src/runtime/codegen_runner.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``codegen_runner.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import asyncio
import os
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Optional

from ..models import CodeExecution, ExecutionTrace, SkillCall
from ..skills.registry import SkillRegistry


# Local ``DEFAULT_PREFIX`` ← '''"""Agent-generated task runner (auto prefix).""".
DEFAULT_PREFIX = '''"""Agent-generated task runner (auto prefix)."""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

# Local ``_SKILLS`` ← {}.
_SKILLS = {}
# Local ``_RESULTS`` ← [].
_RESULTS = []
# Local ``_ARTIFACT_REFS`` ← [].
_ARTIFACT_REFS = []
# Local ``_WORKSPACE_ROOT`` ← os.environ.get("_AGENT_WORKSPACE_ROOT", "").
_WORKSPACE_ROOT = os.environ.get("_AGENT_WORKSPACE_ROOT", "")
# Local ``_PLAN_ID`` ← os.environ.get("_AGENT_PLAN_ID", "0").
_PLAN_ID = os.environ.get("_AGENT_PLAN_ID", "0")
# Local ``_TASK_ID`` ← os.environ.get("_AGENT_TASK_ID", "0").
_TASK_ID = os.environ.get("_AGENT_TASK_ID", "0")
# Local ``_AVAILABLE_ARTIFACTS`` ← json.loads(os.environ.get("_AGENT_AVAILABLE_ARTIFACTS", "[]")).
_AVAILABLE_ARTIFACTS = json.loads(os.environ.get("_AGENT_AVAILABLE_ARTIFACTS", "[]"))

def _register_skill(name, fn):
    _SKILLS[name] = fn

def _jsonable(value):
    # Try the fallible work below.
    try:
        # Call ``json.dumps``.
        json.dumps(value)
        # Hand ``value`` back to the caller.
        return value
    # On except TypeError: recover or re-raise as appropriate.
    except TypeError:
        # Hand ``repr(value)`` back to the caller.
        return repr(value)

def _call_skill(name, **kwargs):
    # Local ``fn`` ← _SKILLS[name].
    fn = _SKILLS[name]
    # Local ``start`` ← time.perf_counter().
    start = time.perf_counter()
    # Local ``result`` ← fn(**kwargs).
    result = fn(**kwargs)
    # Local ``duration_ms`` ← int((time.perf_counter() - start) * 1000).
    duration_ms = int((time.perf_counter() - start) * 1000)
    _RESULTS.append({
        "skill_id": name,
        "args": _jsonable(kwargs),
        "result": _jsonable(result),
        "duration_ms": duration_ms,
    })
    # Hand ``result`` back to the caller.
    return result

def _publish_artifact(name, data, format="json", schema_hint=None, description=""):
    """Write an artifact to the plan workspace. Returns the artifact ref dict."""
    if not _WORKSPACE_ROOT:
        # Hand ``{"error": "no workspace configured"}`` back to the caller.
        return {"error": "no workspace configured"}
    # Local ``dest_dir`` ← Path(_WORKSPACE_ROOT) / _PLAN_ID / _TASK_ID.
    dest_dir = Path(_WORKSPACE_ROOT) / _PLAN_ID / _TASK_ID
    # Call ``dest_dir.mkdir``.
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Local ``dest`` ← dest_dir / name.
    dest = dest_dir / name
    # Only when (isinstance(data, str)).
    if isinstance(data, str):
        # Local ``data`` ← data.encode("utf-8").
        data = data.encode("utf-8")
    # Call ``dest.write_bytes``.
    dest.write_bytes(data)
    # Local ``ref`` ← {.
    ref = {
        "uri": f"workspace://{_PLAN_ID}/{_TASK_ID}/{name}",
        "name": name,
        "format": format,
        "size_bytes": len(data),
        "schema_hint": schema_hint or {},
        "description": description,
        "producer_task_id": _TASK_ID,
        "producer_agent_id": "",
    }
    # Call ``_ARTIFACT_REFS.append``.
    _ARTIFACT_REFS.append(ref)
    # Hand ``ref`` back to the caller.
    return ref

def _load_artifact(name, producer_task_id=""):
    """Load a previously published artifact from the plan workspace."""
    for art in _AVAILABLE_ARTIFACTS:
        # Only when (art.get("name") == name).
        if art.get("name") == name:
            # Only when (producer_task_id and art.get("producer_task_id") != producer_task_id).
            if producer_task_id and art.get("producer_task_id") != producer_task_id:
                continue
            # Local ``ptid`` ← art.get("producer_task_id", "0").
            ptid = art.get("producer_task_id", "0")
            # Local ``path`` ← Path(_WORKSPACE_ROOT) / _PLAN_ID / ptid / name.
            path = Path(_WORKSPACE_ROOT) / _PLAN_ID / ptid / name
            # Only when (path.exists()).
            if path.exists():
                # Hand ``path.read_bytes()`` back to the caller.
                return path.read_bytes()
            # Hand ``None`` back to the caller.
            return None
    # Hand ``None`` back to the caller.
    return None

def _list_available_artifacts():
    """Return list of artifact refs available from prior tasks."""
    return _AVAILABLE_ARTIFACTS

'''

# Local ``DEFAULT_SUFFIX`` ← '''.
DEFAULT_SUFFIX = '''
if __name__ == "__main__":
    # Try the fallible work below.
    try:
        # Local ``result`` ← _main().
        result = _main()
        print(json.dumps({
            "__agent_result__": result,
            "__skill_calls__": _RESULTS,
            "__artifact_refs__": _ARTIFACT_REFS,
        }, default=str))
    # On except Exception as e: recover or re-raise as appropriate.
    except Exception as e:
        import traceback
        print(json.dumps({
            "__agent_result__": {"success": False, "error": str(e), "traceback": traceback.format_exc()},
            "__skill_calls__": _RESULTS,
            "__artifact_refs__": _ARTIFACT_REFS,
        }, default=str))
        # Call ``sys.exit``.
        sys.exit(1)
'''


class CodeExecutionRunner:
    """Write generated Python to a temp file and run in subprocess."""

    def __init__(
        self,
        skills: SkillRegistry,
        work_dir: str = "/tmp/agent_runs",
        timeout_secs: float = 120.0,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        import_paths: Optional[list[str]] = None,
    ):
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self.skills = skills
        # Bind ``work_dir`` from Path(work_dir) for later use on this instance.
        self.work_dir = Path(work_dir)
        # Call ``self.work_dir.mkdir``.
        self.work_dir.mkdir(parents=True, exist_ok=True)
        # Bind ``timeout_secs`` from timeout_secs for later use on this instance.
        self.timeout_secs = timeout_secs
        # Bind ``prefix`` from prefix or DEFAULT_PREFIX for later use on this instance.
        self.prefix = prefix or DEFAULT_PREFIX
        # Bind ``suffix`` from suffix or DEFAULT_SUFFIX for later use on this instance.
        self.suffix = suffix or DEFAULT_SUFFIX
        # Bind ``import_paths`` from [str(Path(p).resolve()) for p in (import_paths or [])] for later use on this instance.
        self.import_paths = [str(Path(p).resolve()) for p in (import_paths or [])]

    def _build_skill_injection(self) -> str:
        """``_build_skill_injection`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        lines = []
        # Loop: for spec, func in self.skills.iter_registered().
        for spec, func in self.skills.iter_registered():
            # Only when (spec.module == "memory").
            if spec.module == "memory":
                continue
            # Local ``mod`` ← spec.module or getattr(func, "__module__", "tools").
            mod = spec.module or getattr(func, "__module__", "tools")
            lines.append(
                f"from {mod} import {spec.callable} as _fn_{spec.id}\n"
                f"_register_skill({spec.id!r}, _fn_{spec.id})\n"
            )
        # Hand ``"".join(lines)`` back to the caller.
        return "".join(lines)

    def wrap_code(self, user_code: str) -> str:
        """``wrap_code`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        injection = self._build_skill_injection()
        # Local ``body`` ← textwrap.dedent(user_code).
        body = textwrap.dedent(user_code)
        if "def _main(" not in body and "def main(" not in body:
            # Local ``body`` ← f"def _main():\n{textwrap.indent(body, '    ')}\n".
            body = f"def _main():\n{textwrap.indent(body, '    ')}\n"
        elif "def _main(" not in body and "def main(" in body:
            # Local ``body`` ← f"{body}\n\n_main = main\n".
            body = f"{body}\n\n_main = main\n"
        # Hand ``f"{self.prefix}\n{injection}\n{body}\n{self.suffix}"`` back to the caller.
        return f"{self.prefix}\n{injection}\n{body}\n{self.suffix}"

    def _subprocess_env(
        self,
        workspace_root: str = "",
        plan_id: str = "0",
        task_id: str = "0",
        available_artifacts: Optional[list[dict]] = None,
    ) -> dict[str, str]:
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        env = os.environ.copy()
        runtime_paths: list[str] = []
        # Loop: for entry in sys.path.
        for entry in sys.path:
            # Only when (entry in ("", ".")).
            if entry in ("", "."):
                # Call ``runtime_paths.append``.
                runtime_paths.append(str(Path.cwd().resolve()))
            elif entry:
                # Call ``runtime_paths.append``.
                runtime_paths.append(str(Path(entry).resolve()))

        # Local ``existing`` ← env.get("PYTHONPATH", "").
        existing = env.get("PYTHONPATH", "")
        # Local ``parts`` ← self.import_paths + runtime_paths + ([existing] if existing else ….
        parts = self.import_paths + runtime_paths + ([existing] if existing else [])
        # Local ``deduped`` ← list(dict.fromkeys(part for part in parts if part)).
        deduped = list(dict.fromkeys(part for part in parts if part))
        # Call ``env["PYTHONPATH"] = os.pathsep.join``.
        env["PYTHONPATH"] = os.pathsep.join(deduped)

        # Only when (workspace_root).
        if workspace_root:
            env["_AGENT_WORKSPACE_ROOT"] = workspace_root
        env["_AGENT_PLAN_ID"] = plan_id
        env["_AGENT_TASK_ID"] = task_id
        import json as _json
        # Call ``env["_AGENT_AVAILABLE_ARTIFACTS"] = _json.dumps``.
        env["_AGENT_AVAILABLE_ARTIFACTS"] = _json.dumps(available_artifacts or [])
        # Hand ``env`` back to the caller.
        return env

    async def run(
        self,
        code: str,
        task_id: str = "run",
        workspace_root: str = "",
        plan_id: str = "0",
        available_artifacts: Optional[list[dict]] = None,
    ) -> tuple[CodeExecution, list[ExecutionTrace], list[dict]]:
        """Run code in subprocess.

        Returns (CodeExecution, traces, artifact_refs published during execution).
        """
        full_code = self.wrap_code(code)
        # Local ``run_dir`` ← self.work_dir / task_id.
        run_dir = self.work_dir / task_id
        # Call ``run_dir.mkdir``.
        run_dir.mkdir(parents=True, exist_ok=True)
        # Local ``script_path`` ← run_dir / "task_run.py".
        script_path = run_dir / "task_run.py"
        # Call ``script_path.write_text``.
        script_path.write_text(full_code)

        # Local ``start`` ← time.perf_counter().
        start = time.perf_counter()
        # Local ``proc`` ← await asyncio.create_subprocess_exec(.
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            # Local ``stdout`` ← asyncio.subprocess.PIPE,.
            stdout=asyncio.subprocess.PIPE,
            # Local ``stderr`` ← asyncio.subprocess.PIPE,.
            stderr=asyncio.subprocess.PIPE,
            # Local ``cwd`` ← str(run_dir),.
            cwd=str(run_dir),
            # Local ``env`` ← self._subprocess_env(.
            env=self._subprocess_env(
                # Local ``workspace_root`` ← workspace_root,.
                workspace_root=workspace_root,
                # Local ``plan_id`` ← plan_id,.
                plan_id=plan_id,
                # Local ``task_id`` ← task_id,.
                task_id=task_id,
                # Local ``available_artifacts`` ← available_artifacts,.
                available_artifacts=available_artifacts,
            ),
        )
        # Try the fallible work below.
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                # Local ``timeout`` ← self.timeout_secs,.
                timeout=self.timeout_secs,
            )
        # On except asyncio.TimeoutError: recover or re-raise as appropriate.
        except asyncio.TimeoutError:
            # Call ``proc.kill``.
            proc.kill()
            # Await ``proc.communicate`` and continue once it completes.
            await proc.communicate()
            # Local ``duration_ms`` ← int((time.perf_counter() - start) * 1000).
            duration_ms = int((time.perf_counter() - start) * 1000)
            # Local ``ce`` ← CodeExecution(.
            ce = CodeExecution(
                # Local ``code`` ← code,.
                code=code,
                # Local ``file_path`` ← str(script_path),.
                file_path=str(script_path),
                # Local ``stdout`` ← "",.
                stdout="",
                # Local ``stderr`` ← "timeout",.
                stderr="timeout",
                # Local ``success`` ← False,.
                success=False,
                # Local ``duration_ms`` ← duration_ms,.
                duration_ms=duration_ms,
            )
            # Hand ``ce, [ExecutionTrace(trace_type="code_execution", payload=ce.model_dump…`` back to the caller.
            return ce, [ExecutionTrace(trace_type="code_execution", payload=ce.model_dump(mode="json"))], []

        # Local ``duration_ms`` ← int((time.perf_counter() - start) * 1000).
        duration_ms = int((time.perf_counter() - start) * 1000)
        # Local ``stdout`` ← stdout_b.decode(errors="replace").
        stdout = stdout_b.decode(errors="replace")
        # Local ``stderr`` ← stderr_b.decode(errors="replace").
        stderr = stderr_b.decode(errors="replace")
        return_value: Any = None
        skill_calls: list[SkillCall] = []
        artifact_refs: list[dict] = []
        # Only when (stdout.strip()).
        if stdout.strip():
            # Try the fallible work below.
            try:
                import json
                # Local ``parsed`` ← json.loads(stdout.strip().splitlines()[-1]).
                parsed = json.loads(stdout.strip().splitlines()[-1])
                # Only when (isinstance(parsed, dict) and "__agent_result__" in parsed).
                if isinstance(parsed, dict) and "__agent_result__" in parsed:
                    # Local ``return_value`` ← parsed.get("__agent_result__").
                    return_value = parsed.get("__agent_result__")
                    # Local ``skill_calls`` ← [.
                    skill_calls = [
                        # Call ``SkillCall``.
                        SkillCall(**item)
                        # Loop: for item in parsed.get("__skill_calls__", []).
                        for item in parsed.get("__skill_calls__", [])
                        # Only when (isinstance(item, dict)).
                        if isinstance(item, dict)
                    ]
                    # Local ``artifact_refs`` ← parsed.get("__artifact_refs__", []).
                    artifact_refs = parsed.get("__artifact_refs__", [])
                else:
                    # Local ``return_value`` ← parsed.
                    return_value = parsed
            # On except Exception: recover or re-raise as appropriate.
            except Exception:
                # Local ``return_value`` ← stdout.strip().
                return_value = stdout.strip()

        # Local ``ce`` ← CodeExecution(.
        ce = CodeExecution(
            # Local ``code`` ← code,.
            code=code,
            # Local ``file_path`` ← str(script_path),.
            file_path=str(script_path),
            # Local ``stdout`` ← stdout,.
            stdout=stdout,
            # Local ``stderr`` ← stderr,.
            stderr=stderr,
            # Local ``return_value`` ← return_value,.
            return_value=return_value,
            # Local ``success`` ← proc.returncode == 0,.
            success=proc.returncode == 0,
            # Local ``duration_ms`` ← duration_ms,.
            duration_ms=duration_ms,
            # Local ``skill_calls`` ← skill_calls,.
            skill_calls=skill_calls,
        )
        # Local ``trace`` ← ExecutionTrace(trace_type="code_execution", payload=ce.model_dump….
        trace = ExecutionTrace(trace_type="code_execution", payload=ce.model_dump(mode="json"))
        # Hand ``ce, [trace], artifact_refs`` back to the caller.
        return ce, [trace], artifact_refs
