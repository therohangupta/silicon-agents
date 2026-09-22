/**
 * @fileoverview Frosted white card surface and optional CardHeader for titled sections.
 */

// ReactNode for arbitrary card body / header actions.
import { ReactNode } from 'react'
// Merge base card styles with caller overrides.
import { cn } from '../../lib/utils'

/**
 * Props for {@link Card}.
 */
interface CardProps {
  /** Card body content. */
  children: ReactNode
  /** Extra Tailwind classes merged onto the root. */
  className?: string
  /** When true, apply lift-on-hover (`.card-hover`) and pointer cursor. */
  hover?: boolean
  /** Optional click handler (also enables pointer cursor when hover is false). */
  onClick?: () => void
}

/**
 * Elevated panel used across dashboards, lists, and modals.
 *
 * @param props - Card props.
 * @returns Styled div wrapping children.
 */
export function Card({ children, className, hover = false, onClick }: CardProps) {
  return (
    <div
      className={cn(
        // Frosted white surface with soft border and padding.
        'bg-white/90 backdrop-blur-sm border border-slate-200/70 rounded-xl p-5',
        // Resting multi-layer slate shadow.
        'shadow-[0_1px_3px_rgba(15,23,42,0.04),0_4px_14px_rgba(15,23,42,0.03)]',
        // Smooth transitions for hover affordances.
        'transition-all duration-200',
        // Optional interactive lift + cyan border hint.
        hover && 'card-hover cursor-pointer hover:border-cyan-300/50 hover:shadow-[0_8px_30px_rgba(8,145,178,0.08)]',
        // Clickable without full hover lift still gets a lighter hover.
        onClick && !hover && 'cursor-pointer hover:border-slate-300/90 hover:shadow-md',
        // Caller overrides last.
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

/**
 * Props for {@link CardHeader}.
 */
interface CardHeaderProps {
  /** Primary card title. */
  title: string
  /** Optional subtitle under the title. */
  subtitle?: string
  /** Optional uppercase mono eyebrow label. */
  label?: string
  /** Optional right-aligned action node (button, menu). */
  action?: ReactNode
}

/**
 * Standard title row for cards with optional eyebrow, subtitle, and action.
 *
 * @param props - CardHeader props.
 * @returns Header flex row.
 */
export function CardHeader({ title, subtitle, label, action }: CardHeaderProps) {
  return (
    // Space title block from body; gap keeps action from colliding.
    <div className="flex items-start justify-between mb-4 gap-4">
      {/* Left text stack; min-w-0 allows truncation in flex layouts. */}
      <div className="min-w-0">
        {/* Optional eyebrow label (section kicker). */}
        {label && (
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-700/70 font-mono mb-1.5">
            {label}
          </p>
        )}
        {/* Card title. */}
        <h3 className="text-base font-semibold text-slate-900 tracking-tight">{title}</h3>
        {/* Optional supporting subtitle. */}
        {subtitle && (
          <p className="text-sm text-slate-500 mt-1 leading-relaxed">{subtitle}</p>
        )}
      </div>
      {/* Optional action aligned to the top-right. */}
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
