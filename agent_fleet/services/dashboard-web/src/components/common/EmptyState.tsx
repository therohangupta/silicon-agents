/**
 * @fileoverview Centered empty-state placeholder with icon, copy, and optional CTA.
 */

// ReactNode for icon and optional action button cluster.
import { ReactNode } from 'react'
// Merge optional className onto the outer flex column.
import { cn } from '../../lib/utils'

/**
 * Props for {@link EmptyState}.
 */
interface EmptyStateProps {
  /** Decorative icon node (usually a Lucide icon). */
  icon: ReactNode
  /** Short heading describing the empty condition. */
  title: string
  /** Supporting sentence suggesting next steps. */
  description: string
  /** Optional primary action (e.g. Create Goal button). */
  action?: ReactNode
  /** Extra classes on the outer container. */
  className?: string
}

/**
 * Friendly empty placeholder used when lists or tabs have no data.
 *
 * @param props - EmptyState props.
 * @returns Centered empty-state block.
 */
export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    // Vertical stack centered in the available width.
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {/* Icon well. */}
      <div className="w-14 h-14 rounded-xl bg-slate-50 flex items-center justify-center mb-4 text-[var(--color-text-muted)]">
        {icon}
      </div>
      {/* Title. */}
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-1.5">{title}</h3>
      {/* Description capped for readability. */}
      <p className="text-sm text-[var(--color-text-secondary)] max-w-sm mb-5">{description}</p>
      {/* Optional CTA rendered as-is (usually a Button). */}
      {action}
    </div>
  )
}
