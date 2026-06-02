import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface CardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  onClick?: () => void
}

export function Card({ children, className, hover = false, onClick }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white/90 backdrop-blur-sm border border-slate-200/70 rounded-xl p-5',
        'shadow-[0_1px_3px_rgba(15,23,42,0.04),0_4px_14px_rgba(15,23,42,0.03)]',
        'transition-all duration-200',
        hover && 'card-hover cursor-pointer hover:border-cyan-300/50 hover:shadow-[0_8px_30px_rgba(8,145,178,0.08)]',
        onClick && !hover && 'cursor-pointer hover:border-slate-300/90 hover:shadow-md',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  label?: string
  action?: ReactNode
}

export function CardHeader({ title, subtitle, label, action }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-4 gap-4">
      <div className="min-w-0">
        {label && (
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-700/70 font-mono mb-1.5">
            {label}
          </p>
        )}
        <h3 className="text-base font-semibold text-slate-900 tracking-tight">{title}</h3>
        {subtitle && (
          <p className="text-sm text-slate-500 mt-1 leading-relaxed">{subtitle}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
