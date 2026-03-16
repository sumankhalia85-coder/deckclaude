'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Sparkles } from 'lucide-react'
import { THEMES, DECK_TYPES } from '@/lib/constants'
import { deckImageSrc } from '@/components/home/DeckPreview'
import Button from '@/components/ui/Button'
import GlassCard from '@/components/ui/GlassCard'

const AUDIENCES = ['Executives', 'Board', 'Investors', 'Clients', 'Internal Team', 'Employees', 'Partners']

interface FormModeProps {
  onSubmit: (data: {
    prompt: string
    theme: string
    slides: number
    deckType: string
    includeCharts: boolean
    includeDiagrams: boolean
    includeImages: boolean
    formData: Record<string, unknown>
  }) => void
  loading?: boolean
}

const inputClass =
  'w-full bg-void-800/60 border border-white/10 rounded-xl px-4 py-3 text-void-100 placeholder-void-500 text-sm outline-none focus:border-brand-purple/60 focus:shadow-glow-sm transition-all duration-200'

export default function FormMode({ onSubmit, loading = false }: FormModeProps) {
  const [industry, setIndustry] = useState('')
  const [audience, setAudience] = useState('Executives')
  const [deckType, setDeckType] = useState('strategy_deck')
  const [slides, setSlides] = useState(10)
  const [keyMessage, setKeyMessage] = useState('')
  const [theme, setTheme] = useState('mckinsey')
  const [includeCharts, setIncludeCharts] = useState(true)
  const [includeDiagrams, setIncludeDiagrams] = useState(true)
  const [includeImages, setIncludeImages] = useState(true)
  const [includeArchitecture, setIncludeArchitecture] = useState(false)

  const handleSubmit = () => {
    const selectedDeck = DECK_TYPES.find(d => d.value === deckType)
    const prompt = `Create a ${selectedDeck?.label || deckType} for ${audience} in the ${industry || 'general'} industry. Key message: ${keyMessage || 'provide strategic insights and recommendations'}. Target ${slides} slides.`
    onSubmit({
      prompt,
      theme,
      slides,
      deckType,
      includeCharts,
      includeDiagrams,
      includeImages,
      formData: { industry, audience, keyMessage, includeArchitecture },
    })
  }

  return (
    <div className="space-y-8">
      {/* Industry */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">Industry / Sector</p>
        <input
          type="text"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          placeholder="e.g. Healthcare, Retail, Financial Services, Technology..."
          className={inputClass}
        />
      </GlassCard>

      {/* Target Audience */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">Target Audience</p>
        <div className="flex flex-wrap gap-2">
          {AUDIENCES.map((a) => (
            <button
              key={a}
              onClick={() => setAudience(a)}
              className={`px-4 py-2 rounded-full text-sm font-medium border transition-all duration-200 ${
                audience === a
                  ? 'border-brand-purple bg-brand-purple/20 text-brand-violet'
                  : 'border-white/10 text-void-400 hover:border-white/20 hover:text-void-200'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </GlassCard>

      {/* Deck Type */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">Deck Type</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {DECK_TYPES.map((dt) => {
            const active = deckType === dt.value
            return (
              <button
                key={dt.value}
                onClick={() => setDeckType(dt.value)}
                className={`group relative rounded-xl overflow-hidden border text-left transition-all duration-200 ${
                  active
                    ? 'border-brand-purple shadow-glow-sm'
                    : 'border-white/8 hover:border-white/25'
                }`}
              >
                <div className="relative w-full" style={{ aspectRatio: '16/9' }}>
                  <Image
                    src={deckImageSrc(dt.value, 320)}
                    alt={dt.label}
                    fill
                    sizes="(max-width: 640px) 50vw, 25vw"
                    className={`object-cover transition-all duration-300 ${active ? 'brightness-75' : 'brightness-50 group-hover:brightness-65'}`}
                  />
                  {active && <div className="absolute inset-0 bg-brand-purple/25" />}
                </div>
                <div className={`px-2.5 py-2 ${active ? 'bg-brand-purple/15' : 'bg-void-800/60'}`}>
                  <span className={`text-xs font-semibold leading-tight block ${active ? 'text-brand-violet' : 'text-void-300'}`}>
                    {dt.label}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </GlassCard>

      {/* Slide count */}
      <GlassCard padding="md">
        <div className="flex justify-between items-center mb-3">
          <p className="text-void-300 text-sm font-semibold">Number of Slides</p>
          <span className="text-brand-violet font-bold text-lg">{slides}</span>
        </div>
        <div className="relative h-2 bg-void-700 rounded-full overflow-hidden">
          <div
            className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-brand-purple to-brand-blue transition-all"
            style={{ width: `${((slides - 5) / 20) * 100}%` }}
          />
          <input
            type="range"
            min={5}
            max={25}
            value={slides}
            onChange={(e) => setSlides(Number(e.target.value))}
            className="absolute inset-0 w-full opacity-0 cursor-pointer"
          />
        </div>
        <div className="flex justify-between text-xs text-void-500 mt-1">
          <span>5</span><span>25</span>
        </div>
      </GlassCard>

      {/* Key Message */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">Key Message / Objective</p>
        <textarea
          value={keyMessage}
          onChange={(e) => setKeyMessage(e.target.value)}
          placeholder="What is the primary takeaway or goal of this presentation? e.g. 'Convince the board to approve $5M investment in AI infrastructure'"
          rows={3}
          className={inputClass + ' resize-none'}
        />
      </GlassCard>

      {/* Theme picker */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">Brand Theme</p>
        <div className="flex flex-wrap gap-3 mb-2">
          {THEMES.map((t) => (
            <button
              key={t.value}
              onClick={() => setTheme(t.value)}
              title={t.label}
              className={`theme-badge ${theme === t.value ? 'selected' : ''}`}
              style={{ background: `linear-gradient(135deg, ${t.primary}, ${t.secondary})` }}
            />
          ))}
        </div>
        <p className="text-void-500 text-xs">
          Selected: <span className="text-brand-violet font-medium">{THEMES.find(t => t.value === theme)?.label}</span>
        </p>
      </GlassCard>

      {/* Toggles */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-4">Content Options</p>
        <div className="space-y-3">
          {[
            { label: 'Include Charts', desc: 'Auto-generate data visualizations', value: includeCharts, set: setIncludeCharts },
            { label: 'Include Diagrams', desc: 'Frameworks, matrices, process flows', value: includeDiagrams, set: setIncludeDiagrams },
            { label: 'Include Images', desc: 'Stock photography and icons', value: includeImages, set: setIncludeImages },
            { label: 'Architecture Diagram', desc: 'System or process architecture', value: includeArchitecture, set: setIncludeArchitecture },
          ].map((opt) => (
            <div key={opt.label} className="flex items-center justify-between">
              <div>
                <p className="text-void-200 text-sm font-medium">{opt.label}</p>
                <p className="text-void-500 text-xs">{opt.desc}</p>
              </div>
              <button
                onClick={() => opt.set(!opt.value)}
                className={`relative w-12 h-6 rounded-full border transition-all duration-200 ${
                  opt.value ? 'bg-brand-purple border-brand-purple' : 'bg-void-700 border-white/10'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-200 ${
                    opt.value ? 'left-6' : 'left-0.5'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Submit */}
      <Button
        variant="gradient"
        size="lg"
        fullWidth
        loading={loading}
        onClick={handleSubmit}
        disabled={!industry.trim() && !keyMessage.trim()}
      >
        <Sparkles className="w-5 h-5" />
        <span>Generate Presentation ✦</span>
      </Button>
    </div>
  )
}
