# client_sdk/typescript/src/models/

TypeScript **interfaces** for Gateway JSON payloads.

## Purpose

`types.ts` defines request/response shapes shared by `gatewayClient.ts` and
dashboard components. Strong typing catches contract drift at compile time when
Gateway adds or renames fields.

This file describes **BFF JSON**, not raw `fleet_manager_pb2` messages — field
names may differ from gRPC after Gateway normalization.

## File inventory

| File | Role |
|------|------|
| `types.ts` | Interfaces + type aliases for REST DTOs |
| `README.md` | you are here |

## Major type groups (consult types.ts for full list)

| Group | Examples | Used by |
|-------|----------|---------|
| Agents | `Agent`, `AgentInstanceCreateRequest`, `AgentAllocationsResponse` | Agent admin UI |
| Plans | `Plan`, `PlanCreateRequest`, `ManualPlanCreateRequest`, `PlanStatus` | Planner views |
| Tasks | `Task` | Task boards, execution |
| Goals | `Goal`, `GoalCreateRequest` | Goal management |
| Strategies | `StrategiesResponse` | Planner/allocator pickers |
| World | `Embodiment`, world-related types | Digital twin / embodiment panels |
| Methods | `MethodSummary`, `MethodDetail` | Method browser |

WebSocket-specific unions live in **`../realtime/events.ts`**, not here — except
when task objects inside `tasks_update` mirror `Task` fields.

## Maintenance workflow

1. Gateway handler changes JSON shape.
2. Update **`types.ts`** interfaces.
3. Fix TypeScript errors in dashboard-web (compiler-driven audit).
4. Optionally update **`python/src/models/types.py`** for script parity.
5. REST OpenAPI snapshot (future) should match this file.

Prefer optional `?` properties for newly nullable server fields to avoid breaking
existing UI during rollout.

## Relationship to JSON Schema

| Contract | File |
|----------|------|
| WebSocket events | `../../../contract/events.schema.json` |
| REST bodies | `types.ts` (authoritative for TS today) |

If REST schema files are added under `contract/`, duplicate documentation in
`contract/README.md` and keep `types.ts` in sync.

## How Gateway, fleet, and agents relate

```
fleet_manager_pb2 messages
        ▼ (Gateway mapping layer)
JSON DTOs in types.ts
        ▼
React components
```

Agent-local task payloads on agent HTTP servers are **not** these types unless
Gateway proxies them unchanged.

## Related documentation

- `../http/README.md` — methods returning these types
- `../../python/src/models/README.md` — Python typing roadmap
- `../../../../fleet_sdk/src/models.py` — persistence layer (different layer)

## Reading order

1. Skim **`types.ts`** for resource you are building UI for.
2. Hit Gateway endpoint with curl — compare JSON to interface.
3. Adjust interface + fix compile errors in dashboard.
4. Document notable BFF ↔ proto differences in Gateway service comments.

## Naming conventions

- `*Request` suffix for POST/PATCH bodies.
- `*Response` when wrapper objects exist (e.g. allocations).
- Use `number` for plan/goal/task ids matching JSON (not bigint unless required).
