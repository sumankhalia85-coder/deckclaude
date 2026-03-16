import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { HTMLAttributes, forwardRef } from 'react'

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: boolean
  hover?: boolean
  gradient?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ glow = false, hover = false, gradient = false, padding = 'md', className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={twMerge(
          clsx(
            'glass rounded-2xl',
            paddings[padding],
            hover && 'glass-hover cursor-pointer',
            glow && 'shadow-glow-sm',
            gradient && 'bg-gradient-to-br from-brand-purple/10 to-brand-blue/5',
            className
          )
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

GlassCard.displayName = 'GlassCard'
export default GlassCard
