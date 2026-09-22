/**
 * @file `@agent-fleet/client-sdk` public barrel.
 *
 * Re-exports the Gateway HTTP client, typed models, realtime WebSocket
 * helpers, event unions, and the telemetry realtime client used by
 * `dashboard-web`. Import from this package rather than deep paths so the
 * Gateway contract stays the only client-facing API surface.
 */

export * from './models/types'
export * from './http/gatewayClient'
export * from './realtime/events'
export * from './realtime/wsClient'
export * from './realtime/telemetryClient'

