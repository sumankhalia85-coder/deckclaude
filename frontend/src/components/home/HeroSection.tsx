'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Sparkles, ArrowRight } from 'lucide-react'
import { EXAMPLE_PROMPTS } from '@/lib/constants'

const STATS = [
  { value: '12', label: 'AI Agents' },
  { value: '10', label: 'Deck Types' },
  { value: '10', label: 'Brand Themes' },
  { value: '< 60s', label: 'Generation Time' },
]

const MOCK_SLIDE_LEFT = {
  title: 'Market Entry Strategy',
  subtitle: 'Southeast Asia Expansion',
  bars: [70, 55, 85, 45, 90],
  accent: '#7C3AED',
}

const MOCK_SLIDE_RIGHT = {
  title: 'Q4 Performance',
  subtitle: 'Executive Summary',
  bars: [60, 80, 50, 75, 65],
  accent: '#2563EB',
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] } },
}

function MockSlideCard({
  slide,
  rotate,
  offset,
  blur,
}: {
  slide: typeof MOCK_SLIDE_LEFT
  rotate: number
  offset: { x: number; y: number }
  blur: boolean
}) {
  return (
    <motion.div
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', delay: offset.x > 0 ? 1 : 0 }}
      style={{ rotate, x: offset.x, y: offset.y }}
      className={`hidden xl:block absolute w-64 slide-card p-4 ${blur ? 'opacity-60 blur-[1px]' : 'opacity-80'}`}
    >
      {/* Title bar */}
      <div className="h-3 rounded-full mb-3" style={{ background: slide.accent, width: '70%' }} />
      <div className="h-2 rounded-full mb-6 bg-white/10" style={{ width: '50%' }} />

      {/* Mock chart bars */}
      <div className="flex items-end gap-2 h-16 mt-2">
        {slide.bars.map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-sm opacity-80"
            style={{
              height: `${h}%`,
              background: `linear-gradient(to top, ${slide.accent}cc, ${slide.accent}44)`,
            }}
          />
        ))}
      </div>

      {/* Footer line */}
      <div className="mt-4 flex gap-2">
        <div className="h-2 rounded-full bg-white/10 flex-1" />
        <div className="h-2 rounded-full bg-white/5 w-1/3" />
      </div>

      {/* Bottom tag */}
      <div className="mt-3 text-xs font-mono" style={{ color: slide.accent + 'cc' }}>
        {slide.title}
      </div>
    </motion.div>
  )
}

export default function HeroSection() {
  const router = useRouter()
  const [prompt, setPrompt] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleGenerate = () => {
    if (!prompt.trim()) return
    router.push(`/generate?prompt=${encodeURIComponent(prompt.trim())}`)
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleGenerate()
  }

  const SHOWN_EXAMPLES = EXAMPLE_PROMPTS.slice(0, 3)

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-32 pb-32 px-6">
      {/* Background orbs */}
      <div className="orb w-[600px] h-[600px] bg-brand-blue/15 top-[-150px] left-[-200px] animate-float" />
      <div
        className="orb w-[500px] h-[500px] bg-cyan-500/10 bottom-[-100px] right-[-150px]"
        style={{ animationDelay: '3s' }}
      />
      <div className="orb w-[300px] h-[300px] bg-sky-400/10 top-[40%] left-[50%] -translate-x-1/2" />

      {/* Grid */}
      <div className="absolute inset-0 grid-bg opacity-50" />

      {/* Main content */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center max-w-7xl mx-auto w-full pt-20 px-4">
        {/* Left column: Controls / CTA */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="lg:col-span-6 flex flex-col items-start text-left"
        >
          {/* Badge */}
          <motion.div variants={itemVariants}>
            <span className="chip inline-flex items-center gap-2 mb-6 cursor-default">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              ✦ AI-Powered Class
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={itemVariants}
            className="font-black leading-[1.05] mb-6 tracking-tight"
            style={{ fontSize: 'clamp(38px, 5vw, 64px)' }}
          >
            <span className="text-white block">Transform Ideas Into</span>
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-400 bg-clip-text text-transparent block">
               Consulting-Grade Decks
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={itemVariants}
            className="text-void-300 text-base md:text-lg max-w-lg mb-10 leading-relaxed"
          >
            Generate McKinsey-quality PowerPoint presentations with AI. 
            Powered by specialized agent ecosystems. 
          </motion.p>

          {/* Prompt bar */}
          <motion.div variants={itemVariants} className="w-full max-w-md mb-5">
            <div className="prompt-input flex items-center gap-3 bg-void-800/40 border border-white/5 rounded-2xl px-4 py-3.5 transition-all duration-200 hover:border-cyan-500/30 shadow-2xl focus-within:border-cyan-500/40">
              <Sparkles className="w-5 h-5 text-cyan-500 flex-shrink-0" />
              <input
                ref={inputRef}
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Describe your presentation..."
                className="flex-1 bg-transparent outline-none text-void-100 placeholder-void-500 text-sm min-w-0"
              />
              <button
                onClick={handleGenerate}
                disabled={!prompt.trim()}
                className="flex-shrink-0 flex items-center gap-1.5 bg-gradient-to-r from-cyan-500 to-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold hover:opacity-90 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-glow-sm"
              >
                Generate ✦ <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>

          {/* Example chips */}
          <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-1.5 mb-12">
            <span className="text-void-400 text-xs mr-1">Try:</span>
            {SHOWN_EXAMPLES.map((ex, i) => (
              <button
                key={i}
                onClick={() => {
                  setPrompt(ex)
                  inputRef.current?.focus()
                }}
                className="chip text-[11px] max-w-[160px] truncate bg-white/3 hover:bg-white/5 border border-white/5 py-1 px-2.5"
                title={ex}
              >
                {ex.split(',')[0]}
              </button>
            ))}
          </motion.div>

          {/* Stats row */}
          <motion.div
            variants={itemVariants}
            className="flex flex-wrap items-center gap-6 md:gap-10 border-t border-white/5 pt-6 w-full max-w-md"
          >
            {STATS.slice(0, 3).map((stat, i) => (
              <div key={i} className="flex flex-col items-start gap-1">
                <span className="text-xl md:text-2xl font-black bg-gradient-to-r from-white to-void-300 bg-clip-text text-transparent">{stat.value}</span>
                <span className="text-void-400 text-[10px] font-medium uppercase tracking-wider">{stat.label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Right column: Dashboard Mockup */}
        <motion.div 
          variants={itemVariants}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="lg:col-span-6 relative w-full flex justify-center items-center"
        >
          <div className="relative rounded-xl overflow-hidden border border-white/5 shadow-glass w-full group shadow-2xl">
            <div className="absolute top-0 left-0 right-0 h-8 border-b border-white/5 flex items-center px-4 gap-1.5 bg-white/5 z-20">
              <span className="w-2 h-2 rounded-full bg-red-400/80" />
              <span className="w-2 h-2 rounded-full bg-yellow-400/80" />
              <span className="w-2 h-2 rounded-full bg-green-400/80" />
            </div>
            <div className="pt-8">
               <img 
                 src="https://images.unsplash.com/photo-1542744173-8e7e53415bb0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80" 
                 className="w-full object-cover aspect-[4/3] group-hover:scale-[1.01] transition-all duration-500"
                 alt="App Dashboard Preview"
               />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-void-900/60 via-transparent to-transparent pointer-events-none" />
          </div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-void-900 to-transparent pointer-events-none" />
    </section>
  )
}
