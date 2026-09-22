# client_sdk/src/

**Legacy / reserved directory** — not the active implementation root for either
language SDK.

## Purpose

Historical monorepo layouts sometimes placed shared client sources directly
under `client_sdk/src/`. The current layout splits implementations by language:

- **`../typescript/src/`** — `@agent-fleet/client-sdk` (dashboard)
- **`../python/src/`** — `agent-fleet-client-sdk` (scripts)

This folder remains as a documented placeholder so contributors do not recreate
duplicate HTTP clients here.

## File inventory

| File | Role |
|------|------|
| `README.md` | you are here — routing doc only |

No `.ts` or `.py` implementation files belong in this directory. If you find
stray sources here during cleanup, move them to the appropriate language tree
and update imports in `dashboard-web` or Python packaging.

## Where to work instead

| Task | Go to |
|------|--------|
| Add Gateway REST method | `typescript/src/http/gatewayClient.ts` + optional `python/src/http/client.py` |
| Add WebSocket event type | `contract/events.schema.json` + both `realtime/events` modules |
| Shared JSON Schema | `../contract/` |
| Package metadata | `../typescript/package.json` or `../python/pyproject.toml` |

## How Gateway, fleet, and agents relate

Nothing in **`client_sdk/src/`** participates in runtime flows. Gateway serves
HTTP/WS; fleet_server serves gRPC; agents serve task HTTP — all wired through
the language-specific SDK trees listed above.

## Related documentation

- `../README.md` — client_sdk overview and reading order
- `../typescript/README.md` — primary frontend SDK
- `../python/README.md` — script SDK

## Reading order

1. Read **`../README.md`** — skip lingering here unless auditing repo layout.
2. Jump to **`../typescript/src/`** or **`../python/src/`** for all implementation work.

## FAQ

**Why does this directory exist at all?** Early scaffolding used a language-neutral
`src/` folder name. Splitting by `typescript/` and `python/` keeps packaging,
lint rules, and CI jobs independent (npm vs pip) while preserving a clear redirect
for anyone following old paths or docs.

**Can we delete `client_sdk/src/`?** Only after confirming no tooling or imports
reference it. Until then, this README prevents accidental duplication of HTTP
clients in an unused folder.

**Is shared code coming here?** Unlikely. JSON Schema lives in `contract/`; there
is no runtime shared library between TS and Python in this repo — duplication is
intentionally thin and contract-tested via `events.schema.json`.

## Directory map (sibling folders)

| Sibling | Contains |
|---------|----------|
| `../contract/` | WebSocket JSON Schema |
| `../typescript/` | `@agent-fleet/client-sdk` |
| `../python/` | `agent-fleet-client-sdk` |
| `../README.md` | Bilingual overview |

## Gateway integration reminder

External clients never import this path. **`dashboard-web`** resolves
`@agent-fleet/client-sdk` to `../typescript/`. Python scripts install
`../python/`. Both talk to the Gateway BFF only; fleet gRPC remains internal.
