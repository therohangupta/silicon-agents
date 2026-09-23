"""Lead planning: turn :class:`EDAAgentConfig` into a :class:`WorkflowProposal` graph."""

from __future__ import annotations

from ..config.models import EDAAgentConfig, EDAAgentRole, EDADelegationStep
from ..schemas.messages import WorkflowProposal, ProposedTask
from ..schemas.task import TaskBrief


def build_workflow(config: EDAAgentConfig, task: TaskBrief) -> WorkflowProposal:
    steps = list(config.delegation_plan) or _derived_steps(config)
    tasks: list[ProposedTask] = []
    for step in steps:
        tasks.append(
            ProposedTask(
                id=step.id,
                agent_type=step.agent_type,
                capability=step.capability or _primary_capability(step.agent_type),
                depends_on=list(step.depends_on),
                objective=step.objective or task.objective,
            )
        )
    return WorkflowProposal(
        workflow_id=f"{config.agent_id}:{task.task_id}",
        parent_task_id=task.task_id,
        parent_agent=config.agent_id,
        tasks=tasks,
    )


def _derived_steps(config: EDAAgentConfig) -> list[EDADelegationStep]:
    from ..fleet.registry import get_config

    workers: list[str] = []
    validators: list[str] = []
    for agent_id in config.delegates_to:
        child = get_config(agent_id)
        if child.role == EDAAgentRole.VALIDATOR:
            validators.append(agent_id)
        else:
            workers.append(agent_id)
    steps = [EDADelegationStep(id=agent_id, agent_type=agent_id) for agent_id in workers]
    for agent_id in validators:
        steps.append(
            EDADelegationStep(
                id=agent_id,
                agent_type=agent_id,
                depends_on=[step.id for step in steps],
            )
        )
    return steps


def _primary_capability(agent_type: str) -> str:
    from ..fleet.registry import get_config

    config = get_config(agent_type)
    if config.role == EDAAgentRole.LEAD:
        return "delegate_tasks"
    if config.skills:
        return config.skills[0].name
    return agent_type
