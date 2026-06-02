import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

export interface PageHeaderProps {
  title: ReactNode
  description?: ReactNode
  meta?: ReactNode
  leading?: ReactNode
  actions?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  description,
  meta,
  leading,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn('mb-2', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className={cn('flex items-start gap-3 min-w-0 flex-1')}>
          {leading}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-slate-900 via-cyan-800 to-slate-700 bg-clip-text text-transparent">
                {title}
              </h1>
              {meta && (
                <span className="text-sm font-medium text-slate-400 tabular-nums">
                  {meta}
                </span>
              )}
            </div>
            {description && (
              <p className="text-sm text-slate-500 mt-1">{description}</p>
            )}
          </div>
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>
        )}
      </div>
    </header>
  )
}
