/**
 * @fileoverview Shared button primitive with variant and size tokens.
 */

// Button HTML attrs + ReactNode for children (icons + labels).
import { ReactNode, ButtonHTMLAttributes } from 'react'
// Merge variant/size classes with caller className.
import { cn } from '../../lib/utils'

/**
 * Props for {@link Button}; extends native button attributes.
 */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button contents (text and/or icons). */
  children: ReactNode
  /** Visual style: primary CTA, secondary outline, danger, or ghost. */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  /** Padding / type scale preset. */
  size?: 'sm' | 'md' | 'lg'
}

/**
 * Mission Control button with consistent focus, hover, and disabled styles.
 *
 * @param props - Button props including native button attributes.
 * @returns Styled `<button>` element.
 */
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
        // Base layout: inline flex, centered, rounded, fast transitions.
        'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-150',
        // Accessible cyan focus ring for keyboard users.
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40 focus-visible:ring-offset-2',
        // Primary: cyan gradient CTA.
        variant === 'primary' && 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-sm hover:shadow-md hover:from-cyan-500 hover:to-cyan-400 active:shadow-none',
        // Secondary: white with slate ring.
        variant === 'secondary' && 'bg-white text-slate-700 ring-1 ring-slate-200/80 hover:ring-slate-300 hover:text-slate-900 hover:shadow-sm',
        // Danger: soft red chip style.
        variant === 'danger' && 'bg-red-50 text-red-700 ring-1 ring-red-200/80 hover:bg-red-100',
        // Ghost: text-only until hover.
        variant === 'ghost' && 'text-slate-500 hover:text-slate-900 hover:bg-slate-50',
        // Size presets.
        size === 'sm' && 'px-2.5 py-1.5 text-xs',
        size === 'md' && 'px-3.5 py-2 text-sm',
        size === 'lg' && 'px-5 py-2.5 text-sm',
        // Disabled: fade and block pointer events.
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
