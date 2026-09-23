# client_sdk/python/src/models/

Typed **payload helpers** for Gateway JSON responses and request bodies.

## Purpose

Python `GatewayClient` currently returns `Any` from many methods. This module
(`types.py`) is the home for dataclasses, TypedDicts, or Pydantic models that
mirror Gateway DTOs as the REST contract stabilizes — matching the role of
`client_sdk/typescript/src/models/types.ts` in the dashboard.

## File inventory

| File | Role |
|------|------|
| `types.py` | Dataclasses / structures for Gateway JSON |
| `README.md` | you are here |

## Design direction

| Concern | Approach |
|---------|----------|
| Source of truth | Gateway route handlers + TS `types.ts` |
| Validation | Optional — start with dataclasses for IDE hints |
| WebSocket tasks | `tasks_update.tasks` remains `list[dict]` until Task DTO frozen |

When adding a type:

1. Copy field names from Gateway OpenAPI or TS interface.
2. Use optional fields for nullable JSON keys.
3. Parse in client methods: `Plan(**client.get_plan(id))` when ready.

## Relationship to other modules

```
http/client.py  ──returns JSON──►  models/types.py (future parsing)
realtime/events.py  ──separate──►  WebSocket union (not in types.py today)
```

WebSocket event dataclasses live in **`../realtime/events.py`** by design — do
not merge WS types into `types.py` unless sharing nested DTOs (e.g. Task).

## TypeScript parity

`typescript/src/models/types.ts` defines:

- `Agent`, `Plan`, `Task`, `Goal`, agent profile types
- Request types: `PlanCreateRequest`, `GoalCreateRequest`, etc.

Python should grow equivalent names for script ergonomics. Grep TS file when
adding Python models.

## How Gateway, fleet, and agents relate

Models describe **Gateway JSON**, not gRPC proto messages. Field names may differ
slightly from `fleet_manager_pb2` due to BFF shaping.

Agents expose their own task payloads on agent HTTP servers — out of scope here.

## Related documentation

- `../http/README.md` — REST client methods returning JSON
- `../../typescript/src/models/README.md` — canonical TS interfaces
- `../../../contract/README.md` — WebSocket schema (not REST)

## Reading order

1. Skim **`types.py`** for what exists today.
2. Read **`typescript/src/models/types.ts`** for full contract.
3. Pick one resource (e.g. Plan) and add Python dataclass + client return type.
4. Validate against live Gateway JSON in a script or pytest fixture.

## Testing suggestion

Golden JSON files under tests (future) parsed into dataclasses catch Gateway
breaking changes without running the full dashboard.

## Field mapping hints (Plan / Task)

When modeling Plan and Task, align with Gateway JSON keys (not proto snake_case
unless the BFF uses it):

| Concept | Typical JSON keys | Notes |
|---------|-------------------|-------|
| Plan id | `plan_id` | integer |
| Execution status | `execution_status` or nested status object | confirm in TS `Plan` |
| Task id | `task_id` | integer |
| Assigned agent | `agent_id` | string agent id |
| Dependencies | `depends_on` or `dependency_task_ids` | Gateway-specific |

Always verify against a live `GET /api/plans/{id}` response before locking
dataclass fields as required.

## Optional Pydantic migration

If validation becomes necessary (CLI writing back to Gateway), Pydantic v2 models
can replace dataclasses in this module without changing httpx call sites — parse
with `Model.model_validate(json)` inside `GatewayClient` methods when you add
return types.

## Import paths in monorepo scripts

Scripts run from `` often use:

```python
# Prefer installed package name after pip install -e .../python
# or append python/src to PYTHONPATH and import submodules directly.
```

Document the chosen import style in your script header so operators reproduce
the environment consistently.
