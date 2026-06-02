import { useEffect, useRef, useState, useCallback } from 'react'
import {
  connectRobotTelemetry,
  type TelemetryEvent,
  type TelemetrySignal,
  type BlobRef,
} from '@robot-fleet/client-sdk'

export interface JointState {
  name: string
  position: number
  velocity: number
  effort: number
  unit: string
}

export interface ActionEntry {
  timestamp: number
  signals: TelemetrySignal[]
  attributes?: Record<string, string>
}

export interface TelemetryStreamState {
  connected: boolean
  jointStates: JointState[]
  latestVisionUri: string | null
  latestVisionMeta: BlobRef | null
  actionLog: ActionEntry[]
  eventLog: { type: string; severity: string; message: string; timestamp: number }[]
}

const MAX_ACTION_LOG = 50
const MAX_EVENT_LOG = 100

export function useTelemetryStream(robotId: string | null): TelemetryStreamState {
  const [connected, setConnected] = useState(false)
  const [jointStates, setJointStates] = useState<JointState[]>([])
  const [latestVisionUri, setLatestVisionUri] = useState<string | null>(null)
  const [latestVisionMeta, setLatestVisionMeta] = useState<BlobRef | null>(null)
  const [actionLog, setActionLog] = useState<ActionEntry[]>([])
  const [eventLog, setEventLog] = useState<TelemetryStreamState['eventLog']>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!robotId) {
      setConnected(false)
      setJointStates([])
      setLatestVisionUri(null)
      setLatestVisionMeta(null)
      setActionLog([])
      setEventLog([])
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsBaseUrl = `${protocol}//${window.location.host}`

    const ws = connectRobotTelemetry(robotId, {
      onConnect: () => setConnected(true),
      onDisconnect: () => setConnected(false),

      onState: (event: TelemetryEvent) => {
        if (!event.state?.signals) return
        const states: JointState[] = event.state.signals.map((sig) => ({
          name: sig.name,
          position: sig.values?.[0] ?? 0,
          velocity: sig.values?.[1] ?? 0,
          effort: sig.values?.[2] ?? 0,
          unit: sig.unit ?? '',
        }))
        setJointStates(states)
      },

      onAction: (event: TelemetryEvent) => {
        if (!event.action?.signals) return
        const entry: ActionEntry = {
          timestamp: Date.now(),
          signals: event.action.signals,
          attributes: event.action.attributes,
        }
        setActionLog((prev) => [entry, ...prev].slice(0, MAX_ACTION_LOG))
      },

      onVision: (event: TelemetryEvent) => {
        const blob = event.vision?.blobs?.[0]
        if (!blob) return
        const uri = blob.uri.startsWith('/')
          ? `/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}`
          : blob.uri.startsWith('s3://')
            ? `/api/telemetry/blob?uri=${encodeURIComponent(blob.uri)}`
            : blob.uri
        setLatestVisionUri(uri)
        setLatestVisionMeta(blob)
      },

      onEvent: (event: TelemetryEvent) => {
        if (!event.event) return
        setEventLog((prev) => [{
          type: event.event!.event_type,
          severity: event.event!.severity,
          message: event.event!.message,
          timestamp: Date.now(),
        }, ...prev].slice(0, MAX_EVENT_LOG))
      },

      onInitialState: (streams: Record<string, any>) => {
        for (const [, evt] of Object.entries(streams)) {
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

    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [robotId])

  return {
    connected,
    jointStates,
    latestVisionUri,
    latestVisionMeta,
    actionLog,
    eventLog,
  }
}
