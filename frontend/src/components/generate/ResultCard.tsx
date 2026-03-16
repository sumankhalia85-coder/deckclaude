'use client'

import Image from 'next/image'
import { motion } from 'framer-motion'
import { Download, CheckCircle2, RefreshCw } from 'lucide-react'
import Button from '@/components/ui/Button'
import GlassCard from '@/components/ui/GlassCard'
import Badge from '@/components/ui/Badge'
import { THEMES, DECK_TYPES } from '@/lib/constants'
import { deckImageSrc } from '@/components/home/DeckPreview'
import { getDownloadUrl } from '@/lib/api'
import type { GenerationJob } from '@/lib/store'

interface ResultCardProps {
  job: GenerationJob
  onGenerateAnother: () => void
}

export default function ResultCard({ job, onGenerateAnother }: ResultCardProps) {
  const handleDownload = () => {
    if (!job.downloadUrl) return
    const url = getDownloadUrl(job.downloadUrl)
    const a = document.createElement('a')
    a.href = url
    a.download = url.split('/').pop() || 'deck.pptx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const theme = THEMES.find(t => t.value === job.theme)
  const deckType = DECK_TYPES.find(d => d.value === job.deckType)
  const imgSrc = deckImageSrc(job.deckType || 'strategy_deck', 900)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="text-center space-y-8"
    >
      {/* Deck type image hero */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="relative w-full overflow-hidden rounded-2xl"
        style={{ aspectRatio: '16 / 7' }}
      >
        {imgSrc && (
          <Image
            src={imgSrc}
            alt={deckType?.label || 'Deck preview'}
            fill
            sizes="(max-width: 768px) 100vw, 660px"
            className="object-cover"
            priority
          />
        )}
        {/* gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        {/* success badge top-right */}
        <div className="absolute top-4 right-4">
          <div className="flex items-center gap-1.5 bg-emerald-500/20 backdrop-blur-md border border-emerald-500/30 rounded-full px-3 py-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-emerald-300 text-xs font-semibold">Ready</span>
          </div>
        </div>
      </motion.div>

      {/* Minimal Prompt Preview style quote */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-left px-2 max-w-3xl mx-auto"
      >
        <div className="border-l-2 border-cyan-500/40 pl-4 py-1">
          <p className="text-void-300 text-sm leading-relaxed antialiased font-medium">
             "{job.prompt}"
          </p>
        </div>
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="flex flex-col gap-3 max-w-xl mx-auto w-full"
      >
        <Button
          variant="gradient"
          size="lg"
          fullWidth
          onClick={handleDownload}
          disabled={!job.downloadUrl}
        >
          <Download className="w-5 h-5" />
          <span>{job.downloadUrl ? 'Download .pptx' : 'File not available (demo mode)'}</span>
        </Button>

        <Button variant="ghost" size="md" fullWidth onClick={onGenerateAnother}>
          <RefreshCw className="w-4 h-4" />
          <span>Generate Another</span>
        </Button>
      </motion.div>
    </motion.div>
  )
}
