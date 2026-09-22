/**
 * @fileoverview React hook that opens a per-agent telemetry WebSocket and
 * projects events into UI-friendly joint / vision / action / event state.
 *
 * Used by AgentExecutionModal (and any future live agent panels). When `agentId`
 * is null the hook clears state and does not open a socket.
 */

// React state + effect + ref for the live WebSocket handle.
import { useEffect, useRef, useState } from 'react'
// SDK helper that speaks the agent telemetry protocol over WebSocket.
import {
  connectAgentTelemetry,
  type TelemetryEvent,
  type TelemetrySignal,
  type BlobRef,
} from '@agent-fleet/client-sdk'

/**
 * One row in the joint-state table (mapped from a TelemetrySignal).
 */
export interface JointState {
  /** Joint / signal name from the agent. */
  name: string
  /** Position (values[0]). */
  position: number
  /** Velocity (values[1]). */
  velocity: number
  /** Effort / torque (values[2]). */
  effort: number
  /** Unit string when the publisher provides one. */
  unit: string
}

/**
 * One entry in the rolling action-command log.
 */
export interface ActionEntry {
  /** Client-side receive timestamp (ms). */
  timestamp: number
  /** Raw signals from the action event. */
  signals: TelemetrySignal[]
  /** Optional attributes (e.g. cmd_type). */
  attributes?: Record<string, string>
}

/**
 * Aggregated stream state returned by {@link useTelemetryStream}.
 */
export interface TelemetryStreamState {
  /** True while the WebSocket is connected. */
  connected: boolean
  /** Latest joint states from onState / onInitialState. */
  jointStates: JointState[]
  /** Resolved HTTP(S) URI for the latest vision frame (may be proxied). */
  latestVisionUri: string | null
  /** Raw blob metadata for the latest vision frame. */
  latestVisionMeta: BlobRef | null
  /** Newest-first action log (capped). */
  actionLog: ActionEntry[]
  /** Newest-first discrete event log (capped). */
  eventLog: { type: string; severity: string; message: string; timestamp: number }[]
}

/** Max action-log rows retained in memory. */
const MAX_ACTION_LOG = 50
/** Max event-log rows retained in memory. */
const MAX_EVENT_LOG = 100

/**
 * Subscribe to live telemetry for a single agent.
 *
 * @param agentId - Agent id or `host:port` telemetry key; null disables the stream.
 * @returns Connected flag plus joint / vision / action / event projections.
 */
