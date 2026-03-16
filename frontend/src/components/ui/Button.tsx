'use client'

import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { Loader2 } from 'lucide-react'
import { ButtonHTMLAttributes, forwardRef } from 'react'

type Variant = 'gradient' | 'ghost' | 'glass'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  fullWidth?: boolean
}

const base =
  'inline-flex items-center justify-center gap-2 font-semibold rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-purple/50 disabled:opacity-50 disabled:cursor-not-allowed select-none relative overflow-hidden'

const variants: Record<Variant, string> = {
  gradient:
    'bg-gradient-to-r from-brand-purple to-brand-blue text-white hover:from-brand-violet hover:to-brand-electric shadow-glow-sm hover:shadow-glow-md',
  ghost:
    'border border-white/20 text-void-200 hover:border-brand-purple/60 hover:text-white hover:bg-brand-purple/10',
  glass:
    'glass text-void-200 hover:bg-white/10 hover:border-brand-purple/40 hover:text-white border border-white/10',
}

const sizes: Record<Size, string> = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-sm',
  lg: 'px-8 py-4 text-base',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'gradient', size = 'md', loading = false, fullWidth = false, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={twMerge(
          clsx(base, variants[variant], sizes[size], fullWidth && 'w-full', className)
        )}
        {...props}
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
