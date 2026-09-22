/**
 * @fileoverview Modal dialog with backdrop, Escape-to-close, and body scroll lock.
 */

// ReactNode for body; useEffect for keydown + overflow side effects.
import { ReactNode, useEffect } from 'react'
// Close (X) icon in the header.
import { X } from 'lucide-react'
// Merge size + caller classes onto the panel.
import { cn } from '../../lib/utils'

/**
 * Props for {@link Modal}.
 */
interface ModalProps {
  /** When false, render nothing. */
  isOpen: boolean
  /** Called on backdrop click, Escape, or the X button. */
  onClose: () => void
  /** Text shown in the modal header. */
  title: string
  /** Modal body content. */
  children: ReactNode
  /** Extra classes on the panel (e.g. max-height). */
  className?: string
  /** Max-width token from sm → wide. */
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'wide'
}

/** Map size prop → Tailwind max-width utility. */
const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-3xl',
  '2xl': 'max-w-5xl',
  wide: 'max-w-7xl',
}

/**
 * Centered modal with dimmed backdrop and keyboard dismissal.
 *
 * @param props - Modal props.
 * @returns Portal-like fixed overlay, or null when closed.
 */
export function Modal({ isOpen, onClose, title, children, className, size = 'lg' }: ModalProps) {
  // While open: listen for Escape and lock document scroll; cleanup on close/unmount.
  useEffect(() => {
    /**
     * Close when the user presses Escape.
     * @param e - Keyboard event from document.
     */
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    // Only attach listeners / lock scroll while visible.
    if (isOpen) {
      document.addEventListener('keydown', handleEsc)
      // Prevent background page from scrolling under the dialog.
      document.body.style.overflow = 'hidden'
    }
    // Always remove listener and restore overflow on cleanup.
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  // Closed → render nothing (unmount children).
  if (!isOpen) return null

  return (
    // Full-viewport overlay stacking above page chrome (z-50).
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      {/* Backdrop — click dismisses the modal. */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal panel — relative so it stacks above the backdrop. */}
      <div
        className={cn(
          'relative bg-white border border-slate-200/70 rounded-2xl shadow-2xl w-full mx-4 animate-slide-up',
          sizeClasses[size],
          className
        )}
      >
        {/* Header with title + close button. */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded-lg hover:bg-slate-50 transition-colors duration-150"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content body with standard horizontal/vertical padding. */}
        <div className="px-6 py-5">
          {children}
        </div>
      </div>
    </div>
  )
}
