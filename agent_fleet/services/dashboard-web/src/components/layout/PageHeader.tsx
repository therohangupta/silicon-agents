/**
 * @fileoverview Shared page title row used at the top of most Mission Control pages.
 *
 * Supports optional leading slot (back button / icon), meta (counts), description,
 * and a right-aligned actions cluster (primary buttons).
 */

// ReactNode allows string or rich JSX for title / description / actions.
import { ReactNode } from 'react'
// Class merge for optional outer className.
import { cn } from '../../lib/utils'

/**
 * Props for {@link PageHeader}.
 */
export interface PageHeaderProps {
  /** Primary heading (string or JSX, e.g. with gradient spans). */
  title: ReactNode
  /** Optional supporting sentence under the title. */
  description?: ReactNode
  /** Optional count / filter meta shown beside the title. */
  meta?: ReactNode
  /** Optional leading control (e.g. back chevron). */
  leading?: ReactNode
  /** Optional right-side action buttons. */
  actions?: ReactNode
  /** Extra classes on the outer `<header>`. */
  className?: string
}

/**
 * Consistent page heading block with optional meta and actions.
 *
 * @param props - PageHeader props.
 * @returns Header markup for the top of a page.
 */
export function PageHeader({
  title,
  description,
  meta,
  leading,
  actions,
  className,
}: PageHeaderProps) {
  return (
    // Outer header with small bottom margin before page body content.
    <header className={cn('mb-2', className)}>
      {/* Stack on mobile; row with space-between on sm+. */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        {/* Left cluster: leading + title block. */}
        <div className={cn('flex items-start gap-3 min-w-0 flex-1')}>
          {/* Optional leading slot (back button, avatar, etc.). */}
          {leading}
          {/* Title / meta / description column; min-w-0 enables truncation. */}
          <div className="min-w-0 flex-1">
            {/* Title + optional meta baseline-aligned. */}
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              {/* Gradient clipped heading matching Mission Control branding. */}
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-slate-900 via-cyan-800 to-slate-700 bg-clip-text text-transparent">
                {title}
              </h1>
              {/* Optional meta (e.g. “12 of 40”). */}
              {meta && (
                <span className="text-sm font-medium text-slate-400 tabular-nums">
                  {meta}
                </span>
              )}
            </div>
            {/* Optional description under the title row. */}
            {description && (
              <p className="text-sm text-slate-500 mt-1">{description}</p>
            )}
          </div>
        </div>
        {/* Right-aligned action buttons when provided. */}
        {actions && (
          <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>
        )}
      </div>
    </header>
  )
}
