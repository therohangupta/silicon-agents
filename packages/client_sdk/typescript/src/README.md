# client_sdk/typescript/src/

TypeScript **implementation root** for `@agent-fleet/client-sdk`.

## Purpose

Groups HTTP transport, shared JSON types, and realtime clients behind a single
barrel (`index.ts`). Dashboard features import from the package root so internal
file moves stay encapsulated.

## Directory layout

```
src/
├── index.ts              ← public barrel
├── README.md             ← you are here
├── http/
│   ├── fetchApi.ts
│   ├── gatewayClient.ts
│   └── README.md
├── models/
│   ├── types.ts
│   └── README.md
└── realtime/
    ├── events.ts
    ├── wsClient.ts
    ├── telemetryClient.ts
    └── README.md
```

## Module dependency graph

```
index.ts
    ├── models/types.ts          (no internal deps)
    ├── http/fetchApi.ts         (standalone fetch wrapper)
    ├── http/gatewayClient.ts    → fetchApi, models/types
    ├── realtime/events.ts       (types only)
    ├── realtime/wsClient.ts     → events
    └── realtime/telemetryClient.ts → fetch or WS helpers (see file)
```

No circular imports — models stay leaf nodes.

## HTTP vs realtime split

| Layer | Responsibility |
|-------|----------------|
| **http/** | Request/response REST; cache-friendly reads |
| **realtime/** | Push invalidation and live task snapshots |
| **models/** | Shared interfaces for both |

REST does not subscribe to WebSocket — dashboard combines both clients.

## Contract alignment

| Artifact | Location |
|----------|----------|
| WebSocket union | `../../contract/events.schema.json` |
| TS event types | `realtime/events.ts` |
| REST DTOs | `models/types.ts` + Gateway server |

When Gateway adds fields, update `types.ts` first for compiler coverage in
dashboard-web.

## How Gateway, fleet, and agents use this tree

| Component | Role |
|-----------|------|
| **dashboard-web** | Imports barrel; primary runtime consumer |
| **Gateway** | Server-side counterpart |
| **fleet_server** | Persists state mutated via REST |
| **Agents** | Task execution updates flow fleet → Gateway → WS |

Agents never bundle this package in Docker images.

## Related documentation

- `../README.md` — package.json and linking
- `http/README.md` — fetchApi + GatewayClient methods
- `models/README.md` — interface catalog
- `realtime/README.md` — WS + telemetry viewer
- `../../python/src/README.md` — Python mirror layout

## Reading order

1. **`index.ts`** — exported symbols.
2. **`models/types.ts`** — data shapes for UI.
3. **`http/gatewayClient.ts`** — endpoint map.
4. **`realtime/wsClient.ts`** — subscription entry points.
5. **`realtime/telemetryClient.ts`** — live telemetry panels.

## Tooling notes

- Vite resolves `.ts` exports directly — no separate `dist/` required for local
  `file:` dependency.
- Keep interfaces (not classes) in `models/` unless behavior is required.
- Prefer `fetchApi` error shape `{ detail: string }` consistent with Gateway.
