"""EDA agent registry: domain rules on top of the generic agent registry."""

from __future__ import annotations

from pathlib import Path

from packages.agent_sdk.src.config.registry import validate_agent_registry

from ..config.load import AGENTS_EDA_ROOT, load_eda_agent_config
from ..config.models import EDAAgentConfig, EDAAgentRole, ROLE_OPERATIONS


class EDARegistryError(ValueError):
    """An EDA fleet breaks a chip-flow role, skill, or delegation rule."""


def iter_configs() -> list[Path]:
    configs: list[Path] = []
    for path in AGENTS_EDA_ROOT.rglob("config.yaml"):
        parts = path.relative_to(AGENTS_EDA_ROOT).parts
        if "runtime" in parts or "__pycache__" in parts:
            continue
        configs.append(path)
    return sorted(configs)


_CACHE: dict[str, EDAAgentConfig] | None = None


def validate_eda_registry(configs: list[EDAAgentConfig] | None = None) -> None:
    """Check generic uniqueness, then EDA role, skill, and delegation rules."""
    configs = list(configs) if configs is not None else [
        load_eda_agent_config(path.parent) for path in iter_configs()
    ]
    validate_agent_registry(configs)
    by_id = {cfg.agent_id: cfg for cfg in configs}
    seen_tools: dict[str, str] = {}
    for cfg in configs:
        if cfg.role == EDAAgentRole.LEAD and not cfg.delegates_to and not cfg.delegation_plan:
            raise EDARegistryError(f"{cfg.agent_id} is a lead with no children")
        tool_names = [item.name for item in cfg.skills]
        if not 10 <= len(tool_names) <= 40:
            raise EDARegistryError(f"{cfg.agent_id} has {len(tool_names)} tools; expected 10 to 40")
        if len(tool_names) != len(set(tool_names)):
            raise EDARegistryError(f"{cfg.agent_id} has duplicate tools")
        for item in cfg.skills:
            param_names = [param.name for param in item.parameters]
            if len(param_names) != len(set(param_names)):
                raise EDARegistryError(f"{cfg.agent_id} tool {item.name} has duplicate parameters")
            for param_name in param_names:
                if not param_name.isidentifier() or param_name == "params":
                    raise EDARegistryError(
                        f"{cfg.agent_id} tool {item.name} parameter {param_name} is invalid"
                    )
            if not item.name.isidentifier():
                raise EDARegistryError(f"{cfg.agent_id} tool {item.name} is not an identifier")
            if item.name in seen_tools:
                raise EDARegistryError(
                    f"Tool {item.name} is declared by both {seen_tools[item.name]} and {cfg.agent_id}"
                )
            seen_tools[item.name] = cfg.agent_id
            if item.operation not in ROLE_OPERATIONS[cfg.role]:
                raise EDARegistryError(
                    f"{cfg.agent_id} skill {item.name} operation {item.operation.value} "
                    f"is not allowed for {cfg.role.value}"
                )
        for child in cfg.delegates_to:
            if child not in by_id:
                raise EDARegistryError(f"{cfg.agent_id} delegates to unknown agent {child}")
        step_ids = {item.id for item in cfg.delegation_plan}
        for plan_step in cfg.delegation_plan:
            if plan_step.agent_type not in by_id:
                raise EDARegistryError(
                    f"{cfg.agent_id} plan references unknown agent {plan_step.agent_type}"
                )
            missing = [dep for dep in plan_step.depends_on if dep not in step_ids]
            if missing:
                raise EDARegistryError(f"{cfg.agent_id} step {plan_step.id} depends on {missing}")
        for validator in cfg.validators:
            target = by_id.get(validator)
            if target is None or target.role != EDAAgentRole.VALIDATOR:
                raise EDARegistryError(f"{cfg.agent_id} validator {validator} is not a validator")


def all_configs() -> list[EDAAgentConfig]:
    global _CACHE
    if _CACHE is None:
        loaded = [load_eda_agent_config(path.parent) for path in iter_configs()]
        validate_eda_registry(loaded)
        _CACHE = {cfg.agent_id: cfg for cfg in loaded}
    return [cfg for _, cfg in sorted(_CACHE.items(), key=lambda item: item[1].port)]


def get_config(agent_id: str) -> EDAAgentConfig:
    if _CACHE is None:
        all_configs()
    assert _CACHE is not None
    try:
        return _CACHE[agent_id]
    except KeyError as exc:
        raise EDARegistryError(f"Unknown agent {agent_id}") from exc


def fleet_capability_index() -> list[dict]:
    rows: list[dict] = []
    for cfg in all_configs():
        rows.append({
            "agent_id": cfg.agent_id,
            "display_name": cfg.display_name,
            "stage": cfg.stage,
            "path": cfg.fleet_path,
            "role": cfg.role.value,
            "port": cfg.port,
            "responsibility": cfg.responsibility,
            "may": cfg.may,
            "may_not": cfg.may_not,
            "capabilities": [
                {"id": capability_id, "description": description}
                for capability_id, description in cfg.capability_pairs
            ],
            "delegates_to": cfg.delegates_to,
            "validators": cfg.validators,
        })
    return rows
