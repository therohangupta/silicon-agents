# hooks/

Custom **React hooks** that encapsulate gateway WebSocket protocols and project streaming data into UI-friendly state. Pages and execution components stay declarative: pass an agent id (or null) and render from returned fields.

Global fleet invalidation is **not** a hook in this folder — it lives in `lib/api.ts` as `useRealtimeUpdates()`.

## Mission Control role

During plan execution, Mission Control shows more than REST snapshots:

- **Joint/state telemetry** — position, velocity, effort per signal name.
- **Vision metadata** — latest frame URI (often proxied through the gateway blob endpoint).
- **Action command log** — recent command signals with attributes.
- **Discrete events** — typed log lines with severity.

`useTelemetryStream` powers the right column of `AgentExecutionModal` and any future live agent panel.

## Files

| File | Export | Purpose |
|------|--------|---------|
| `useTelemetryStream.ts` | `useTelemetryStream`, types | Per-agent telemetry WebSocket |

## `useTelemetryStream(agentId: string | null)`

Returns `TelemetryStreamState`:

| Field | Type | Meaning |
|-------|------|---------|
| `connected` | boolean | Socket open vs closed |
| `jointStates` | `JointState[]` | Latest table rows |
| `latestVisionUri` | string \| null | Suitable for `<img src>` |
| `latestVisionMeta` | `BlobRef` \| null | MIME/dimensions from SDK type |
| `actionLog` | `ActionEntry[]` | Newest first, max **50** |
| `eventLog` | array | Newest first, max **100** |

Exported types: `JointState`, `ActionEntry`, `TelemetryStreamState`.

### Lifecycle

```
agentId null  →  reset all state, no socket
agentId set   →  connectAgentTelemetry(..., wsBaseUrl)
agentId change / unmount  →  ws.close()
```

`wsBaseUrl` = `` `${ws|wss}//${window.location.host}` `` so dev traffic goes through Vite’s `/ws` proxy to port 8000.

### SDK handler mapping

Uses `connectAgentTelemetry` from `@agent-fleet/client-sdk`:

| Callback | Updates |
|----------|---------|
| `onConnect` / `onDisconnect` | `connected` |
| `onState` | Replaces `jointStates` from `event.state.signals` |
| `onAction` | Prepends to `actionLog` (cap 50) |
| `onVision` | Sets URI + meta; rewrites relative `/...` and `s3://...` to `/api/telemetry/blob?uri=...` |
| `onEvent` | Prepends to `eventLog` (cap 100) |
| `onInitialState` | Seeds joints/vision from snapshot map |

Joint mapping assumes signal `values[0..2]` → position, velocity, effort; `unit` defaults to empty string.

### Vision URI rewriting

Absolute HTTP(S) URIs pass through unchanged. Relative and S3 URIs need the gateway blob proxy so the browser can fetch without direct store credentials:

```
/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}
```

The hook applies this in both `onVision` and `onInitialState` (note: initial state path only rewrites leading `/`, not `s3://` in one branch — behavior matches source).

### Relationship to live video

| Channel | Hook / component | Content |
|---------|------------------|---------|
| Telemetry WS | `useTelemetryStream` | JSON events, occasional vision URIs |
| Video WS | `LiveVideoCanvas` | Binary JPEG/H.264 stream |

Both may run simultaneously in `AgentExecutionModal`. Prefer **`host:port`** telemetry key when `taskServerInfo` is available (see `execution/README.md`).

### REST usage

**None in the hook.** Blob display uses GET on `/api/telemetry/blob` via img/canvas consumers, not inside the hook’s fetch.

## Global invalidation (for comparison)

`useRealtimeUpdates()` in `lib/api.ts`:

- Singleton `realtimeManager.connect()`.
- Messages `{ type: 'invalidate', queries: string[] }` → `queryClient.invalidateQueries({ queryKey: [key] })`.
- Does not update telemetry state.

Operators see list views refresh when the gateway pushes invalidations; execution modals combine that with this hook for sub-second agent state.

## Testing and debugging

- Console: SDK and manager log connect/disconnect at app level; telemetry hook is silent except via UI `connected` flag.
- Set `agentId` null when modal closes to tear down sockets (see `AgentExecutionModal`).
- Caps prevent unbounded memory during long runs; increase constants only with care.

## Adding a new hook

1. Place WebSocket or subscription logic here, not in leaf components.
2. Document caps, URI rewriting, and cleanup in this README.
3. Re-export types used by components from the same file for a single import path.

## Related documentation

- `lib/api.ts` — REST facades and `RealtimeManager`
- `components/execution/README.md` — modal wiring and telemetry key
- `components/common/README.md` — `LiveVideoCanvas` protocol