export function useTelemetryStream(agentId: string | null): TelemetryStreamState {
  // Whether the socket is currently open.
  const [connected, setConnected] = useState(false)
  // Latest joint table rows.
  const [jointStates, setJointStates] = useState<JointState[]>([])
  // Latest vision image URI suitable for <img src>.
  const [latestVisionUri, setLatestVisionUri] = useState<string | null>(null)
  // Latest vision blob metadata (mime, dims, etc.).
  const [latestVisionMeta, setLatestVisionMeta] = useState<BlobRef | null>(null)
  // Rolling action command log.
  const [actionLog, setActionLog] = useState<ActionEntry[]>([])
  // Rolling discrete event log.
  const [eventLog, setEventLog] = useState<TelemetryStreamState['eventLog']>([])
  // Keep the WebSocket so cleanup can close it.
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // No agent selected — reset all projections and skip connecting.
    if (!agentId) {
      setConnected(false)
      setJointStates([])
      setLatestVisionUri(null)
      setLatestVisionMeta(null)
      setActionLog([])
      setEventLog([])
      return
    }

    // Choose ws vs wss to match the page.
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Same-origin base; Vite proxies `/ws` to the gateway in development.
    const wsBaseUrl = `${protocol}//${window.location.host}`

    // Open the telemetry socket with typed event handlers.
    const ws = connectAgentTelemetry(agentId, {
      // Mark UI as live when the socket opens.
      onConnect: () => setConnected(true),
      // Mark UI as offline when the socket closes.
      onDisconnect: () => setConnected(false),

      /**
       * Handle continuous state frames (joint positions, etc.).
       * @param event - Telemetry envelope with optional `state.signals`.
       */
      onState: (event: TelemetryEvent) => {
        // Ignore empty state payloads.
        if (!event.state?.signals) return
        // Map each signal into a JointState row for the table.
        const states: JointState[] = event.state.signals.map((sig) => ({
          name: sig.name,
          position: sig.values?.[0] ?? 0,
          velocity: sig.values?.[1] ?? 0,
          effort: sig.values?.[2] ?? 0,
          unit: sig.unit ?? '',
        }))
        // Replace the whole joint table with the latest snapshot.
        setJointStates(states)
      },

      /**
       * Handle action / command frames; prepend to the rolling log.
       * @param event - Telemetry envelope with optional `action.signals`.
       */
      onAction: (event: TelemetryEvent) => {
        // Ignore empty action payloads.
        if (!event.action?.signals) return
        // Stamp with client receive time for display ordering.
        const entry: ActionEntry = {
          timestamp: Date.now(),
          signals: event.action.signals,
          attributes: event.action.attributes,
        }
        // Newest first; trim to MAX_ACTION_LOG.
        setActionLog((prev) => [entry, ...prev].slice(0, MAX_ACTION_LOG))
      },

      /**
       * Handle vision frames; rewrite relative / s3 URIs through the blob proxy.
       * @param event - Telemetry envelope with optional `vision.blobs`.
       */
      onVision: (event: TelemetryEvent) => {
        // Take the first blob only (primary camera).
        const blob = event.vision?.blobs?.[0]
        if (!blob) return
        // Relative paths and s3:// refs need the gateway blob proxy.
        const uri = blob.uri.startsWith('/')
          ? `/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}`
          : blob.uri.startsWith('s3://')
            ? `/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}`
            : blob.uri
        // Expose URI for <img> / canvas consumers.
        setLatestVisionUri(uri)
        // Keep raw metadata for callers that need mime / size.
        setLatestVisionMeta(blob)
      },

      /**
       * Handle discrete log-style events (warnings, milestones).
       * @param event - Telemetry envelope with optional `event` payload.
       */
      onEvent: (event: TelemetryEvent) => {
        // Ignore empty event payloads.
        if (!event.event) return
        // Prepend and cap the event log.
        setEventLog((prev) => [{
          type: event.event!.event_type,
          severity: event.event!.severity,
          message: event.event!.message,
          timestamp: Date.now(),
        }, ...prev].slice(0, MAX_EVENT_LOG))
      },

      /**
       * Handle the initial snapshot of streams sent right after connect.
       * @param streams - Map of stream name → last known TelemetryEvent-like object.
       */
      onInitialState: (streams: Record<string, any>) => {
        // Walk every seeded stream and apply state/vision when present.
        for (const [, evt] of Object.entries(streams)) {
          // Seed joints if this stream carried state.
          if (evt.state?.signals) {
            const states: JointState[] = evt.state.signals.map((sig: TelemetrySignal) => ({
              name: sig.name,
              position: sig.values?.[0] ?? 0,
              velocity: sig.values?.[1] ?? 0,
              effort: sig.values?.[2] ?? 0,
              unit: sig.unit ?? '',
            }))
            setJointStates(states)
          }
          // Seed vision if this stream carried a blob (relative paths proxied).
          if (evt.vision?.blobs?.[0]) {
            const blob = evt.vision.blobs[0]
            const uri = blob.uri.startsWith('/')
              ? `/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}`
              : blob.uri
            setLatestVisionUri(uri)
            setLatestVisionMeta(blob)
          }
        }
      },
    }, wsBaseUrl)

    // Stash for cleanup.
    wsRef.current = ws

    // Close the socket when agentId changes or the component unmounts.
    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [agentId])

  // Expose the aggregated projection to the caller.
  return {
    connected,
    jointStates,
    latestVisionUri,
    latestVisionMeta,
    actionLog,
    eventLog,
  }
}
