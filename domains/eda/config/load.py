"""Load :class:`EDAAgentConfig` by extending the generic agent config loader."""

from __future__ import annotations

from pathlib import Path

from packages.agent_sdk.src.config.load import load_agent_config, load_agent_document
from packages.agent_sdk.src.config.registry import agent_class_name
from packages.config import AGENTS_DIR

from .models import (
    EDAAgentConfig,
    EDAAgentRole,
    EDAAgentSkill,
    EDABoundary,
    EDADelegationStep,
    EDAEngineeringContext,
    EDAOperation,
)

AGENTS_EDA_ROOT = AGENTS_DIR / "eda"


class EDAConfigError(ValueError):
    """An EDA agent config is missing domain fields or sits outside ``agents/eda``."""


def fleet_path_for(directory: Path) -> str:
    """Path of the agent directory relative to ``agents/``."""
    directory = directory.resolve()
    try:
        relative = directory.relative_to(AGENTS_DIR.resolve())
    except ValueError as exc:
        raise EDAConfigError(f"{directory} is not under {AGENTS_DIR}") from exc
    if not relative.parts or relative.parts[0] != "eda":
        raise EDAConfigError(f"{directory} is not an EDA agent directory")
    return relative.as_posix()


def load_eda_agent_config(directory: str | Path) -> EDAAgentConfig:
    """Load the generic agent config, then attach EDA flow fields."""
    directory = Path(directory)
    config_path = directory / "config.yaml"
    document = load_agent_document(config_path)
    base = load_agent_config(config_path, document)
    metadata = document["metadata"]
    labels = metadata.get("labels") or {}

    skills: list[EDAAgentSkill] = []
    for skill in document.get("skills") or []:
        if "action" not in skill:
            raise EDAConfigError(
                f"{metadata.get('name')} skill {skill.get('callable')} has no action"
            )
        skills.append(
            EDAAgentSkill(
                id=skill["id"],
                description=str(skill.get("description") or ""),
                module=str(skill.get("module") or "tools"),
                callable=skill["callable"],
                timeout_secs=skill.get("timeout_secs"),
                args_defaults=dict(skill.get("args_defaults") or {}),
                params=skill.get("params") or [],
                operation=EDAOperation(skill["action"]),
            )
        )

    delegation_plan: list[EDADelegationStep] = []
    for item in document.get("plan") or []:
        delegation_plan.append(
            EDADelegationStep(
                id=item["id"],
                agent_type=item.get("agent") or item["agent_type"],
                capability=str(item.get("capability") or ""),
                depends_on=list(item.get("depends_on") or []),
                objective=str(item.get("objective") or ""),
            )
        )

    boundary_raw = document.get("boundary") or {}
    raw_context = document.get("context")
    if not isinstance(raw_context, dict) or not raw_context.get("include") or not raw_context.get("precedence"):
        raise EDAConfigError(
            f"{metadata.get('name')} must declare context.include and context.precedence"
        )

    agent_id = str(metadata["name"])
    base_data = base.model_dump()
    for extra_key in (
        "role",
        "stage",
        "responsibility",
        "boundary",
        "delegates_to",
        "validators",
        "context",
        "plan",
        "skills",
        "may",
        "may_not",
    ):
        base_data.pop(extra_key, None)
    return EDAAgentConfig(
        **base_data,
        role=EDAAgentRole(document.get("role") or labels.get("role")),
        stage=str(document.get("stage") or labels.get("stage") or ""),
        responsibility=str(document.get("responsibility") or metadata.get("description") or ""),
        boundary=EDABoundary(
            may=list(boundary_raw.get("may") or []),
            may_not=list(boundary_raw.get("may_not") or []),
        ),
        delegates_to=list(document.get("delegates_to") or []),
        delegation_plan=delegation_plan,
        validators=list(document.get("validators") or []),
        context=EDAEngineeringContext(
            include=list(raw_context["include"]),
            exclude=list(raw_context.get("exclude") or []),
            drop=list(raw_context.get("drop") or ["rejected"]),
            precedence=list(raw_context["precedence"]),
            protect=list(raw_context.get("protect") or []),
            token_budget=int(raw_context.get("token_budget") or 80_000),
        ),
        skills=skills,
        fleet_path=fleet_path_for(directory),
        fleet_class_name=agent_class_name(agent_id),
    )
