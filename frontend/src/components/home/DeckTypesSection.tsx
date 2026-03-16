'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { ChevronLeft, ChevronRight, Sparkles, ArrowUpRight } from 'lucide-react'
import Image from 'next/image'
import { DECK_TYPES } from '@/lib/constants'
import { DECK_IMAGES, deckImageSrc } from './DeckPreview'

const SLIDE_COUNTS: Record<string, number> = {
  strategy_deck: 16,
  executive_update: 10,
  proposal_deck: 14,
  pitch_deck: 12,
  board_presentation: 18,
  research_summary: 12,
  project_status: 8,
  training_deck: 20,
}

const AUTOPLAY_MS = 4500

// ── Text animation variants ──────────────────────────────────────────────────

const textContainer = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
  exit: { transition: { staggerChildren: 0.04, staggerDirection: -1 } },
}

const textItem = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25 } },
}

// ── Main component ───────────────────────────────────────────────────────────

export default function DeckTypesSection() {
  const router = useRouter()
  const [active, setActive] = useState(0)
  const [dir, setDir] = useState(1)
  const [paused, setPaused] = useState(false)
  const [progressKey, setProgressKey] = useState(0)
  const thumbsRef = useRef<HTMLDivElement>(null)

  const go = useCallback(
    (idx: number) => {
      setDir(idx > active ? 1 : -1)
      setActive(idx)
      setProgressKey((k) => k + 1)
    },
    [active],
  )

  const goPrev = useCallback(() => go((active - 1 + DECK_TYPES.length) % DECK_TYPES.length), [active, go])
  const goNext = useCallback(() => go((active + 1) % DECK_TYPES.length), [active, go])

  // Auto-advance
  useEffect(() => {
    if (paused) return
    const t = setInterval(goNext, AUTOPLAY_MS)
    return () => clearInterval(t)
  }, [goNext, paused])

  // Scroll active thumbnail into view
  useEffect(() => {
    const container = thumbsRef.current
    if (!container) return
    const thumb = container.children[active] as HTMLElement
    if (thumb) {
      thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [active])

  const deck = DECK_TYPES[active]
  const imgData = DECK_IMAGES[deck.value]

  const slideVariants = {
    enter: (d: number) => ({ x: d > 0 ? 80 : -80, opacity: 0 }),
    center: { x: 0, opacity: 1, transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] } },
    exit: (d: number) => ({
      x: d > 0 ? -80 : 80,
      opacity: 0,
      transition: { duration: 0.35, ease: [0.55, 0, 1, 0.45] },
    }),
  }

  return (
    <section className="py-24 px-6 overflow-hidden">
      <div className="max-w-6xl mx-auto">

        {/* ── Heading ── */}
        <div className="text-center mb-12">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-brand-violet text-sm font-semibold uppercase tracking-widest mb-3"
          >
            Deck Library
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="text-4xl md:text-5xl font-black text-white"
          >
            Every Deck Type,{' '}
            <span className="gradient-text">Perfected</span>
          </motion.h2>
        </div>

        {/* ── Spotlight card ── */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative rounded-3xl overflow-hidden"
          style={{ height: 'clamp(340px, 50vw, 520px)' }}
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          {/* ── Background photo layer ── */}
          <AnimatePresence custom={dir} initial={false}>
            <motion.div
              key={`bg-${active}`}
              custom={dir}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="absolute inset-0"
            >
              <Image
                src={deckImageSrc(deck.value, 1200)}
                alt={imgData?.alt || deck.label}
                fill
                priority
                sizes="100vw"
                className="object-cover"
              />
            </motion.div>
          </AnimatePresence>

          {/* ── Gradient overlays ── */}
          {/* Bottom fade for text */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/35 to-black/10 pointer-events-none" />
          {/* Left brand tint */}
          <div className="absolute inset-0 bg-gradient-to-r from-brand-purple/30 via-transparent to-transparent pointer-events-none" />
          {/* Subtle vignette */}
          <div className="absolute inset-0 bg-radial-gradient pointer-events-none opacity-40"
            style={{ background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)' }} />

          {/* ── Deck counter (top-right) ── */}
          <div className="absolute top-5 right-5 flex items-center gap-1.5 bg-black/40 backdrop-blur-md rounded-full px-3 py-1.5 border border-white/10">
            <span className="text-white font-bold text-sm tabular-nums">
              {String(active + 1).padStart(2, '0')}
            </span>
            <span className="text-white/30 text-xs">/</span>
            <span className="text-white/40 text-xs tabular-nums">
              {String(DECK_TYPES.length).padStart(2, '0')}
            </span>
          </div>

          {/* ── Slide count badge (top-left) ── */}
          <div className="absolute top-5 left-5 bg-black/40 backdrop-blur-md rounded-full px-3 py-1.5 border border-white/10">
            <span className="text-white/60 text-xs font-medium">
              ~{SLIDE_COUNTS[deck.value]} slides
            </span>
          </div>

          {/* ── Animated text content (bottom-left) ── */}
          <div className="absolute bottom-0 left-0 right-0 p-7 md:p-10">
            <AnimatePresence mode="wait">
              <motion.div
                key={`text-${active}`}
                variants={textContainer}
                initial="hidden"
                animate="show"
                exit="exit"
                className="max-w-2xl"
              >
                <motion.p variants={textItem} className="text-brand-violet text-xs font-bold uppercase tracking-widest mb-2">
                  {deck.label}
                </motion.p>

                <motion.h3 variants={textItem} className="text-white font-black text-3xl md:text-5xl leading-tight mb-3 drop-shadow-lg">
                  {deck.label}
                </motion.h3>

                <motion.p variants={textItem} className="text-white/60 text-sm md:text-base leading-relaxed mb-6 max-w-lg">
                  {deck.description}
                </motion.p>

                <motion.div variants={textItem}>
                  <button
                    onClick={() => router.push(`/generate?type=${deck.value}`)}
                    className="group/btn inline-flex items-center gap-2 bg-brand-purple hover:bg-brand-violet transition-colors duration-200 text-white text-sm font-semibold px-5 py-2.5 rounded-full"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Generate this deck
                    <ArrowUpRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform duration-150" />
                  </button>
                </motion.div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* ── Prev / Next buttons ── */}
          <button
            onClick={(e) => { e.stopPropagation(); goPrev() }}
            className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/40 hover:bg-black/70 backdrop-blur-sm border border-white/10 hover:border-white/25 flex items-center justify-center text-white transition-all duration-200 hover:scale-110"
            aria-label="Previous deck"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); goNext() }}
            className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/40 hover:bg-black/70 backdrop-blur-sm border border-white/10 hover:border-white/25 flex items-center justify-center text-white transition-all duration-200 hover:scale-110"
            aria-label="Next deck"
          >
            <ChevronRight className="w-5 h-5" />
          </button>

          {/* ── Autoplay progress bar ── */}
          <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-white/10">
            {!paused && (
              <motion.div
                key={progressKey}
                className="h-full bg-brand-purple"
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: AUTOPLAY_MS / 1000, ease: 'linear' }}
              />
            )}
          </div>
        </motion.div>

        {/* ── Thumbnail strip ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          ref={thumbsRef}
          className="flex gap-3 mt-4 overflow-x-auto pb-2 scrollbar-hide snap-x snap-mandatory"
          style={{ scrollbarWidth: 'none' }}
        >
          {DECK_TYPES.map((d, i) => {
            const isActive = i === active
            return (
              <button
                key={d.value}
                onClick={() => go(i)}
                className="flex-shrink-0 snap-start group/thumb flex flex-col items-center gap-1.5 focus:outline-none"
                style={{ width: 'clamp(88px, 11vw, 120px)' }}
              >
                <div
                  className={`relative w-full overflow-hidden rounded-xl transition-all duration-300 ${
                    isActive
                      ? 'ring-2 ring-brand-purple shadow-glow-sm scale-100 opacity-100'
                      : 'ring-1 ring-white/10 scale-95 opacity-45 hover:opacity-70 hover:scale-100'
                  }`}
                  style={{ aspectRatio: '16 / 9' }}
                >
                  <Image
                    src={deckImageSrc(d.value, 240)}
                    alt={d.label}
                    fill
                    sizes="120px"
                    className="object-cover"
                  />
                  {/* active shimmer overlay */}
                  {isActive && (
                    <motion.div
                      layoutId="thumb-active"
                      className="absolute inset-0 bg-brand-purple/20"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                </div>
                <span
                  className={`text-[10px] font-medium text-center leading-tight transition-colors duration-200 ${
                    isActive ? 'text-white' : 'text-void-500'
                  }`}
                >
                  {d.label}
                </span>
              </button>
            )
          })}
        </motion.div>

        {/* ── Dot indicators ── */}
        <div className="flex justify-center gap-1.5 mt-4">
          {DECK_TYPES.map((_, i) => (
            <button
              key={i}
              onClick={() => go(i)}
              className={`rounded-full transition-all duration-300 ${
                i === active
                  ? 'w-6 h-1.5 bg-brand-purple'
                  : 'w-1.5 h-1.5 bg-white/20 hover:bg-white/40'
              }`}
              aria-label={`Go to deck ${i + 1}`}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
