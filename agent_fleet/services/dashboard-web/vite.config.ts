/**
 * @fileoverview Vite build and dev-server configuration for the Agent Fleet dashboard.
 *
 * This file is loaded by the Vite CLI (`vite`, `vite build`, `vite preview`) and by
 * TypeScript via `tsconfig.node.json`. It wires React Fast Refresh, path aliases that
 * match `tsconfig.json`, and HTTP/WebSocket proxies so the SPA can call the gateway
 * on port 8000 without CORS issues during local development.
 */

// Named helper that validates and types the exported Vite config object.
import { defineConfig } from 'vite'
// Official Vite plugin that enables JSX transform and HMR for React components.
import react from '@vitejs/plugin-react'
// Node.js path utilities used to resolve absolute alias targets from __dirname.
import path from 'path'

/**
 * Default export consumed by Vite.
 * @returns A fully typed Vite UserConfig for this package.
 */
export default defineConfig({
  // Register plugins that run during transform / serve / build.
  plugins: [
    // Enable React JSX runtime and hot module replacement for .tsx/.jsx files.
    react(),
  ],
  // Module resolution options shared by the bundler and the Vite SSR/deps optimizer.
  resolve: {
    // Map import prefixes to filesystem locations so we can avoid deep relative paths.
    alias: {
      // `@/…` → `src/…` (mirrors the TypeScript path mapping in tsconfig.json).
      '@': path.resolve(__dirname, './src'),
      // Point the published package name at the TypeScript source of the local client SDK
      // so Vite can tree-shake and HMR the SDK without publishing a build artifact first.
      '@agent-fleet/client-sdk': path.resolve(__dirname, '../../packages/client_sdk/typescript/src/index.ts'),
    },
  },
  // Dev-server-only settings (ignored for production `vite build` output).
  server: {
    // Bind the SPA to a fixed port so docs and bookmarks stay stable.
    port: 5173,
    // Forward browser requests that target the gateway API / realtime endpoints.
    proxy: {
      // REST and other HTTP traffic under `/api/*` goes to the local gateway process.
      '/api': {
        // Gateway HTTP listen address (same host the dashboard expects in prod behind nginx).
        target: 'http://127.0.0.1:8000',
        // Rewrite the Host header so the upstream sees the gateway origin, not localhost:5173.
        changeOrigin: true,
      },
      // WebSocket upgrade path used for fleet-wide invalidation and telemetry streams.
      '/ws': {
        // Use the `ws:` scheme so Vite upgrades the connection correctly.
        target: 'ws://127.0.0.1:8000',
        // Explicitly enable WebSocket proxying (required for realtime features).
        ws: true,
      },
    },
  },
})
