# dashboard-web

React + Vite SPA for **Agent Fleet Mission Control** — the operator UI that talks to the gateway over same-origin `/api` and `/ws` (proxied to `127.0.0.1:8000` in development).

## What this package does

- Browse agents, goals, plans, planners, and allocators
- Create goals and (via Plans pages) run planning / allocation / execution
- Live telemetry and video during agent execution
- Realtime TanStack Query invalidation over a global WebSocket

## Layout

| Path | Role |
|------|------|
| `index.html` | HTML shell, fonts, `#root` mount |
| `src/` | Application source (see `src/README.md`) |
| `vite.config.ts` | Dev server, aliases, API/WS proxy |
| `tailwind.config.js` | Theme tokens (cyber, surface, motion) |
| `postcss.config.js` | Tailwind + Autoprefixer |
| `tsconfig.json` / `tsconfig.node.json` | TypeScript project refs |
| `package.json` | Scripts and dependencies (no comments allowed in JSON) |
| `public/` | Static assets (favicon) |

## `package.json` keys (explained here — do not comment inside JSON)

| Key | Meaning |
|-----|---------|
| `name` | npm package id: `agent-fleet-dashboard` |
| `private` | Not published to a registry |
| `version` | Semver of this UI package |
| `type: "module"` | Native ESM for Vite/Node config |
| `scripts.dev` | `vite` — local HMR on port 5173 |
| `scripts.build` | `tsc` typecheck then `vite build` |
| `scripts.preview` | Serve the production build locally |
| `dependencies.@agent-fleet/client-sdk` | Local file dependency on the TypeScript gateway SDK |
| `dependencies.@hpcc-js/wasm-graphviz` | WASM Graphviz for DAG SVGs |
| `dependencies.@tanstack/react-query` | Server-state cache / mutations |
| `dependencies.clsx` / `tailwind-merge` | `cn()` class merging |
| `dependencies.framer-motion` | Motion (available; used where imported) |
| `dependencies.jszip` | Zip helpers for artifact downloads |
| `dependencies.lucide-react` | Icon set |
| `dependencies.react` / `react-dom` | React 18 |
| `dependencies.react-router-dom` | Client routing |
| `dependencies.reactflow` | Optional React Flow DAG embeds |
| `devDependencies` | Vite, React plugin, Tailwind, PostCSS, TypeScript, React types |

## Commands

```bash
cd agent_fleet/services/dashboard-web
npm install
npm run dev      # http://localhost:5173  (gateway on :8000)
npm run build
npm run preview
```

## Path aliases

- `@/*` → `src/*`
- `@agent-fleet/client-sdk` → `../../packages/client_sdk/typescript/src/index.ts` (Vite + TS)

## Out of scope for this documentation pass

Page modules owned by another task (comments/README there):

- `src/pages/PlanDetails.tsx`
- `src/pages/Plans.tsx`
- `src/pages/Agents.tsx`
- `src/pages/Execution.tsx`
- `src/pages/README.md`
