/**
 * @file Gateway realtime WebSocket client.
 *
 * Subscribes to live control-plane events (invalidate, tasks_update,
 * connected, …). Reconnect and handler registration live here so React
 * hooks stay declarative.
 */

import type { GatewayRealtimeMessage } from './events'

/** interface `GatewayRealtimeClientOptions` — Gateway client SDK contract type. */
export interface GatewayRealtimeClientOptions {
  /** Example: "ws://localhost:8000" (no trailing slash). Empty string means relative WS URL. */
  wsBaseUrl?: string
}

/** class `GatewayRealtimeClient` — Gateway client SDK helper; see methods. */
export class GatewayRealtimeClient {
  private wsBaseUrl: string

  constructor(opts?: GatewayRealtimeClientOptions) {
    this.wsBaseUrl = opts?.wsBaseUrl ?? ''
  }

  connectGlobalUpdates(onMessage: (msg: GatewayRealtimeMessage) => void): WebSocket {
    /** `url` — Gateway client SDK export. */
    const url = `${this.wsBaseUrl}/ws/global-updates`
    /** `ws` — Gateway client SDK export. */
    const ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        onMessage(JSON.parse(ev.data))
      } catch {
        // ignore
      }
    }
    // Return this value to the Gateway client caller.
    return ws
  }

  connectPlanExecution(planId: number, onMessage: (msg: GatewayRealtimeMessage) => void): WebSocket {
    /** `url` — Gateway client SDK export. */
    const url = `${this.wsBaseUrl}/ws/execution/${planId}`
    /** `ws` — Gateway client SDK export. */
    const ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        onMessage(JSON.parse(ev.data))
      } catch {
        // ignore
      }
    }
    // Return this value to the Gateway client caller.
    return ws
  }
}

