'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, ChevronRight } from 'lucide-react'
import { THEMES, DECK_TYPES } from '@/lib/constants'
import { deckImageSrc } from '@/components/home/DeckPreview'
import Button from '@/components/ui/Button'

// ── Deck-specific example prompts ─────────────────────────────────────────────

const DECK_PROMPTS: Record<string, string[]> = {
  strategy_deck: [
    'Build a 16-slide AI transformation strategy for a Fortune 500 retail CEO — market shifts, competitive threats, and a 3-year implementation roadmap',
    'Create a market entry strategy for expanding into Southeast Asia covering TAM sizing, regulatory landscape, and go-to-market phasing',
    'Generate a digital transformation strategy for a traditional bank modernising core infrastructure with cloud, data, and AI pillars',
    'Build a growth strategy deck showing market sizing, customer segments, revenue expansion levers, and resource requirements for a SaaS company',
    'Create a competitive positioning strategy for a healthcare company responding to new market entrants and changing regulatory environment',
  ],
  executive_update: [
    'Generate a Q3 executive update for the CEO covering revenue vs target, key wins, flagged risks, and revised Q4 priorities',
    'Create a monthly board update with KPI dashboard, team highlights, budget utilisation, and strategic milestone tracking',
    'Build a QBR presentation for a tech company — ARR growth, churn analysis, product launches, NPS movement, and next quarter plan',
    'Generate an executive briefing on our AI adoption programme — progress to date, ROI achieved, blockers, and next quarter investment ask',
    'Create a year-end performance summary covering financial results, operational highlights, people metrics, and 2025 strategic priorities',
  ],
  proposal_deck: [
    'Create a digital transformation services proposal for a healthcare client — scope, approach, team, timeline, and commercial model',
    'Build a cloud migration proposal for a retail enterprise including current-state assessment, phased roadmap, pricing tiers, and risk mitigation',
    'Generate an AI implementation proposal for a financial services firm covering prioritised use cases, build roadmap, and 3-year ROI projection',
    'Create a strategic consulting proposal for a manufacturing company addressing supply chain inefficiencies with McKinsey-style problem framing',
    'Build a technology partnership proposal for co-selling an enterprise SaaS product — strategic rationale, joint GTM plan, and revenue model',
  ],
  pitch_deck: [
    'Create a Series A pitch deck for a B2B SaaS HR-tech startup raising $10M — problem, solution, traction, unit economics, and use of funds',
    'Build a seed round pitch for an AI-powered healthcare diagnostics startup — problem urgency, proprietary model, clinical validation, and team',
    'Generate an investor pitch for a climate-tech company with $50B TAM — technology moat, regulatory tailwinds, 18-month plan, and ask',
    'Create a VC pitch deck for a fintech startup disrupting SME lending with proprietary credit scoring — market, product, traction, and team',
    'Build a fundraising deck for a logistics tech startup with live pilots, 3x YoY growth, and an international expansion roadmap',
  ],
  board_presentation: [
    'Create a Q4 board presentation — financial performance vs plan, strategic KPI dashboard, top risks, and revised FY outlook',
    'Build a board deck on a proposed $50M acquisition including strategic rationale, synergy analysis, integration plan, and financial impact',
    'Generate an annual board strategy review with market position assessment, competitive landscape, and 3-year financial projection model',
    'Create a board risk management presentation covering cybersecurity posture, regulatory exposure, operational risks, and mitigation investments',
    'Build a board governance update with ESG scorecard, compliance status, audit findings, and stakeholder engagement summary',
  ],
  research_summary: [
    'Generate a market research summary on AI adoption in retail banking — trends, investment levels, use case maturity, and strategic opportunities',
    'Create a competitive landscape analysis comparing the top 5 cloud ERP vendors across feature depth, pricing, implementation complexity, and NPS',
    'Build a customer insight research deck with persona mapping, Jobs-to-be-Done analysis, pain point prioritisation, and design implications',
    'Generate a global supply chain disruption report covering root causes, sector-level impact analysis, resilience strategies, and investment priorities',
    'Create a technology landscape analysis of generative AI platforms for enterprise knowledge management and decision support',
  ],
  project_status: [
    'Build a cloud migration programme status update — workstream RAG status, budget variance, milestone burn-down, and escalation items',
    'Create a monthly digital transformation programme update with dependency map, completed deliverables, blockers, and next 30-day plan',
    'Generate a sprint review presentation showing team velocity, completed user stories, backlog refinement, and upcoming sprint goals',
    'Build an infrastructure modernisation project status with phase gate results, timeline variance analysis, and revised delivery forecast',
    'Create a post-merger integration status deck tracking workstream progress, synergy capture to date, people risks, and leadership decisions needed',
  ],
  training_deck: [
    'Create a new sales hire onboarding deck covering our ICP, product positioning, sales methodology, objection handling, and first 30-60-90 day plan',
    'Build a cybersecurity awareness training for all staff — phishing recognition, password hygiene, data handling, and incident reporting protocol',
    'Generate a leadership development programme deck on executive communication, effective delegation, feedback models, and team performance coaching',
    'Create an AI tools enablement deck for marketing teams — prompt engineering fundamentals, approved tool stack, use cases, and guardrails',
    'Build a GDPR and data compliance training covering core principles, employee obligations, breach reporting, and practical dos and don\u2019ts',
  ],
}

