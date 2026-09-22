# docs/ — architecture and runbook index

Design and operational notes for **`agent_fleet/`**. This file is an **index only**; the documents linked below are the sources of truth. Do not treat this README as a substitute for reading those pages when debugging production or onboarding to the control plane.

## How to use this folder

| Audience | Suggested path |
|----------|----------------|
| New contributor | [`RUN.md`](RUN.md) → [`REPO_LAYOUT.md`](REPO_LAYOUT.md) → [`DESIGN.md`](DESIGN.md) |
| Frontend/dashboard developer | [`COMPONENT_FLOWS.md`](COMPONENT_FLOWS.md) → [`OPENAPI_CONTRACT.md`](OPENAPI_CONTRACT.md) |
| Infra / memory plane | [`TELEMETRY_AND_DATA_FLOW.md`](TELEMETRY_AND_DATA_FLOW.md) → [`../domains/eda/memory/README.md`](../domains/eda/memory/README.md) |
| Planner / event migration | [`COMMUNICATION_REVIEW.md`](COMMUNICATION_REVIEW.md) → [`REQUIRED_TO_REMOVE_POLLING.md`](REQUIRED_TO_REMOVE_POLLING.md) |

Keep long-form decisions in dedicated **`*.md`** files; extend this index when you add a new doc.

## Start here

| Document | When to read it |
|----------|-----------------|
| [RUN.md](RUN.md) | Bring services up, smoke-test, common failures |
| [REPO_LAYOUT.md](REPO_LAYOUT.md) | What each directory is for (inventory) |
| [DESIGN.md](DESIGN.md) | Architecture goals and major decisions |
| [COMPONENT_FLOWS.md](COMPONENT_FLOWS.md) | Who talks to whom (gateway, fleet, agents, telemetry) |

## Control plane and APIs

| Document | Topic |
|----------|--------|
| [GATEWAY_VS_TELEMETRY_SPLIT.md](GATEWAY_VS_TELEMETRY_SPLIT.md) | Why gateway (BFF) and telemetry are separate processes |
| [OPENAPI_CONTRACT.md](OPENAPI_CONTRACT.md) | Notes on the Gateway OpenAPI / HTTP contract |
| [COMMUNICATION_REVIEW.md](COMMUNICATION_REVIEW.md) | Polling vs event-driven update paths |
| [REQUIRED_TO_REMOVE_POLLING.md](REQUIRED_TO_REMOVE_POLLING.md) | Checklist to finish the event-driven migration |

## Telemetry and data

| Document | Topic |
|----------|--------|
| [TELEMETRY_AND_DATA_FLOW.md](TELEMETRY_AND_DATA_FLOW.md) | Heartbeats, stores, and data movement |
| [TELEMETRY_STORE_AND_EVENTS.md](TELEMETRY_STORE_AND_EVENTS.md) | Storage patterns and event publishing |

Engineering memory specifics (record types, plane backends, **`EdaAgent`** journaling) live in code-adjacent docs:

- [`../domains/eda/README.md`](../domains/eda/README.md)
- [`../domains/eda/memory/README.md`](../domains/eda/memory/README.md)
- [`../domains/eda/schemas/README.md`](../domains/eda/schemas/README.md)

## Planning and backlog

| Document | Topic |
|----------|--------|
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Phased roadmap and implementation status |
| [TODO.md](TODO.md) | Deferred / follow-up work items |

## Related docs outside this folder

| Path | Topic |
|------|--------|
| [`../README.md`](../README.md) | Package overview, quick start, directory tree |
| [`../fleets/README.md`](../fleets/README.md) | Fleet YAML selectors used by `scripts/startup.sh` |
| [`../deploy/README.md`](../deploy/README.md) | Config snippets mounted into Compose |
| [`../scripts/README.md`](../scripts/README.md) | Maintainer scripts index |
| [`../cli/README.md`](../cli/README.md) | `agentctl` operator CLI |
| [`../tests/README.md`](../tests/README.md) | Pytest layout and live-test flags |
| [`../../README.md`](../../README.md) | Repo-root overview and documentation map |
| [`../../etched_agentic_chip_design_system_v3.md`](../../etched_agentic_chip_design_system_v3.md) | Product/system design this fleet implements |

## Conventions for new docs

- Prefer **one topic per file** with a descriptive **`SCREAMING_SNAKE.md`** or **`PascalCase.md`** name consistent with neighbors.
- Link from this README in the appropriate section table.
- Reference **`config/platform.yaml`** and **`domains.eda`** by path when documenting behavior that code owns.
- Runbooks belong in **`RUN.md`** or a dedicated ops file — avoid duplicating step-by-step commands in **`DESIGN.md`**.

## Glossary (cross-doc terms)

| Term | Meaning in this repo |
|------|----------------------|
| **Catalog agent** | Directory under **`agents/`** with validated **`config.yaml`** |
| **Fleet YAML** | Lists catalog paths; drives Compose via **`domains.eda.fleet`** |
| **Engineering memory** | **`EngineeringMemory`** + **`MemoryRecord`** envelopes |
| **Plane** | Multi-store memory backend used in Compose (**`MEMORY_BACKEND=plane`**) |
| **Gateway** | HTTP BFF for dashboard/clients; distinct from telemetry process |
| **Embodiment** | Gateway scan of which agents exist for UI routing |

When **`DESIGN.md`** and code disagree, treat **`domains/eda`** implementation and **`tests/contract/`** as tie-breakers until docs are updated.
