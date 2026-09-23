"""Runtime execution traces exchanged between agent components."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SkillCall(BaseModel):
    """One invocation of a registered skill."""

    skill_id: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration_ms: int = 0


class MemoryOp(BaseModel):
    """One memory operation recorded in an execution trace."""

    op: Literal["read", "write", "search", "clear"]
    store_id: str
    key: Optional[str] = None
    value: Any = None


class CodeExecution(BaseModel):
    """The outcome of code run by an agent runtime."""

    language: str = "python"
    code: str
    file_path: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    success: bool = True
    duration_ms: int = 0
    skill_calls: list[SkillCall] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    """A typed event emitted during task execution."""

    trace_type: Literal["skill_call", "code_execution", "memory_op", "event"]
    payload: dict[str, Any] = Field(default_factory=dict)
