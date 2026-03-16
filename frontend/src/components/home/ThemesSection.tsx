'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { THEMES } from '@/lib/constants'

function MockSlidePreview({ theme }: { theme: typeof THEMES[0] }) {
  const bars = [65, 80, 45, 90, 55, 70]

  return (
    <motion.div
      key={theme.value}
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.25 }}
      className="w-full rounded-2xl overflow-hidden border border-white/10 shadow-glass"
      style={{ aspectRatio: '16/9', background: theme.secondary }}
    >
      {/* Title bar */}
      <div className="h-14 flex items-center px-6 gap-3" style={{ background: theme.primary }}>
        <div className="w-2 h-6 rounded-sm" style={{ background: theme.accent }} />
        <div>
          <div className="h-3 w-40 rounded-full" style={{ background: theme.accent + 'cc' }} />
          <div className="h-2 w-24 rounded-full mt-1.5 opacity-40" style={{ background: '#ffffff' }} />
        </div>
        <div className="ml-auto text-xs font-mono opacity-50 text-white">
          Deck-star ✦
        </div>
      </div>

      {/* Content area */}
      <div className="flex gap-6 p-6 h-[calc(100%-56px)]">
        {/* Left col */}
        <div className="flex-1 flex flex-col gap-3">
          <div className="h-3 rounded-full opacity-60" style={{ background: '#ffffff', width: '80%' }} />
          <div className="h-2 rounded-full opacity-30" style={{ background: '#ffffff', width: '100%' }} />
          <div className="h-2 rounded-full opacity-30" style={{ background: '#ffffff', width: '90%' }} />
          <div className="h-2 rounded-full opacity-30" style={{ background: '#ffffff', width: '70%' }} />
          <div className="mt-3 flex gap-2">
            {[theme.accent, '#ffffff44', '#ffffff22'].map((c, i) => (
              <div key={i} className="h-6 rounded-md flex-1" style={{ background: c }} />
            ))}
          </div>
        </div>

        {/* Right col — chart */}
        <div className="w-1/2 flex flex-col">
          <div className="h-2 rounded-full opacity-40 mb-3" style={{ background: '#ffffff', width: '60%' }} />
          <div className="flex-1 flex items-end gap-1.5">
            {bars.map((h, i) => (
              <div
                key={i}
                className="flex-1 rounded-sm"
                style={{
                  height: `${h}%`,
                  background: i % 2 === 0
                    ? theme.accent
                    : theme.accent + '66',
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function ThemesSection() {
  const [selected, setSelected] = useState(THEMES[0])

  return (
    <section className="py-24 px-6 relative overflow-hidden">
      <div className="orb w-[400px] h-[400px] bg-brand-purple/10 bottom-0 right-0 pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Heading */}
        <div className="text-center mb-14">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-brand-violet text-sm font-semibold uppercase tracking-widest mb-3"
          >
            Visual Identity
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="text-4xl md:text-5xl font-black text-white"
          >
            10 Professional{' '}
            <span className="gradient-text">Brand Themes</span>
          </motion.h2>
        </div>

        <div className="flex flex-col lg:flex-row gap-10 items-center">
          {/* Theme picker */}
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55 }}
            className="flex flex-col gap-3 lg:w-56 flex-shrink-0"
          >
            {THEMES.map((theme) => (
              <button
                key={theme.value}
                onClick={() => setSelected(theme)}
                className={`flex items-center gap-4 px-4 py-3 rounded-xl border transition-all duration-200 text-left ${
                  selected.value === theme.value
                    ? 'border-brand-purple/60 bg-brand-purple/10 shadow-glow-sm'
                    : 'border-white/8 glass hover:border-white/20 hover:bg-white/5'
                }`}
              >
                {/* Color dot */}
                <div
                  className="w-8 h-8 rounded-lg flex-shrink-0 border border-white/10"
                  style={{ background: `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})` }}
                />
                <div>
                  <div
                    className={`text-sm font-semibold ${
                      selected.value === theme.value ? 'text-brand-violet' : 'text-void-200'
                    }`}
                  >
                    {theme.label}
                  </div>
                  <div className="text-xs text-void-500 capitalize">{theme.value.replace(/_/g, ' ')}</div>
                </div>
                {selected.value === theme.value && (
                  <div className="ml-auto w-2 h-2 rounded-full bg-brand-violet" />
                )}
              </button>
            ))}
          </motion.div>

          {/* Preview */}
          <motion.div
            initial={{ opacity: 0, x: 24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55 }}
            className="flex-1 w-full"
          >
            <div className="mb-3 flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-sm"
                style={{ background: `linear-gradient(135deg, ${selected.primary}, ${selected.accent})` }}
              />
              <span className="text-void-300 text-sm font-medium">{selected.label} Theme Preview</span>
            </div>
            <AnimatePresence mode="wait">
              <MockSlidePreview key={selected.value} theme={selected} />
            </AnimatePresence>
            <p className="text-void-500 text-xs mt-3 text-center">
              Live preview of {selected.label} color palette applied to a sample slide
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
