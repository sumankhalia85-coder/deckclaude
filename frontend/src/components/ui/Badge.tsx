import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { HTMLAttributes } from 'react'

type BadgeColor = 'purple' | 'blue' | 'green' | 'orange' | 'red' | 'ghost'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor
}

const colorMap: Record<BadgeColor, string> = {
  purple: 'bg-brand-purple/20 border-brand-purple/40 text-brand-violet',
  blue: 'bg-brand-blue/20 border-brand-blue/40 text-brand-electric',
  green: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
  orange: 'bg-orange-500/15 border-orange-500/30 text-orange-400',
  red: 'bg-red-500/15 border-red-500/30 text-red-400',
  ghost: 'bg-white/5 border-white/10 text-void-300',
}

export default function Badge({ color = 'purple', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border',
          colorMap[color],
          className
        )
      )}
      {...props}
    >
      {children}
    </span>
  )
}
