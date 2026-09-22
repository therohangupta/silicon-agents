/**
 * @fileoverview Browser bootstrap entry for the Agent Fleet dashboard SPA.
 *
 * Responsibilities:
 * 1. Create a shared TanStack Query client (server-state cache + invalidation).
 * 2. Mount React under `#root` with StrictMode, QueryClientProvider, and BrowserRouter.
 * 3. Import global styles (`index.css`) so Tailwind + design tokens apply app-wide.
 *
 * This module is referenced from `index.html` as `/src/main.tsx`.
 */

// React core — needed for StrictMode wrapper around the tree.
import React from 'react'
// React 18 concurrent root API (createRoot replaces the legacy ReactDOM.render).
import ReactDOM from 'react-dom/client'
// TanStack Query provider + client factory for REST cache / mutations.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
// HTML5 history router so route components (Dashboard, Goals, …) sync with the URL.
import { BrowserRouter } from 'react-router-dom'
// Top-level route tree, method preload gate, and layout shell.
import App from './App'
// Global CSS: Tailwind layers, design tokens, scrollbar, React Flow overrides.
import './index.css'

/**
 * Shared QueryClient used by every `useQuery` / `useMutation` in the app.
 * `staleTime: 2000` keeps list views from thrashing the gateway on rapid remounts
 * while still refreshing quickly when realtime invalidation fires.
 */
const queryClient = new QueryClient({
  // Default options applied unless a call site overrides them.
  defaultOptions: {
    // Defaults for all queries (agents, goals, plans, methods, …).
    queries: {
      // Consider cached data fresh for 2 seconds before a background refetch is allowed.
      staleTime: 2000,
    },
  },
})

/**
 * Mount the React application into the `#root` element from index.html.
 * Non-null assertion is safe because the shell always defines that node.
 */
ReactDOM.createRoot(document.getElementById('root')!).render(
  // StrictMode double-invokes effects in development to surface impure side effects.
  <React.StrictMode>
    {/* Make the QueryClient available to all descendants via context. */}
    <QueryClientProvider client={queryClient}>
      {/* Enable client-side routing with the browser History API. */}
      <BrowserRouter>
        {/* App owns routes, method preload, and the Layout chrome. */}
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
