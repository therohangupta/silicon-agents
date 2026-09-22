/**
 * @fileoverview Compact `#taskId` chip with optional hover tooltip showing task details.
 */

// Local tooltip open state + ref for the chip host (reserved for future positioning).
import { useState, useRef } from 'react'
// Class merge helper.
import { cn } from '../../lib/utils'
// Task type for optional tooltip payload.
import type { Task } from '../../types'

/**
 * Props for {@link TaskIdChip}.
 */
interface TaskIdChipProps {
  /** Numeric task id to display after `#`. */
  taskId: number
  /** Optional full task for tooltip contents. */
  task?: Task
  /** Extra classes on the outer relative span. */
  className?: string
  /** Optional color override for the chip text/border. */
  colorClass?: string
  /** If false, no hover popup (use in dense tables where details are already visible). Default true. */
  showTooltip?: boolean
}

/**
 * Monospace task id chip with optional rich hover tooltip.
 *
 * @param props - TaskIdChip props.
 * @returns Inline chip (and conditional tooltip).
 */
export function TaskIdChip({ taskId, task, className, colorClass, showTooltip = true }: TaskIdChipProps) {
  // Whether the tooltip is currently visible.
  const [tooltipOpen, setTooltipOpen] = useState(false)
  // Host element ref (available if we later pin tooltip to viewport).
  const chipRef = useRef<HTMLSpanElement>(null)

  // Status → text color for the tooltip status label.
  const statusColors: Record<string, string> = {
    completed: 'text-emerald-800',
    in_progress: 'text-amber-900',
    failed: 'text-red-800',
    pending: 'text-sky-900',
    cancelled: 'text-[var(--color-text-secondary)]',
    unknown: 'text-[var(--color-text-secondary)]',
  }

  return (
    // Relative host so the absolutely positioned tooltip anchors here.
    <span
      ref={chipRef}
      className={cn('relative inline-flex', className)}
      onMouseEnter={showTooltip ? () => setTooltipOpen(true) : undefined}
      onMouseLeave={showTooltip ? () => setTooltipOpen(false) : undefined}
    >
      {/* Visible chip label. */}
      <span
        className={cn(
          'px-1.5 py-0.5 rounded text-xs font-mono bg-slate-50 border border-slate-200',
          showTooltip && 'cursor-default hover:border-slate-300 transition-colors',
          colorClass
        )}
      >
        #{taskId}
      </span>

      {/* Hover tooltip — only when enabled, open, and task data exists. */}
      {showTooltip && tooltipOpen && task && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 pointer-events-none">
          {/* Raised panel matching modal shadow token. */}
          <div className="bg-surface-raised border border-slate-200 rounded-lg shadow-modal p-3 text-left">
            {/* Id + status row. */}
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-mono text-[var(--color-text-muted)]">Task #{taskId}</span>
              <span className={cn('text-xs font-medium', statusColors[task.status] || 'text-[var(--color-text-muted)]')}>
                {task.status.replace(/_/g, ' ')}
              </span>
            </div>
            {/* Description. */}
            <p className="text-sm text-[var(--color-text)] leading-snug mb-2">{task.description}</p>
            {/* Assigned agent when present. */}
            {task.agent_id && (
              <div className="text-xs text-slate-800 font-mono font-medium">@{task.agent_id}</div>
            )}
            {/* Required type when unallocated but typed. */}
            {task.agent_type && !task.agent_id && (
              <div className="text-xs text-[var(--color-text-secondary)]">Requires: {task.agent_type}</div>
            )}
            {/* Little caret pointing down at the chip. */}
            <div className="absolute left-1/2 -translate-x-1/2 top-full w-2 h-2 bg-surface-raised border-r border-b border-slate-200 rotate-45 -mt-1" />
          </div>
        </div>
      )}
    </span>
  )
}
