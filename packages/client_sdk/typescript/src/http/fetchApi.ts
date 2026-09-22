/**
 * @file Low-level `fetch` wrapper for Gateway REST calls.
 *
 * Centralizes base URL joining, JSON parsing, and error shaping so
 * `gatewayClient` methods stay thin. This is the HTTP transport half of
 * the client SDK — not the fleet_server gRPC client.
 */

export interface GatewayFetchOptions extends RequestInit {
  baseUrl?: string
}

/** function `fetchApi` — Gateway client SDK operation. */
export async function fetchApi<T>(endpoint: string, options?: GatewayFetchOptions): Promise<T> {
  /** `baseUrl` — Gateway client SDK export. */
  const baseUrl = options?.baseUrl ?? ''
  // Local `}` used by the surrounding Gateway client logic.
  const { headers: optHeaders, baseUrl: _ignored, ...restOptions } = options ?? {}
  /** `response` — Gateway client SDK export. */
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...restOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(optHeaders || {}),
    },
  })

  // Conditional branch for this Gateway client path.
  if (!response.ok) {
    /** `error` — Gateway client SDK export. */
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    // Surface the error to the UI or CLI caller.
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  // Return this value to the Gateway client caller.
  return response.json()
}

