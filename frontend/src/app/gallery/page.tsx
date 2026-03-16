'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { Download, RefreshCw, Sparkles, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import Navbar from '@/components/layout/Navbar'
import GlassCard from '@/components/ui/GlassCard'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { useAppStore } from '@/lib/store'
import { THEMES, DECK_TYPES } from '@/lib/constants'
import type { GenerationJob } from '@/lib/store'

const STATUS_COLORS: Record<GenerationJob['status'], 'green' | 'blue' | 'orange' | 'red'> = {
  completed: 'green',
  processing: 'blue',
  running: 'blue',
  pending: 'orange',
  queued: 'orange',
  failed: 'red',
}

const STATUS_ICONS: Record<GenerationJob['status'], typeof CheckCircle2> = {
  completed: CheckCircle2,
  processing: Loader2,
  running: Loader2,
  pending: Clock,
  queued: Clock,
  failed: XCircle,
}

function DeckCard({ job }: { job: GenerationJob }) {
  const theme = THEMES.find(t => t.value === job.theme)
  const deckType = DECK_TYPES.find(d => d.value === job.deckType)
  const StatusIcon = STATUS_ICONS[job.status]

  const timeAgo = (date: Date) => {
    const diff = Date.now() - new Date(date).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  return (
    <GlassCard hover className="flex flex-col gap-4 h-full">
      {/* Mock slide thumbnail */}
      <div
        className="slide-card w-full p-4"
        style={{ background: `linear-gradient(135deg, ${theme?.primary || '#1A1A2E'}, ${theme?.secondary || '#12121F'})` }}
      >
        {/* Title bar */}
        <div className="h-2.5 rounded-full mb-2" style={{ background: theme?.accent || '#7C3AED', width: '65%' }} />
        <div className="h-1.5 rounded-full mb-4 opacity-40" style={{ background: '#ffffff', width: '45%' }} />
        {/* Content bars */}
        <div className="space-y-1.5">
          {[80, 60, 90, 50].map((w, i) => (
            <div key={i} className="h-1 rounded-full opacity-20" style={{ background: '#ffffff', width: `${w}%` }} />
          ))}
        </div>
        {/* Chart placeholder */}
        <div className="mt-3 flex items-end gap-1 h-8">
          {[60, 80, 45, 90, 55].map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-sm opacity-60"
              style={{ height: `${h}%`, background: theme?.accent || '#7C3AED' }}
            />
          ))}
        </div>
      </div>

      {/* Meta */}
      <div className="flex-1 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <p className="text-void-200 text-sm font-semibold leading-tight line-clamp-2">{job.prompt}</p>
          <Badge color={STATUS_COLORS[job.status]} className="flex-shrink-0">
            <StatusIcon className={`w-3 h-3 ${job.status === 'processing' ? 'animate-spin' : ''}`} />
            {job.status}
          </Badge>
        </div>

        <div className="flex items-center gap-3 text-xs text-void-500">
          <span className="flex items-center gap-1">
            {deckType?.label || job.deckType}
          </span>
          <span>·</span>
          <span className="flex items-center gap-1">
            {theme?.label || job.theme}
          </span>
          <span>·</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(job.createdAt)}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          variant="gradient"
          size="sm"
          className="flex-1"
          disabled={job.status !== 'completed' || !job.downloadUrl}
          onClick={() => job.downloadUrl && window.open(job.downloadUrl, '_blank')}
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download</span>
        </Button>
        <Link href={`/generate?prompt=${encodeURIComponent(job.prompt)}&type=${job.deckType}`}>
          <Button variant="ghost" size="sm">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </GlassCard>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-center">
      {/* Decorative */}
      <div className="relative mb-8">
        <div className="w-24 h-24 rounded-2xl glass flex items-center justify-center border border-white/10">
          <Sparkles className="w-10 h-10 text-brand-violet opacity-50" />
        </div>
        <div className="absolute -inset-4 rounded-3xl bg-brand-purple/5 -z-10 blur-xl" />
      </div>

      <h3 className="text-2xl font-bold text-white mb-3">No decks yet</h3>
      <p className="text-void-400 text-sm max-w-xs mb-8">
        Generate your first consulting-grade presentation and it will appear here.
      </p>

      <Link href="/generate">
        <Button variant="gradient" size="lg">
          <Sparkles className="w-5 h-5" />
          <span>Generate Your First Deck</span>
        </Button>
      </Link>
    </div>
  )
}

const ALL_FILTER = 'all'

export default function GalleryPage() {
  const { jobs } = useAppStore()
  const [filter, setFilter] = useState<string>(ALL_FILTER)

  const deckTypeFilters = Array.from(new Set(jobs.map(j => j.deckType)))
  const filteredJobs = filter === ALL_FILTER ? jobs : jobs.filter(j => j.deckType === filter || j.status === filter)

  return (
    <main className="min-h-screen bg-void-900 grid-bg">
      <Navbar />

      <div className="fixed orb w-[400px] h-[400px] bg-brand-purple/8 top-0 right-0 pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 pt-32 pb-20">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-4xl md:text-5xl font-black mb-2">
                <span className="text-white">Your Decks </span>
                <span className="gradient-text">✦</span>
              </h1>
              <p className="text-void-400 text-sm">
                {jobs.length} deck{jobs.length !== 1 ? 's' : ''} generated
              </p>
            </div>

            <Link href="/generate">
              <Button variant="gradient" size="md">
                <Sparkles className="w-4 h-4" />
                <span>New Deck</span>
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Filters */}
        {jobs.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex flex-wrap gap-2 mb-8"
          >
            <button
              onClick={() => setFilter(ALL_FILTER)}
              className={`chip ${filter === ALL_FILTER ? 'active' : ''}`}
            >
              All ({jobs.length})
            </button>
            {deckTypeFilters.map((dt) => {
              const deckType = DECK_TYPES.find(d => d.value === dt)
              const count = jobs.filter(j => j.deckType === dt).length
              return (
                <button
                  key={dt}
                  onClick={() => setFilter(dt)}
                  className={`chip ${filter === dt ? 'active' : ''}`}
                >
                  {deckType?.label || dt} ({count})
                </button>
              )
            })}
            {['completed', 'processing', 'failed'].filter(s => jobs.some(j => j.status === s)).map(s => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`chip ${filter === s ? 'active' : ''}`}
              >
                {s}
              </button>
            ))}
          </motion.div>
        )}

        {/* Content */}
        {jobs.length === 0 ? (
          <EmptyState />
        ) : filteredJobs.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-void-400">No decks match this filter.</p>
            <button onClick={() => setFilter(ALL_FILTER)} className="chip mt-4">
              Show all
            </button>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.15 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
          >
            {filteredJobs.map((job, i) => (
              <motion.div
                key={job.jobId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
              >
                <DeckCard job={job} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </main>
  )
}
