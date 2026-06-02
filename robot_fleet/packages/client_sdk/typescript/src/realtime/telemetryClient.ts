/**
 * Robot telemetry WebSocket client.
 *
 * Opens WS /ws/telemetry/{robotId} to receive real-time telemetry events
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

export interface StatePayload {
  state_type: string
  signals: TelemetrySignal[]
  attributes?: Record<string, string>
}

export interface ActionPayload {
  action_type: string
  signals: TelemetrySignal[]
  attributes?: Record<string, string>
}

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

export interface VisionPayload {
  blobs: BlobRef[]
  camera_name: string
  attributes?: Record<string, string>
}

export interface EventPayload {
  event_type: string
  severity: string
  message: string
  attributes?: Record<string, string>
}

export interface TelemetryEvent {
  type: 'telemetry' | 'initial_state' | 'ping'
  robot_id: string
  modality?: string
  stream_name?: string
  event_time_ns?: string
  sequence_id?: string

  /** Monotonic per (robot_id, task_id) across all streams — the timestep axis
   *  for ML trajectory reconstruction and multi-stream alignment. */
  step_index?: string
  /** Producer identity (e.g. "moma-1:joint_adapter") */
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

export interface TelemetryCallbacks {
  onState?: (event: TelemetryEvent) => void
  onAction?: (event: TelemetryEvent) => void
  onVision?: (event: TelemetryEvent) => void
  onEvent?: (event: TelemetryEvent) => void
  onInitialState?: (streams: Record<string, any>) => void
  onDisconnect?: () => void
  onConnect?: () => void
}

export function connectRobotTelemetry(
  robotId: string,
  callbacks: TelemetryCallbacks,
  wsBaseUrl?: string,
): WebSocket {
  const base = wsBaseUrl ?? ''
  const url = `${base}/ws/telemetry/${encodeURIComponent(robotId)}`
  const ws = new WebSocket(url)

  ws.onopen = () => {
    callbacks.onConnect?.()
  }

  ws.onclose = () => {
    callbacks.onDisconnect?.()
  }

  ws.onmessage = (ev) => {
    try {
      const msg: TelemetryEvent = JSON.parse(ev.data)

      if (msg.type === 'ping') return

      if (msg.type === 'initial_state' && msg.streams) {
        callbacks.onInitialState?.(msg.streams)
        return
      }

      if (msg.type === 'telemetry') {
        const modality = msg.modality?.toLowerCase()
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

  return ws
}
