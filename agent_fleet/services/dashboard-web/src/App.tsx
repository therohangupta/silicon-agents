/**
 * @fileoverview Root application component for Mission Control.
 *
 * On startup this component:
 * - Subscribes to gateway WebSocket invalidation via `useRealtimeUpdates`.
 * - Loads planner/allocator method summaries from the Methods API and seeds
 *   the in-memory name lookup store (`setMethodData`) used across Plans/Goals UI.
 * - Blocks the route tree behind a loading gate until methods resolve (or fail).
 * - Renders the shared Layout and React Router route table.
 */

// Declarative route matching and a catch-all redirect for unknown paths.
import { Routes, Route, Navigate } from 'react-router-dom'
// Effect for one-shot method preload; state for the loading gate.
import { useEffect, useState } from 'react'
// Persistent sidebar + main content margin shell.
import { Layout } from './components/layout/Layout'
// Home overview: fleet stats and recent tasks.
import { Dashboard } from './pages/Dashboard'
// Agent inventory / health / registration (owned by another doc task for comments).
import { Agents } from './pages/Agents'
// Goal create / search / detail modal page.
import { Goals } from './pages/Goals'
// Plan list and create flows (comments owned by another task).
import { Plans } from './pages/Plans'
// Single-plan deep dive (comments owned by another task).
import PlanDetails from './pages/PlanDetails'
// Live plan execution monitor (comments owned by another task).
import { Execution } from './pages/Execution'
// Catalog of planning methods (prompts, types).
import { Planners } from './pages/Planners'
// Catalog of allocation methods (prompts, types).
import { Allocators } from './pages/Allocators'
// Methods REST client + realtime invalidation hook.
import { methodsApi, useRealtimeUpdates } from './lib/api'
// Seeds planner/allocator display-name maps used by strategy chips.
import { setMethodData } from './lib/utils'

/**
 * Top-level React component mounted by `main.tsx`.
 *
 * @returns Either a full-screen method-loading gate or the Layout + Routes tree.
 */
function App() {
  // Connect (once per mount) to the gateway global-updates WebSocket and invalidate
  // TanStack Query keys when the server broadcasts `{ type: 'invalidate', queries }`.
  useRealtimeUpdates()

  // Gate flag: false until method YAML summaries are loaded (or the load attempt fails).
  const [methodsLoaded, setMethodsLoaded] = useState(false)

  // Load method data synchronously on app startup — block rendering until loaded
  // so strategy name helpers never briefly show "Strategy N" placeholders.
  useEffect(() => {
    /**
     * Fetch all methods, partition planners vs allocators, and seed utils lookups.
     * Errors are logged but still flip `methodsLoaded` so the UI is not stuck forever.
     */
    const loadMethodData = async () => {
      try {
        // Helpful console breadcrumb for operators debugging empty strategy chips.
        console.log('Loading method data from YAML files...')
        // Hit gateway Methods API (list of summaries from server-side YAML configs).
        const methods = await methodsApi.list()
        // Planners define how goals become task DAGs.
        const planners = methods.filter(m => m.category === 'planner')
        // Allocators define how tasks map onto agents.
        const allocators = methods.filter(m => m.category === 'allocator')
        // Populate module-level maps used by getPlanningStrategyName / getAllocationStrategyName.
        setMethodData(planners, allocators)
        // Log counts and ids so a missing YAML file is obvious in the console.
        console.log('Method data loaded from YAML files:', {
          planners: planners.length,
          allocators: allocators.length,
          plannerNames: planners.map(p => `${p.id}: ${p.name}`),
          allocatorNames: allocators.map(a => `${a.id}: ${a.name}`)
        })
        // Unlock the route tree.
        setMethodsLoaded(true)
      } catch (error) {
        // Network / gateway failure — surface in console for debugging.
        console.error('Failed to load method data from YAML files:', error)
        // Still set loaded to true to avoid infinite loading, but log error
        setMethodsLoaded(true)
      }
    }

    // Fire-and-forget async loader; empty deps = once on mount.
    loadMethodData()
  }, [])

  // Show loading screen until method data is loaded
  if (!methodsLoaded) {
    return (
      // Full-viewport centered gate matching the app background token.
      <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center">
        {/* Stack spinner + caption. */}
        <div className="text-center">
          {/* Cyan spinning ring — visual “still booting” affordance. */}
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          {/* Explain why the UI is blank so users do not refresh prematurely. */}
          <p className="text-[var(--color-text-secondary)]">Loading method configurations...</p>
        </div>
      </div>
    )
  }

  // Methods ready — render chrome + routes.
  return (
    <Layout>
      {/* React Router v6 route table; first match wins. */}
      <Routes>
        {/* Mission Control home. */}
        <Route path="/" element={<Dashboard />} />
        {/* Agent fleet management. */}
        <Route path="/agents" element={<Agents />} />
        {/* Goal CRUD and details. */}
        <Route path="/goals" element={<Goals />} />
        {/* Plan index / create. */}
        <Route path="/plans" element={<Plans />} />
        {/* Plan detail (tabs: overview, tasks, DAG, artifacts). */}
        <Route path="/plans/:planId" element={<PlanDetails />} />
        {/* Live execution view for a plan. */}
        <Route path="/plans/:planId/execute" element={<Execution />} />
        {/* Planner method catalog. */}
        <Route path="/planners" element={<Planners />} />
        {/* Allocator method catalog. */}
        <Route path="/allocators" element={<Allocators />} />
        {/* Unknown paths bounce home without pushing an extra history entry. */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

// Default export expected by main.tsx import.
export default App
