/**
 * @fileoverview Application chrome: fixed sidebar + main content margin that
 * tracks the sidebar collapsed width. Persists collapse preference in localStorage.
 */

// ReactNode for children; state + effect for collapse persistence.
import { ReactNode, useState, useEffect } from 'react'
// Left navigation rail with collapse toggle.
import { Sidebar } from './Sidebar'

/**
 * Props for {@link Layout}.
 */
interface LayoutProps {
  /** Page content rendered inside the padded `<main>` region. */
  children: ReactNode
}

/** localStorage key storing `"1"` (collapsed) or `"0"` (expanded). */
const SIDEBAR_KEY = 'rf-sidebar-collapsed'

/**
 * Shell wrapping every authenticated route: sidebar + scrolling main column.
 *
 * @param props - Layout props.
 * @param props.children - Active page element from React Router.
 * @returns Full-height mission shell with sidebar and main.
 */
export function Layout({ children }: LayoutProps) {
  // Initialize from localStorage when available; default expanded on failure / SSR.
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(SIDEBAR_KEY) === '1' } catch { return false }
  })

  // Persist collapse preference whenever it changes.
  useEffect(() => {
    try { localStorage.setItem(SIDEBAR_KEY, collapsed ? '1' : '0') } catch {}
  }, [collapsed])

  return (
    // Full viewport height with mission background token helper class.
    <div className="min-h-screen mission-shell-bg">
      {/* Horizontal flex: fixed sidebar + flowing content. */}
      <div className="flex relative">
        {/* Fixed left nav; toggle flips collapsed state. */}
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
        {/* Content column; margin mirrors sidebar width (56 collapsed / 224 expanded). */}
        <div
          className="flex-1 transition-[margin] duration-200 ease-out"
          style={{ marginLeft: collapsed ? 56 : 224 }}
        >
          {/* Padded main region where route pages render. */}
          <main className="px-8 py-6 min-h-screen">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
