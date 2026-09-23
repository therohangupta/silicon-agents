# Agent SDK — plan workspace (`packages/agent_sdk/src/workspace/`)

**Plan-scoped blob storage** for artifacts too large to inline in `AgentTaskRequest`. Agents **`publish`** outputs; the fleet executor collects **`ArtifactRef`** entries and passes them to downstream tasks via **`ExecutionContextSnapshot.available_artifacts`**.

This is distinct from **agent-local memory** ([`../memory/`](../memory/README.md)) and from user upload storage outside the plan namespace.

---

## Purpose in the fleet

Long-running workflows produce large intermediates (JSON reports, binary blobs, logs). The workspace layer:

- Stores bytes under `{plan_id}/{task_id}/{name}`
- Returns stable **`ArtifactRef`** URIs for planners and LLMs (`schema_hint`, `description`)
- Supports **local disk** (dev/single-node) and **S3** (shared/production) backends

Agents load peer artifacts with **`PlanWorkspace.load(ref)`** without serializing full payloads in every HTTP call.

---

## Placement in architecture

```text
Executor sets request.workspace_uri + context.available_artifacts
        │
        ▼
PlanWorkspace.from_request(request)
        │
        ├── publish(name, data) ──► WorkspaceBackend.write ──► URI
        │         └── append ArtifactRef to published_refs
        │
        └── load(ref) ──► read producer_task_id/name path
        │
        ▼
AgentTaskResult.artifact_refs  ──►  next task's context
```

Backend selection parses **`workspace_uri`** ([`plan_workspace.py`](plan_workspace.py)).

---

## Files in this directory

| File | Role |
|------|------|
| [`backend.py`](backend.py) | `WorkspaceBackend` ABC; `LocalWorkspaceBackend`, `S3WorkspaceBackend` |
| [`plan_workspace.py`](plan_workspace.py) | `PlanWorkspace` agent API — publish, load, list, exists |
| [`__init__.py`](__init__.py) | Re-exports `PlanWorkspace`, backends |
| [`README.md`](README.md) | This document |

Models: [`ArtifactRef`](../models.py) in `models.py`.

Public import: `from packages.agent_sdk import PlanWorkspace`.

---

## WorkspaceBackend (`backend.py`)

Abstract async API:

| Method | Contract |
|--------|----------|
| `write(plan_id, path, data)` | Persist bytes; return canonical URI |
| `read(plan_id, path)` | Load bytes; `FileNotFoundError` if missing |
| `list_paths(plan_id)` | All relative paths under plan |
| `delete(plan_id, path)` | Remove object |
| `exists(plan_id, path)` | Boolean check |
| `uri_for(plan_id, path)` | URI without I/O |

### LocalWorkspaceBackend

- Root: `WORKSPACE_STORAGE_ROOT` env, [`packages.config.WORKSPACE_STORAGE_ROOT`](../../../packages/config/), or constructor `root`.
- Layout on disk: `{root}/{plan_id}/{path}` where path includes `{task_id}/{name}` from `PlanWorkspace`.
- URI scheme: `workspace://{plan_id}/{path}`

### S3WorkspaceBackend

- Bucket from `WORKSPACE_S3_BUCKET`, `S3_BUCKET`, or constructor.
- Keys: `{prefix}/{plan_id}/{path}` default prefix `workspaces`.
- URI scheme: `s3://{bucket}/{prefix}/{plan_id}/{path}`
- Uses boto3 sync client inside async methods (acceptable for artifact-sized I/O).

---

## PlanWorkspace (`plan_workspace.py`)

**Construction:**

- `PlanWorkspace(plan_id, task_id, agent_id, backend=..., workspace_uri=...)`
- **`from_request(request)`** — Reads `plan_id`, `task_id`, `workspace_uri`; builds backend via `_create_backend_from_uri`.

**URI parsing (`_create_backend_from_uri`):**

| URI pattern | Backend |
|-------------|---------|
| `workspace://{plan_id}` | Local, default root |
| `workspace://{plan_id}?root=/path` | Local with custom root |
| `s3://{bucket}/.../{plan_id}` | S3; plan_id from last path segment |

**Publishing:**

- `publish(name, data, format=..., schema_hint=..., description=...)` → writes `{task_id}/{name}`, builds `ArtifactRef`, tracks in `_published`.
- `publish_file(name, file_path, ...)` — read local file then publish.
- Property **`published_refs`** — executor merges into task result.

**Loading:**

- `load(ref)` / `load_json(ref)` — resolves `{ref.producer_task_id}/{ref.name}` under `plan_id`.
- `list_artifacts()` — all paths in plan namespace.
- `exists(name)` — current task slot only.

---

## Data and control flow

1. Control plane assigns `workspace_uri` per plan run (local or S3).
2. Task N agent publishes congestion or placement JSON → refs in result.
3. Task N+1 receives refs in `context.available_artifacts`; optional `schema_hint` helps LLM agents decide whether to load.
4. Agent loads bytes only when needed (keeps prompts small).

**Inline artifacts** — Small dicts still fit in `AgentTaskResult.artifacts`; workspace is for bulk binary/text.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../models.py`](../models.py) | `ArtifactRef`, `ExecutionContextSnapshot` |
| [`../memory/README.md`](../memory/README.md) | Small agent-local state |
| [`../../../packages/config/`](../../../packages/config/) | Default storage roots and buckets |

---

## Newcomer reading order

1. `ArtifactRef` and `AgentTaskRequest.workspace_uri` in [`../models.py`](../models.py)
2. [`plan_workspace.py`](plan_workspace.py) — agent API
3. [`backend.py`](backend.py) — storage layout
4. Domain agent example that publishes artifacts

---

## Operational notes

- **Permissions** — Local root must be writable by container user; S3 needs IAM/credentials in env.
- **Plan isolation** — Paths scoped by `plan_id`; tasks separated by `task_id` prefix in relative path.
- **Cleanup** — No automatic TTL in SDK; fleet retention policies apply at storage layer.
- **Consistency** — S3 `exists` uses head_object; eventual consistency applies per AWS rules.
- **Testing** — Use `LocalWorkspaceBackend(root=tmp_path)` in unit tests without S3.

No subdirectories under `workspace/`.
