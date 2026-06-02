import { ReactNode, ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40 focus-visible:ring-offset-2',
        variant === 'primary' && 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-sm hover:shadow-md hover:from-cyan-500 hover:to-cyan-400 active:shadow-none',
        variant === 'secondary' && 'bg-white text-slate-700 ring-1 ring-slate-200/80 hover:ring-slate-300 hover:text-slate-900 hover:shadow-sm',
        variant === 'danger' && 'bg-red-50 text-red-700 ring-1 ring-red-200/80 hover:bg-red-100',
        variant === 'ghost' && 'text-slate-500 hover:text-slate-900 hover:bg-slate-50',
        size === 'sm' && 'px-2.5 py-1.5 text-xs',
        size === 'md' && 'px-3.5 py-2 text-sm',
        size === 'lg' && 'px-5 py-2.5 text-sm',
        disabled && 'opacity-40 cursor-not-allowed pointer-events-none',
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
