# components/layout/

Application **chrome** for Mission Control: the fixed left rail, content margin, and shared page headings. Every routed page renders inside `Layout` after `App` finishes loading planner/allocator method metadata.

These modules are intentionally free of TanStack Query and gateway clients. They only manage navigation, spacing, and operator preferences (sidebar collapse).

## Mission Control shell

The operator always sees:

- A **dark slate sidebar** (`bg-slate-900`) with cyan/violet brand gradient on the bot icon.
- Wordmark **Agent Fleet** and subtitle **Mission Control** when expanded.
- Primary nav: Home, Agents, Goals, Plans, Planners, Allocators — matching the route table in `App.tsx`.
- A decorative **System Online** card (expanded mode) with a pulsing emerald dot and static “Fleet Manager: localhost:50051” hint (informational, not a live health check).

Main content scrolls in a padded column (`px-8 py-6`) whose left margin tracks sidebar width so text never sits under the fixed rail.

## Files

| File | Export | Purpose |
|------|--------|---------|
| `Layout.tsx` | `Layout` | Flex shell: `Sidebar` + `<main>` with animated `marginLeft` |
| `Sidebar.tsx` | `Sidebar` | `NavLink` items, collapse toggle, brand row |
| `PageHeader.tsx` | `PageHeader` | Gradient `<h1>`, optional meta, description, actions |
| `Header.tsx` | `Header` | Sticky top bar: pathname → title + today’s date |

### `Layout.tsx`

- Props: `{ children: ReactNode }` — the active route element from React Router.
- State: `collapsed` boolean, initialized from `localStorage` key `rf-sidebar-collapsed` (`"1"` = collapsed, `"0"` = expanded).
- Effect: persists collapse on every toggle (try/catch around storage for private mode).
- Main margin: **56px** collapsed (`w-14`), **224px** expanded (`w-56`), with `transition-[margin] duration-200`.

### `Sidebar.tsx`

- Props: `{ collapsed, onToggle }`.
- Navigation config is a static array `{ name, href, icon }` using Lucide icons.
- `NavLink` active class: cyan/violet wash, white text, left cyan border, subtle inset highlight.
- Collapsed mode: icon-only links with `title` tooltip; brand shrinks to gradient icon tile.
- Footer: collapse button (`PanelLeftClose` / `PanelLeftOpen`).

### `PageHeader.tsx`

- Props: `title`, optional `description`, `meta`, `leading`, `actions`, `className`.
- Title uses `bg-gradient-to-r from-slate-900 via-cyan-800 to-slate-700 bg-clip-text text-transparent`.
- Responsive: stacks vertically on small screens; actions row aligns right on `sm+`.
- Used at the top of Dashboard, Goals, Plans, Planners, Allocators, and nested plan views.

### `Header.tsx`

- Reads `useLocation().pathname` and maps through `pageTitles` (top-level paths only).
- Sticky bar: `bg-surface/80 backdrop-blur-md`, shows formatted date in mono tabular nums.
- **Not mounted** by `Layout` today — available if a future design wants a secondary sticky title under the sidebar layout.

## API and WebSocket

**None.** Layout components do not call `/api` or open `/ws` connections. Realtime invalidation and telemetry are handled at `App`, `lib/api`, and `hooks/`.

## Operator UX details

| Concern | Behavior |
|---------|----------|
| Sidebar persistence | Survives refresh via `localStorage` |
| Active route | React Router `NavLink` `isActive` styling |
| Nested routes | Sidebar highlights Plans for `/plans/42` and `/plans/42/execute` because `href` is prefix `/plans` only for the Plans item — exact match is on `/plans` path segment via NavLink default end behavior: `/plans` item uses `to="/plans"` which may not highlight on child paths depending on RR config; verify in app if highlighting sub-routes matters |

Note: For `/plans/:id`, the Plans nav link may not show active unless `NavLink` uses `end={false}` or partial matching — current code uses default `end` on `/plans` which in RR v6 means only exact `/plans` is active. Document as-is from source.

Actually in React Router v6, NavLink to="/plans" has end=true by default, so /plans/1 won't highlight Plans. I'll mention this as a known quirk.

## Visual tokens

- Shell background: `mission-shell-bg` on the outer `Layout` div (defined in `index.css`).
- Sidebar text: `text-slate-300` default, white on active/hover.
- Main: standard page background via CSS variables on child pages.

## When to use `PageHeader` vs `Header`

| Use | Component |
|-----|-----------|
| Primary page title, CTAs, counts | `PageHeader` |
| Secondary sticky strip with date | `Header` (optional, not wired) |

New pages should use `PageHeader` for consistency with existing Mission Control screens.

## Extension checklist

- Add nav entries in `Sidebar.tsx` **and** routes in `App.tsx` **and** optionally `Header.tsx` `pageTitles`.
- Keep new chrome stateless or local-only (like collapse); do not embed data fetching in layout files.
