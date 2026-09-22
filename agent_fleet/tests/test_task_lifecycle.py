"""Unit tests for the domain-neutral agent task lifecycle."""

from __future__ import annotations

import asyncio

from packages.agent_sdk.src.lifecycle import TaskLifecycle
from packages.agent_sdk.src.models import AgentTaskRequest, AgentTaskResult


class _Lifecycle(TaskLifecycle):
    """Small non-EDA domain adapter used to lock down generic control flow."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.events: list[str] = []

    def decode_task(self, request: AgentTaskRequest) -> dict:
        self.events.append("decode")
        return {"id": request.task_id}

    def prepare_task(self, task: dict) -> dict:
        self.events.append("prepare")
        task["prepared"] = True
        return task

    async def assemble_context(self, task: dict) -> dict:
        self.events.append("context")
        return {"for": task["id"]}

    async def journal_started(self, task: dict, context: dict) -> None:
        assert context == {"for": task["id"]}
        self.events.append("started")

    async def execute_task(self, task: dict, context: dict) -> dict:
        self.events.append("execute")
        if self.fail:
            raise RuntimeError("adapter failed")
        return {"task": task, "context": context}

    async def journal_finished(self, task: dict, result: dict) -> None:
        self.events.append("finished")
        assert result["task"]["prepared"] is True

    def failure_result(self, task: dict, exc: Exception) -> dict:
        self.events.append("failure")
        return {"task": task, "error": str(exc)}

    def encode_result(self, result: dict) -> AgentTaskResult:
        self.events.append("encode")
        return AgentTaskResult(
            success="error" not in result,
            message=result.get("error", "ok"),
            artifacts=result,
        )


def test_lifecycle_runs_opaque_domain_hooks_in_order() -> None:
    lifecycle = _Lifecycle()

    result = asyncio.run(lifecycle.handle(AgentTaskRequest(task_id="generic-1", description="work")))

    assert result.success is True
    assert lifecycle.events == ["decode", "prepare", "context", "started", "execute", "finished", "encode"]


def test_lifecycle_journals_terminal_failure_after_start() -> None:
    lifecycle = _Lifecycle(fail=True)

    result = asyncio.run(lifecycle.handle(AgentTaskRequest(task_id="generic-2", description="work")))

    assert result.success is False
    assert result.message == "adapter failed"
    assert lifecycle.events == [
        "decode",
        "prepare",
        "context",
        "started",
        "execute",
        "failure",
        "finished",
        "encode",
    ]
