/**
 * @fileoverview Sticky top header that shows a human title for the current path.
 *
 * Note: Layout currently does not mount Header; it remains available for pages
 * or future chrome that want a secondary sticky title bar with the date.
 */

// Read the current location to map pathname → title.
import { useLocation } from 'react-router-dom'

/** Static map from top-level path to display title. */
const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/agents': 'Agent Management',
  '/goals': 'Goals',
  '/plans': 'Plan Builder',
  '/planners': 'Planners',
  '/allocators': 'Allocators',
}

/**
 * Compact sticky header with page title and today's formatted date.
 *
 * @returns Header element with title + date.
 */
export function Header() {
  // Current router location (pathname used for title lookup).
  const location = useLocation()
  // Fall back to Dashboard for nested paths not in the map (e.g. /plans/1).
  const title = pageTitles[location.pathname] || 'Dashboard'

  return (
    // Sticky translucent bar above page content.
    <header className="h-14 bg-surface/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-30">
      {/* Current section title. */}
      <h2 className="text-sm font-semibold text-[var(--color-text)] tracking-tight">{title}</h2>
      {/* Locale-formatted calendar date (static per render). */}
      <p className="text-xs text-[var(--color-text-muted)] font-mono tabular-nums">
        {new Date().toLocaleDateString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </p>
    </header>
  )
}
