/**
 * @fileoverview Fixed left navigation rail for Mission Control.
 *
 * Supports collapsed (icon-only, 3.5rem) and expanded (14rem) widths, brand mark,
 * NavLink active styling, a decorative “System Online” status card, and a
 * collapse toggle wired to Layout’s localStorage-backed state.
 */

// Active-aware link component from React Router.
import { NavLink } from 'react-router-dom'
// Lucide icons for each nav destination and collapse controls.
import {
  Home,
  Bot,
  Target,
  GitBranch,
  FileText,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'
// Tailwind class merge helper.
import { cn } from '../../lib/utils'

/** Ordered primary navigation entries. */
const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Goals', href: '/goals', icon: Target },
  { name: 'Plans', href: '/plans', icon: GitBranch },
  { name: 'Planners', href: '/planners', icon: FileText },
  { name: 'Allocators', href: '/allocators', icon: Network },
]

/**
 * Props for {@link Sidebar}.
 */
interface SidebarProps {
  /** When true, render the narrow icon-only rail. */
  collapsed: boolean
  /** Invoked when the user clicks the collapse / expand control. */
  onToggle: () => void
}

/**
 * Fixed dark sidebar with brand, nav links, status, and collapse control.
 *
 * @param props - Sidebar props.
 * @returns Aside element fixed to the left of the viewport.
 */
export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    // Fixed full-height rail; width animates between collapsed and expanded.
    <aside
      className={cn(
        'fixed left-0 top-0 h-full z-40 flex flex-col transition-[width] duration-200 ease-out',
        'bg-slate-900 text-slate-300',
        collapsed ? 'w-14' : 'w-56'
      )}
    >
      {/* Logo / brand row */}
      <div className="h-14 flex items-center border-b border-slate-800 shrink-0 px-3">
        {collapsed ? (
          // Collapsed: only the gradient bot mark, centered.
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 mx-auto">
            <Bot className="w-4 h-4 text-white" />
          </div>
        ) : (
          // Expanded: mark + wordmark + “Mission Control” subtitle.
          <div className="flex items-center gap-2.5 px-1">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="overflow-hidden">
              <h1 className="text-sm font-bold text-white leading-tight whitespace-nowrap tracking-tight">Agent Fleet</h1>
              <p className="text-[10px] text-slate-500 font-mono uppercase tracking-[0.2em] whitespace-nowrap">
                Mission Control
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Primary navigation links */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto overflow-x-hidden">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            // Native tooltip when labels are hidden in collapsed mode.
            title={collapsed ? item.name : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 rounded-lg text-[13px] font-medium transition-all duration-150',
                // Center icons when collapsed; pad when expanded.
                collapsed ? 'justify-center px-0 py-2.5' : 'px-3 py-2.5',
                // Active: cyan/violet wash + left accent bar.
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/15 to-violet-500/10 text-white border-l-2 border-l-cyan-400 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]'
                  : 'text-slate-400 hover:text-white hover:bg-white/5 border-l-2 border-l-transparent'
              )
            }
          >
            {/* Destination icon. */}
            <item.icon className="w-[18px] h-[18px] shrink-0" />
            {/* Label only when expanded. */}
            {!collapsed && <span className="truncate">{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle + optional system status card */}
      <div className="px-2 pb-3 pt-2 border-t border-slate-800 shrink-0 space-y-2">
        {!collapsed && (
          // Decorative online indicator + fleet manager address hint.
          <div className="bg-slate-800/60 rounded-lg p-3 mx-1 ring-1 ring-slate-700/50">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_rgba(52,211,153,0.5)]" />
              <span>System Online</span>
            </div>
            <p className="text-[10px] text-slate-600 font-mono mt-1.5">
              Fleet Manager: localhost:50051
            </p>
          </div>
        )}
        {/* Collapse / expand control. */}
        <button
          onClick={onToggle}
          className={cn(
            'flex items-center gap-2 rounded-lg text-[13px] text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-colors duration-150 w-full',
            collapsed ? 'justify-center px-0 py-2' : 'px-4 py-2'
          )}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed
            ? <PanelLeftOpen className="w-[18px] h-[18px]" />
            : <>
                <PanelLeftClose className="w-[18px] h-[18px]" />
                <span>Collapse</span>
              </>
          }
        </button>
      </div>
    </aside>
  )
}
