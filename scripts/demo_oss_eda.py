"""Run the RTL agent's real Yosys tool path and publish its QoR evidence.

Start the sidecar first:
    docker compose -f compose/docker-compose.eda.yml up --build -d
Then:
    EDA_TOOLCHAIN_URL=http://127.0.0.1:8090 python scripts/demo_oss_eda.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL_AGENT_DIR = REPO_ROOT / "agents/frontend/rtl/rtl_implementation"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(RTL_AGENT_DIR))

from domains.eda.eda import bind_eda_adapter
from domains.eda.eda.toolchain import ToolchainAdapter
from domains.eda.memory.service import open_memory
from domains.eda.schemas.artifact import ArtifactRef
from domains.eda.schemas.memory import MemoryScope
from domains.eda.schemas.messages import ExperimentRecord
from tools import compile_candidate


async def main() -> None:
    """Invoke the agent skill, then store the actual observation as evidence."""
    bind_eda_adapter(ToolchainAdapter())
    observation = compile_candidate(params={
        "design_path": "gcd/gcd.v",
        "top": "gcd",
        "task_id": "gcd-yosys-demo",
        "recipe": "yosys-gcd-v1",
    })
    if observation["status"] != "succeeded":
        raise RuntimeError(observation["summary"])
    # Default file/plane memory is durable across local agent processes.
    memory = open_memory()
    experiment = ExperimentRecord(
        experiment_id="gcd-yosys-demo",
        hypothesis="The OpenSTA GCD RTL elaborates and synthesizes with Yosys.",
        baseline="external/OpenSTA/examples/gcd_rtl.v",
        conditions_held_fixed=["Yosys sidecar image", "top=gcd"],
        metrics=observation["metrics"],
        tool="yosys",
        outcome="confirmed",
        evidence=[ArtifactRef.model_validate(ref) for ref in observation["artifact_refs"]],
    )
    record = await memory.record_experiment(
        experiment,
        scope=MemoryScope(project="oss-eda-demo", revision="opensta-gcd", stage="rtl"),
        agent_id="rtl_implementation",
        task_id="gcd-yosys-demo",
        idempotency_key="gcd-yosys-demo:v1",
    )
    print(json.dumps({
        "observation": observation,
        "memory_id": record.memory_id,
        "memory_scope": record.scope,
    }, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
