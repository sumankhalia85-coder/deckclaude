'use client'

import { motion } from 'framer-motion'
import { Zap, ClipboardList, Upload } from 'lucide-react'

type Mode = 'prompt' | 'form' | 'upload'

interface ModeSelectorProps {
  active: Mode
  onChange: (mode: Mode) => void
}

const MODES: { id: Mode; label: string; Icon: typeof Zap; description: string }[] = [
  { id: 'prompt', label: 'Prompt', Icon: Zap, description: 'Natural language' },
  { id: 'form', label: 'Form', Icon: ClipboardList, description: 'Structured input' },
  { id: 'upload', label: 'Upload', Icon: Upload, description: 'File-based' },
]

export default function ModeSelector({ active, onChange }: ModeSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-2 p-1.5 glass rounded-2xl border border-white/8 w-full max-w-4xl mx-auto mb-10">
      {MODES.map(({ id, label, Icon, description }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          className="relative flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 w-full"
        >
          {active === id && (
            <motion.div
              layoutId="mode-pill"
              className="absolute inset-0 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 shadow-glow-sm"
              transition={{ type: 'spring', bounce: 0.15, duration: 0.4 }}
            />
          )}
          <span className={`relative z-10 flex items-center gap-2 transition-colors ${active === id ? 'text-white' : 'text-void-400 hover:text-void-200'}`}>
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span className="flex items-center gap-1.5 flex-wrap">
              <span>{label}</span>
              <span className={`text-[11px] font-normal hidden md:inline opacity-70`}>
                — {description}
              </span>
            </span>
          </span>
        </button>
      ))}
    </div>
  )
}
