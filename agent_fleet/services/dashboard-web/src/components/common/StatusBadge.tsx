/**
 * @fileoverview Compact status chip that colors itself from {@link getStatusBgColor}.
 */

// Class merge + shared status → chip color mapping.
import { cn, getStatusBgColor } from '../../lib/utils'

/**
 * Props for {@link StatusBadge}.
 */
interface StatusBadgeProps {
  /** Raw status string (underscores shown as spaces). */
  status: string
  /** Extra classes for layout overrides. */
  className?: string
}

/**
 * Pill badge showing a humanized status with tonal colors.
 *
 * @param props - StatusBadge props.
 * @returns Inline span chip.
 */
export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        // Base pill geometry and type.
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
        // Status-driven background / text / ring.
        getStatusBgColor(status),
        className
      )}
    >
      {/* Replace underscores for display (in_progress → in progress). */}
      {status.replace(/_/g, ' ')}
    </span>
  )
}
