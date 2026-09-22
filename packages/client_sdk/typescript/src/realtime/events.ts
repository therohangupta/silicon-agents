/**
 * @file Discriminated union of Gateway WebSocket event payloads.
 *
 * Matches `client_sdk/contract/events.schema.json`. UI code switches on
 * `type` to invalidate queries, refresh task lists, or show connection state.
 */

import type { Task } from '../models/types'

/** type `GatewayRealtimeMessage` — Gateway client SDK contract type. */
export type GatewayRealtimeMessage =
  | { type: 'connected'; message: string }
  | { type: 'invalidate'; queries: string[]; timestamp: number }
  | { type: 'tasks_update'; plan_id: number; tasks: Task[] }
  // Future-proof: unknown messages pass through as generic objects
  | ({ type: string } & Record<string, any>)

