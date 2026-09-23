"""EDA-specific configuration layered on the generic SDK ``AgentConfig``.

The generic SDK defines how an agent process runs. This module defines how a
chip-design agent participates in an EDA program: flow roles, permitted EDA
operations, design-flow delegation, and engineering-memory context.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from packages.agent_sdk.src.config import AgentConfig
from packages.agent_sdk.src.config.registry import agent_class_name
from packages.agent_sdk.src.skills import (
    OperationDeclaration,
    RoleDeclaration,
    SkillDeclaration,
)


class EDAAgentRole(str, Enum):
    """EDA flow responsibility for an agent process."""

    LEAD = "lead"
    WORKER = "worker"
    VALIDATOR = "validator"


class EDAOperation(str, Enum):
    """EDA-specific operation categories enforced before a skill runs."""

    CREATE_FLOW_WORKFLOW = "create_workflow"
    PUBLISH_ENGINEERING_FINDING = "publish_finding"
    READ_ENGINEERING_EVIDENCE = "read_reports"
    REQUEST_PROGRAM_DECISION = "request_human_decision"
    WRITE_DESIGN_CANDIDATE = "write_candidate"
    SUBMIT_EDA_JOB = "submit_tool_job"
    EMIT_SIGNOFF_GATE = "emit_gate"


EDA_ROLE_DEFINITIONS: dict[EDAAgentRole, RoleDeclaration] = {
    EDAAgentRole.LEAD: RoleDeclaration(
        id=EDAAgentRole.LEAD.value,
        description="Coordinates an EDA flow and proposes child workflow graphs.",
    ),
    EDAAgentRole.WORKER: RoleDeclaration(
        id=EDAAgentRole.WORKER.value,
        description="Performs EDA implementation or analysis work.",
    ),
    EDAAgentRole.VALIDATOR: RoleDeclaration(
        id=EDAAgentRole.VALIDATOR.value,
        description="Independently evaluates EDA candidates and gates.",
    ),
}


EDA_OPERATION_DEFINITIONS: dict[EDAOperation, OperationDeclaration] = {
    operation: OperationDeclaration(id=operation.value)
    for operation in EDAOperation
}


ROLE_OPERATIONS: dict[EDAAgentRole, frozenset[EDAOperation]] = {
    EDAAgentRole.LEAD: frozenset({
        EDAOperation.CREATE_FLOW_WORKFLOW,
        EDAOperation.PUBLISH_ENGINEERING_FINDING,
        EDAOperation.READ_ENGINEERING_EVIDENCE,
        EDAOperation.REQUEST_PROGRAM_DECISION,
    }),
    EDAAgentRole.WORKER: frozenset({
        EDAOperation.WRITE_DESIGN_CANDIDATE,
        EDAOperation.SUBMIT_EDA_JOB,
        EDAOperation.READ_ENGINEERING_EVIDENCE,
        EDAOperation.PUBLISH_ENGINEERING_FINDING,
    }),
    EDAAgentRole.VALIDATOR: frozenset({
        EDAOperation.SUBMIT_EDA_JOB,
        EDAOperation.READ_ENGINEERING_EVIDENCE,
        EDAOperation.EMIT_SIGNOFF_GATE,
        EDAOperation.PUBLISH_ENGINEERING_FINDING,
    }),
}


class EDAAgentSkill(SkillDeclaration):
    """A generic skill declaration constrained by one EDA operation."""

    operation: EDAOperation

    @property
    def operation_definition(self) -> OperationDeclaration:
        """Generic operation contract instantiated by this EDA operation."""
        return EDA_OPERATION_DEFINITIONS[self.operation]


class EDADelegationStep(BaseModel):
    """One node in an EDA lead's declared flow delegation plan."""

    id: str
    agent_type: str
    capability: str = ""
    depends_on: list[str] = Field(default_factory=list)
    objective: str = ""


class EDAEngineeringContext(BaseModel):
    """EDA memory sources and ranking policy for an agent task."""

    include: list[str]
    exclude: list[str] = Field(default_factory=list)
    drop: list[str] = Field(default_factory=lambda: ["rejected"])
    precedence: list[str]
    protect: list[str] = Field(default_factory=list)
    token_budget: int = 80_000


class EDABoundary(BaseModel):
    """Declared EDA-flow authority for the agent."""

    may: list[str] = Field(default_factory=list)
    may_not: list[str] = Field(default_factory=list)


class EDAAgentConfig(AgentConfig):
    """Generic agent runtime configuration specialized for the EDA domain.

    This intentionally extends ``AgentConfig`` directly. Other domains are
    free to define entirely different role systems, permission models, and
    planning semantics.
    """

    role: EDAAgentRole
    stage: str = ""
    responsibility: str = ""
    boundary: EDABoundary = Field(default_factory=EDABoundary)
    delegates_to: list[str] = Field(default_factory=list)
    delegation_plan: list[EDADelegationStep] = Field(default_factory=list)
    validators: list[str] = Field(default_factory=list)
    context: EDAEngineeringContext
    skills: list[EDAAgentSkill] = Field(default_factory=list)
    fleet_path: str = ""
    fleet_class_name: str = ""

    @property
    def agent_id(self) -> str:
        return self.metadata.name

    @property
    def display_name(self) -> str:
        return self.metadata.display_name or self.agent_id

    @property
    def port(self) -> int:
        return int(self.connection.port)

    @property
    def may(self) -> list[str]:
        return self.boundary.may

    @property
    def may_not(self) -> list[str]:
        return self.boundary.may_not

    @property
    def category(self) -> str:
        return self.fleet_path

    @property
    def capability_pairs(self) -> list[tuple[str, str]]:
        pairs = [(skill.name, skill.description) for skill in self.skills]
        if self.role == EDAAgentRole.LEAD:
            pairs.append((
                "delegate_tasks",
                "Propose an EDA flow dependency graph without executing child skills.",
            ))
        return pairs

    def model_post_init(self, __context: Any) -> None:
        if not self.fleet_class_name:
            object.__setattr__(self, "fleet_class_name", agent_class_name(self.agent_id))

    @property
    def role_definition(self) -> RoleDeclaration:
        """Generic role contract instantiated by this EDA role."""
        return EDA_ROLE_DEFINITIONS[self.role]