// ── Props ────────────────────────────────────────────────────────────────────

interface PromptModeProps {
  initialPrompt?: string
  initialType?: string
  onSubmit: (data: {
    prompt: string
    theme: string
    slides: number
    deckType: string
    includeCharts: boolean
    includeDiagrams: boolean
    includeImages: boolean
  }) => void
  loading?: boolean
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function PromptMode({
  initialPrompt = '',
  initialType = '',
  onSubmit,
  loading = false,
}: PromptModeProps) {
  const [prompt, setPrompt] = useState(initialPrompt)
  const [theme, setTheme] = useState('mckinsey')
  const [slides, setSlides] = useState(10)
  const [deckType, setDeckType] = useState(initialType || 'strategy_deck')
  const [includeCharts, setIncludeCharts] = useState(true)
  const [includeDiagrams, setIncludeDiagrams] = useState(true)
  const [includeImages, setIncludeImages] = useState(true)
  const [selectedPromptIdx, setSelectedPromptIdx] = useState<number | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const promptsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (initialPrompt) setPrompt(initialPrompt)
    if (initialType) setDeckType(initialType)
  }, [initialPrompt, initialType])

  // Reset selected prompt chip when deck type changes
  useEffect(() => {
    setSelectedPromptIdx(null)
    promptsRef.current?.scrollTo({ left: 0, behavior: 'smooth' })
  }, [deckType])

  const autoResize = () => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.max(el.scrollHeight, 160)}px`
    }
  }

  const handlePromptChip = (p: string, idx: number) => {
    setPrompt(p)
    setSelectedPromptIdx(idx)
    textareaRef.current?.focus()
    setTimeout(autoResize, 10)
  }

  const handleSubmit = () => {
    if (!prompt.trim()) return
    onSubmit({ prompt, theme, slides, deckType, includeCharts, includeDiagrams, includeImages })
  }

  const deckPrompts = DECK_PROMPTS[deckType] || []
  const selectedDeck = DECK_TYPES.find(d => d.value === deckType)

  return (
    <div className="flex w-full min-h-[calc(100vh-200px)] border-t border-white/5 relative">

      {/* ── LEFT PANEL: Deck type + Config (Sticky Sidebar) ── */}
      <motion.div
        animate={{ width: sidebarOpen ? 350 : 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="bg-void-950/20 border-r border-white/5 lg:sticky lg:top-16 lg:h-[calc(100vh-64px)] overflow-hidden shrink-0"
      >
        <div className="p-5 w-[350px] space-y-6 relative h-full overflow-y-auto">
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="absolute top-4 right-4 text-void-500 hover:text-white transition-colors p-1"
            title="Collapse Options"
          >
             <ChevronRight className="w-4 h-4 rotate-180" />
          </button>

        {/* Deck type grid */}
        <div>
          <p className="text-void-400 text-xs font-semibold uppercase tracking-widest mb-3">Deck Type</p>
          <div className="grid grid-cols-2 gap-2">
            {DECK_TYPES.map((dt) => {
              const active = deckType === dt.value
              return (
                <button
                  key={dt.value}
                  onClick={() => setDeckType(dt.value)}
                  className={`group relative rounded-xl overflow-hidden border text-left transition-all duration-200 ${
                    active ? 'border-cyan-500/60 shadow-glow-sm' : 'border-white/8 hover:border-white/25'
                  }`}
                >
                  <div className="relative w-full" style={{ aspectRatio: '16/9' }}>
                    <Image
                      src={deckImageSrc(dt.value, 300)}
                      alt={dt.label}
                      fill
                      sizes="150px"
                      className={`object-cover transition-all duration-300 ${
                        active ? 'brightness-75' : 'brightness-45 group-hover:brightness-60'
                      }`}
                    />
                    {active && <div className="absolute inset-0 bg-cyan-500/10" />}
                  </div>
                  <div className={`px-2 py-1.5 ${active ? 'bg-cyan-500/5' : 'bg-void-800/70'}`}>
                    <span className={`text-[11px] font-semibold leading-tight block ${active ? 'text-cyan-400' : 'text-void-400'}`}>
                       {dt.label}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Slide count */}
        <div className="glass rounded-2xl p-4 border border-white/8">
          <div className="flex justify-between items-center mb-3">
            <p className="text-void-300 text-xs font-semibold uppercase tracking-widest">Slides</p>
            <span className="text-cyan-400 font-black text-xl">{slides}</span>
          </div>
          <div className="relative h-1.5 bg-void-700 rounded-full overflow-hidden">
            <div
              className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all"
              style={{ width: `${((slides - 5) / 20) * 100}%` }}
            />
            <input
              type="range" min={5} max={25} value={slides}
              onChange={(e) => setSlides(Number(e.target.value))}
              className="absolute inset-0 w-full opacity-0 cursor-pointer"
            />
          </div>
          <div className="flex justify-between text-[10px] text-void-600 mt-1.5">
            <span>5</span><span>25</span>
          </div>
        </div>

        {/* Theme picker */}
        <div className="glass rounded-2xl p-4 border border-white/8">
          <p className="text-void-300 text-xs font-semibold uppercase tracking-widest mb-3">Brand Theme</p>
          <div className="flex flex-wrap gap-2 mb-2">
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
          <p className="text-void-500 text-[11px]">
            <span className="text-cyan-400 font-medium">{THEMES.find(t => t.value === theme)?.label}</span>
          </p>
        </div>

        {/* Options */}
        <div className="glass rounded-2xl p-4 border border-white/8">
          <p className="text-void-300 text-xs font-semibold uppercase tracking-widest mb-3">Include</p>
          <div className="space-y-2.5">
            {[
              { label: 'Charts & Data Viz', value: includeCharts, set: setIncludeCharts },
              { label: 'Diagrams & Frameworks', value: includeDiagrams, set: setIncludeDiagrams },
              { label: 'Images', value: includeImages, set: setIncludeImages },
            ].map((opt) => (
              <button
                key={opt.label}
                onClick={() => opt.set(!opt.value)}
                className="w-full flex items-center justify-between group"
              >
                <span className={`text-xs font-medium transition-colors ${opt.value ? 'text-void-200' : 'text-void-500'}`}>
                  {opt.label}
                </span>
                <div className={`relative w-9 h-5 rounded-full border transition-all duration-200 ${
                  opt.value ? 'bg-cyan-500 border-cyan-500' : 'bg-void-700 border-white/10'
                }`}>
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200 ${
                    opt.value ? 'left-4' : 'left-0.5'
                  }`} />
                </div>
              </button>
            ))}
          </div>
          </div>
        </div>
      </motion.div>

      {/* Floating Trigger Button when closed */}
      {!sidebarOpen && (
        <button 
          onClick={() => setSidebarOpen(true)}
          className="fixed left-0 top-1/3 z-30 p-2 rounded-r-xl border border-white/8 bg-void-850 text-cyan-400 shadow-glow-sm hover:bg-void-700 transition-all flex items-center justify-center"
          title="Expand Options"
        >
           <ChevronRight className="w-5 h-5" />
        </button>
      )}

      {/* ── RIGHT PANEL: Prompt + Submit ── */}
      <div className="flex justify-center flex-1 p-6 lg:p-12 w-full">
        <div className="w-full max-w-none space-y-5">

        {/* Active deck label */}
        <AnimatePresence mode="wait">
          <motion.div
            key={deckType}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.25 }}
            className="flex items-center gap-2"
          >
            <div className="relative w-8 h-8 rounded-lg overflow-hidden border border-white/10 flex-shrink-0">
              <Image src={deckImageSrc(deckType, 80)} alt={selectedDeck?.label || ''} fill className="object-cover brightness-75" />
            </div>
            <p className="text-white font-bold text-base">{selectedDeck?.label}</p>
            <span className="text-void-500 text-xs">— describe what you need</span>
          </motion.div>
        </AnimatePresence>

        {/* Prompt textarea */}
        <div className="glass rounded-2xl border border-white/8 overflow-hidden focus-within:border-brand-purple/50 focus-within:shadow-glow-sm transition-all duration-200">
          <div className="flex items-start gap-3 p-5">
            <Sparkles className="w-4 h-4 text-brand-violet mt-0.5 flex-shrink-0" />
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => { setPrompt(e.target.value); autoResize() }}
              placeholder={`Describe your ${selectedDeck?.label || 'presentation'} in detail — audience, industry, key message, tone, and any specific data or frameworks to include...`}
              className="flex-1 bg-transparent outline-none text-void-100 placeholder-void-600 text-sm leading-relaxed resize-none w-full"
              style={{ minHeight: '160px' }}
            />
          </div>
          <div className="flex justify-end px-5 pb-3">
            <span className={`text-xs tabular-nums ${prompt.length > 800 ? 'text-amber-400' : 'text-void-600'}`}>
              {prompt.length} / 1000
            </span>
          </div>
        </div>

        {/* Deck-specific prompt suggestions — horizontal scroll */}
        <div>
          <AnimatePresence mode="wait">
            <motion.p
              key={`label-${deckType}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-void-500 text-[11px] font-semibold uppercase tracking-widest mb-2.5"
            >
              Suggested prompts for {selectedDeck?.label}
            </motion.p>
          </AnimatePresence>

          <div
            ref={promptsRef}
            className="flex gap-3 overflow-x-auto pb-2"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            <AnimatePresence mode="wait">
              {deckPrompts.map((p, i) => (
                <motion.button
                  key={`${deckType}-${i}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.25, delay: i * 0.05 }}
                  onClick={() => handlePromptChip(p, i)}
                  className={`flex-shrink-0 text-left rounded-xl border p-3.5 transition-all duration-200 group ${
                    selectedPromptIdx === i
                      ? 'border-brand-purple bg-brand-purple/10 shadow-glow-sm'
                      : 'border-white/8 glass hover:border-white/20 hover:bg-white/3'
                  }`}
                  style={{ width: '260px' }}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className={`text-[10px] font-bold uppercase tracking-widest ${
                      selectedPromptIdx === i ? 'text-brand-violet' : 'text-void-500'
                    }`}>
                      Prompt {i + 1}
                    </span>
                    <ChevronRight className={`w-3 h-3 flex-shrink-0 mt-0.5 transition-all duration-200 ${
                      selectedPromptIdx === i ? 'text-brand-violet' : 'text-void-600 group-hover:text-void-400'
                    }`} />
                  </div>
                  <p className={`text-xs leading-relaxed line-clamp-4 ${
                    selectedPromptIdx === i ? 'text-void-200' : 'text-void-400'
                  }`}>
                    {p}
                  </p>
                </motion.button>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* Submit */}
        <Button
          variant="gradient"
          size="lg"
          fullWidth
          loading={loading}
          onClick={handleSubmit}
          disabled={!prompt.trim()}
        >
          <Sparkles className="w-5 h-5" />
          <span>Generate {selectedDeck?.label || 'Presentation'}</span>
        </Button>
      </div>
     </div>
    </div>
  )
}
