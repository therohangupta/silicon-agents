/**
 * @file Browser-facing telemetry stream client.
 *
 * Connects to the Gateway/telemetry realtime endpoint to render live
 * agent telemetry panels. Distinct from agent-side `TelemetryPublisher`
 * which *emits* events over gRPC.
 */

/**
 * Agent telemetry WebSocket client.
 *
 * Opens WS /ws/telemetry/{agentId} to receive real-time telemetry events
 * from the gateway. The gateway translates Protobuf events from the NATS bus
 * into JSON for the browser.
 */

export interface TelemetrySignal {
  name: string
  labels: string[]
  values: number[]
  unit: string
  frame?: string
}

/** interface `StatePayload` — Gateway client SDK contract type. */
export interface StatePayload {
  state_type: string
  signals: TelemetrySignal[]
  attributes?: Record<string, string>
}

/** interface `ActionPayload` — Gateway client SDK contract type. */
export interface ActionPayload {
  action_type: string
  signals: TelemetrySignal[]
  attributes?: Record<string, string>
}

/** interface `BlobRef` — Gateway client SDK contract type. */
export interface BlobRef {
  uri: string
  mime_type: string
  encoding: string
  width: number
  height: number
  frame_rate_hz?: number
  frame_index: number
  byte_length: number
  sha256?: string
  compression?: string
}

/** interface `VisionPayload` — Gateway client SDK contract type. */
export interface VisionPayload {
  blobs: BlobRef[]
  camera_name: string
  attributes?: Record<string, string>
}

/** interface `EventPayload` — Gateway client SDK contract type. */
export interface EventPayload {
  event_type: string
  severity: string
  message: string
  attributes?: Record<string, string>
}

/** interface `TelemetryEvent` — Gateway client SDK contract type. */
export interface TelemetryEvent {
  type: 'telemetry' | 'initial_state' | 'ping'
  agent_id: string
  modality?: string
  stream_name?: string
  event_time_ns?: string
  sequence_id?: string

  /** Monotonic per (agent_id, task_id) across all streams — the timestep axis
   *  for ML trajectory reconstruction and multi-stream alignment. */
  step_index?: string
  /** Producer identity (e.g. "requirements:journal") */
  source_id?: string
  /** Whether this event is a full snapshot or a delta/partial update */
  completeness?: 'FULL' | 'DELTA'
  /** True on the last step of an episode/task */
  done?: boolean
  /** Groups events across streams that share the same physical instant */
  sync_group?: string

  state?: StatePayload
  action?: ActionPayload
  vision?: VisionPayload
  event?: EventPayload
  streams?: Record<string, any>
}

/** interface `TelemetryCallbacks` — Gateway client SDK contract type. */
export interface TelemetryCallbacks {
  onState?: (event: TelemetryEvent) => void
  onAction?: (event: TelemetryEvent) => void
  onVision?: (event: TelemetryEvent) => void
  onEvent?: (event: TelemetryEvent) => void
  onInitialState?: (streams: Record<string, any>) => void
  onDisconnect?: () => void
  onConnect?: () => void
}

/** function `connectAgentTelemetry` — Gateway client SDK operation. */
export function connectAgentTelemetry(
  agentId: string,
  callbacks: TelemetryCallbacks,
  wsBaseUrl?: string,
): WebSocket {
  /** `base` — Gateway client SDK export. */
  const base = wsBaseUrl ?? ''
  /** `url` — Gateway client SDK export. */
  const url = `${base}/ws/telemetry/${encodeURIComponent(agentId)}`
  /** `ws` — Gateway client SDK export. */
  const ws = new WebSocket(url)

  ws.onopen = () => {
    callbacks.onConnect?.()
  }

  ws.onclose = () => {
    callbacks.onDisconnect?.()
  }

  ws.onmessage = (ev) => {
    try {
      /** `msg` — Gateway client SDK export. */
      const msg: TelemetryEvent = JSON.parse(ev.data)

      // Conditional branch for this Gateway client path.
      if (msg.type === 'ping') return

      // Conditional branch for this Gateway client path.
      if (msg.type === 'initial_state' && msg.streams) {
        callbacks.onInitialState?.(msg.streams)
        return
      }

      // Conditional branch for this Gateway client path.
      if (msg.type === 'telemetry') {
        /** `modality` — Gateway client SDK export. */
        const modality = msg.modality?.toLowerCase()
        // Conditional branch for this Gateway client path.
        if (modality === 'state' || modality === '1') {
          callbacks.onState?.(msg)
        } else if (modality === 'action' || modality === '2') {
          callbacks.onAction?.(msg)
        } else if (modality === 'vision' || modality === '3') {
          callbacks.onVision?.(msg)
        } else if (modality === 'event' || modality === '4') {
          callbacks.onEvent?.(msg)
        }
      }
    } catch {
      // ignore unparseable messages
    }
  }

  // Return this value to the Gateway client caller.
  return ws
}

/** `connectRobotTelemetry` — Gateway client SDK export. */
export const connectRobotTelemetry = connectAgentTelemetry
