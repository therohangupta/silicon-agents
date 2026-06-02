from typing import Optional

from pydantic import BaseModel


class TaskRequest(BaseModel):
    task_description: str
    task_id: Optional[str] = None
    record_episode: bool = False


class TaskResult(BaseModel):
    success: bool
    message: str
    replan: bool

