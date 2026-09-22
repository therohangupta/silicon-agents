# components/modals/

Feature-level **dialogs** larger than a simple confirm box. These modals orchestrate multi-step operator workflows, own local form state, and call gateway APIs through TanStack Query mutations and queries in `lib/api`.

Shared chrome (`title`, backdrop, Escape, sizes) comes from `components/common/Modal.tsx`.

## Mission Control role

Manual planning is a first-class Mission Control workflow alongside automated planner + allocator strategies. Operators who already have goals can compose a **custom task DAG** (dependencies, per-task goal assignment, optional agent binding) without running an LLM planner.

The modal lives on the Plans flow (opened from the Plans page) and creates plans with allocation strategy semantics equivalent to **Manual Allocation** on the backend (`plansApi.createManual`).

## Files

| File | Export | Purpose |
|------|--------|---------|
| `ManualPlanCreation.tsx` | `ManualPlanCreation` | Full manual plan authoring wizard |

## `ManualPlanCreation`

Props: `{ isOpen, onClose }` — parent controls visibility and typically refetches plans on success via query invalidation (handled in parent mutation callbacks).

### UI sections

1. **Goal picker** — searchable grid of `Card` tiles; multi-select `selectedGoals`. Query: `useQuery({ queryKey: ['goals'], queryFn: goalsApi.list })`.
2. **Plan metadata** — name and description (required before submit).
3. **Task editor** — draft tasks with client `temp_id` (`t1`, `t2`, …), description, `goal_id`, optional `agent_id`, dependency multi-select on other temp ids. Query: `agentsApi.list()` for dropdown.
4. **DAG preview** — embedded Graphviz SVG with local pan/zoom (separate from `DAGVisualization.tsx` but same WASM library pattern).
5. **Actions** — add/remove tasks, regenerate graph, submit create.

### Client-side task model

```ts
interface TaskData {
  temp_id: string
  description: string
  dependencies: string[]   // other temp_ids
  agent_id?: string
  goal_id?: number
}
```

Server submission maps temp ids to the manual plan create payload expected by `ManualPlanCreateRequest` in `types.ts` (see mutation in source for field mapping).

### Validation (pre-submit)

Before `createManual` mutation:

1. At least one selected goal.
2. Non-empty plan name and description.
3. At least one task.
4. Every selected goal appears on at least one task’s `goal_id`.
5. Every task has a `goal_id` set.

Failures set `goalAssignmentError` string and open a **nested** `Modal` (validation error dialog).

### API usage

| Operation | API | Query key / notes |
|-----------|-----|-------------------|
| Load goals | `goalsApi.list()` | `['goals']` |
| Load agents | `agentsApi.list()` | `['agents']` |
| Create plan | `plansApi.createManual(data)` | `useMutation`; parent should invalidate `['plans']` |

No WebSocket in this modal. After create, global realtime may still broadcast `{ type: 'invalidate', queries: ['plans'] }` — redundant with mutation success handlers but harmless.

### Graphviz preview

- Local state: `svgContent`, `zoom`, `pan`, drag handlers, `containerRef`.
- Keyboard shortcuts while modal open: `r` reset view, `+`/`-` zoom (document listener in `useEffect`).
- Regenerates DOT from draft tasks and dependencies when tasks change or operator clicks refresh.
- Errors surface in `error` state string (rendered in preview panel).

### Operator UX details

- Goal search matches goal id substring or description case-insensitive.
- New tasks default `goal_id` to first selected goal.
- Removing a task does not auto-prune dependencies pointing at it — operator must fix deps before submit (server may also validate).
- Uses `Button`, `Card`, `Modal`, Lucide icons (`Search`, `CheckCircle`, `Plus`, `Trash2`, `Bot`, `ArrowRight`).

## WebSocket patterns

**None** in `modals/`. Realtime invalidation applies after server-side plan creation through the global channel in `lib/api.ts`.

## When to add a new modal here

Place a module in `modals/` when:

- The dialog spans multiple API calls or queries.
- Form state is substantial (not a single confirm).
- The workflow is feature-specific (not a generic alert).

Keep generic wrappers in `common/Modal.tsx`; keep execution-time inspectors in `execution/`.

## Related documentation

- `lib/api.ts` — `plansApi.createManual`, request types
- `components/common/README.md` — `Modal` sizes and scroll lock
- `pages/README.md` — Plans page entry point for opening this modal
