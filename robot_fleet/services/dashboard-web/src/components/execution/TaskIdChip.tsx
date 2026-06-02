import { useState, useRef } from 'react'
import { cn } from '../../lib/utils'
import type { Task } from '../../types'

interface TaskIdChipProps {
  taskId: number
  task?: Task
  className?: string
  colorClass?: string
  /** If false, no hover popup (use in dense tables where details are already visible). Default true. */
  showTooltip?: boolean
}

export function TaskIdChip({ taskId, task, className, colorClass, showTooltip = true }: TaskIdChipProps) {
  const [tooltipOpen, setTooltipOpen] = useState(false)
  const chipRef = useRef<HTMLSpanElement>(null)

  const statusColors: Record<string, string> = {
    completed: 'text-emerald-800',
    in_progress: 'text-amber-900',
    failed: 'text-red-800',
    pending: 'text-sky-900',
    cancelled: 'text-[var(--color-text-secondary)]',
    unknown: 'text-[var(--color-text-secondary)]',
  }

  return (
    <span
      ref={chipRef}
      className={cn('relative inline-flex', className)}
      onMouseEnter={showTooltip ? () => setTooltipOpen(true) : undefined}
      onMouseLeave={showTooltip ? () => setTooltipOpen(false) : undefined}
    >
      <span
        className={cn(
          'px-1.5 py-0.5 rounded text-xs font-mono bg-slate-50 border border-slate-200',
          showTooltip && 'cursor-default hover:border-slate-300 transition-colors',
          colorClass
        )}
      >
        #{taskId}
      </span>

      {showTooltip && tooltipOpen && task && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 pointer-events-none">
          <div className="bg-surface-raised border border-slate-200 rounded-lg shadow-modal p-3 text-left">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-mono text-[var(--color-text-muted)]">Task #{taskId}</span>
              <span className={cn('text-xs font-medium', statusColors[task.status] || 'text-[var(--color-text-muted)]')}>
                {task.status.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-sm text-[var(--color-text)] leading-snug mb-2">{task.description}</p>
            {task.robot_id && (
              <div className="text-xs text-slate-800 font-mono font-medium">@{task.robot_id}</div>
            )}
            {task.robot_type && !task.robot_id && (
              <div className="text-xs text-[var(--color-text-secondary)]">Requires: {task.robot_type}</div>
            )}
            <div className="absolute left-1/2 -translate-x-1/2 top-full w-2 h-2 bg-surface-raised border-r border-b border-slate-200 rotate-45 -mt-1" />
          </div>
        </div>
      )}
    </span>
  )
}
