'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import Navbar from '@/components/layout/Navbar'
import ModeSelector from '@/components/generate/ModeSelector'
import PromptMode from '@/components/generate/PromptMode'
import FormMode from '@/components/generate/FormMode'
import UploadMode from '@/components/generate/UploadMode'
import GenerationProgress from '@/components/generate/GenerationProgress'
import ResultCard from '@/components/generate/ResultCard'
import { useAppStore } from '@/lib/store'
import { generateDeck, generateDeckWithFile, getJobStatus, getDownloadUrl } from '@/lib/api'
import type { GenerationJob } from '@/lib/store'

type Mode = 'prompt' | 'form' | 'upload'
type PageState = 'input' | 'generating' | 'complete'

// Module-level constants so startAgentTimer's closure never goes stale
const AGENT_SEQUENCE  = ['intent', 'blueprint', 'research', 'insights', 'design', 'charts', 'images', 'builder', 'critic']
const AGENT_DURATIONS = [12000, 18000, 13000, 22000, 13000, 20000, 18000, 22000, 12000] // ms per agent (~150s total)

const SIMULATED_LOGS = [
  '→ Received generation request',
  '→ [IntentAgent] Classifying prompt type...',
  '✓ [IntentAgent] Identified: Strategy Deck',
  '→ [BlueprintAgent] Designing slide structure...',
  '✓ [BlueprintAgent] 12-slide outline created',
  '→ [ResearchAgent] Extracting domain insights...',
  '✓ [ResearchAgent] 24 data points collected',
  '→ [InsightAgent] Crafting executive narratives...',
  '✓ [InsightAgent] Narratives generated',
  '→ [DesignAgent] Planning visual layout...',
  '✓ [DesignAgent] Layout templates selected',
  '→ [ChartAgent] Building data visualizations...',
  '✓ [ChartAgent] 6 charts created',
  '→ [ImageAgent] Sourcing imagery...',
  '✓ [ImageAgent] Images selected',
  '→ [BuilderAgent] Assembling final deck...',
  '✓ [BuilderAgent] 12 slides assembled',
  '→ [CriticAgent] Running quality review...',
  '✓ [CriticAgent] Quality review passed',
  '✓ Generation complete!',
]

function GeneratePageInner() {
  const searchParams = useSearchParams()
  const [mode, setMode] = useState<Mode>('prompt')
  const [pageState, setPageState] = useState<PageState>('input')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null)
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null)
  const agentTimerRef = useRef<NodeJS.Timeout | null>(null)

  const { addJob, updateJob, getJob } = useAppStore()

  const startAgentTimer = useCallback(() => {
    if (agentTimerRef.current) clearTimeout(agentTimerRef.current)
    let idx = 0
    const advance = () => {
      idx++
      if (idx < AGENT_SEQUENCE.length) {
        setCurrentAgent(AGENT_SEQUENCE[idx])
        agentTimerRef.current = setTimeout(advance, AGENT_DURATIONS[idx])
      }
    }
    setCurrentAgent(AGENT_SEQUENCE[0])
    agentTimerRef.current = setTimeout(advance, AGENT_DURATIONS[0])
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const initialPrompt = searchParams.get('prompt') || ''
  const initialType = searchParams.get('type') || ''

  // Set mode from URL
  useEffect(() => {
    const modeParam = searchParams.get('mode') as Mode | null
    if (modeParam && ['prompt', 'form', 'upload'].includes(modeParam)) {
      setMode(modeParam)
    }
  }, [searchParams])

  // Simulate progress for demo (when real API is not available)
  const simulateProgress = useCallback((jobId: string) => {
    let logIdx = 0
    let prog = 0

    const interval = setInterval(() => {
      prog = Math.min(prog + Math.random() * 8 + 3, 99)
      const agentIdx = Math.floor((prog / 100) * 9)
      const agents = ['intent', 'blueprint', 'research', 'insights', 'design', 'charts', 'images', 'builder', 'critic']

      setProgress(prog)
      setCurrentAgent(agents[Math.min(agentIdx, 8)])

      if (logIdx < SIMULATED_LOGS.length) {
        setLogs((prev) => [...prev, SIMULATED_LOGS[logIdx]])
        logIdx++
      }

      updateJob(jobId, { progress: prog, currentAgent: agents[Math.min(agentIdx, 8)] })

      if (prog >= 99) {
        clearInterval(interval)
        setTimeout(() => {
          setProgress(100)
          setLogs((prev) => [...prev, '✓ PowerPoint file ready for download!'])
          const finalJob: Partial<GenerationJob> = {
            status: 'completed',
            progress: 100,
            downloadUrl: undefined,   // simulation has no real file
          }
          updateJob(jobId, finalJob)
          const updated = getJob(jobId)
          if (updated) setActiveJob({ ...updated, ...finalJob } as GenerationJob)
          setPageState('complete')
        }, 600)
      }
    }, 700)

    setPollInterval(interval)
    return interval
  }, [updateJob, getJob])

  // Poll real API status
  const pollStatus = useCallback((jobId: string) => {
    // Start time-based visual agent progression immediately
    // (backend only returns "running" — no per-agent granularity)
    startAgentTimer()

    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId)
        const progress = status.progress_pct ?? 0
        // Only override the visual agent if backend actually provides one
        const agentFromMessage = status.message?.match(/\[(\w+Agent)\]/)?.[1]?.toLowerCase().replace('agent', '') ?? ''
        setProgress(progress)
        if (agentFromMessage) setCurrentAgent(agentFromMessage)
        // Build absolute download URL so window.open hits :8000 not :3001
        const absoluteDownloadUrl = status.download_url ? getDownloadUrl(status.download_url) : undefined
        updateJob(jobId, {
          status: status.status,
          progress,
          currentAgent: agentFromMessage,
          downloadUrl: absoluteDownloadUrl,
        })

        if (status.status === 'completed') {
          clearInterval(interval)
          if (agentTimerRef.current) clearTimeout(agentTimerRef.current)
          setProgress(100)
          setLogs((prev) => [...prev, '✓ Deck generated successfully!', `✓ Quality score: ${status.quality_score ?? 'N/A'}/10`])
          const updated = getJob(jobId)
          if (updated) setActiveJob(updated)
          setPageState('complete')
        } else if (status.status === 'failed') {
          clearInterval(interval)
          if (agentTimerRef.current) clearTimeout(agentTimerRef.current)
          toast.error(status.error || 'Generation failed. Please try again.')
          setPageState('input')
          setLoading(false)
        }
      } catch {
        // API not available — switch to simulation
        clearInterval(interval)
        if (agentTimerRef.current) clearTimeout(agentTimerRef.current)
        simulateProgress(jobId)
      }
    }, 2000)

    setPollInterval(interval)
    return interval
  }, [updateJob, getJob, simulateProgress])

  // Cleanup poll interval when it changes (NOT the agent timer — separate concerns)
  useEffect(() => {
    return () => { if (pollInterval) clearInterval(pollInterval) }
  }, [pollInterval])

  // Cleanup agent timer only on unmount
  useEffect(() => {
    return () => { if (agentTimerRef.current) clearTimeout(agentTimerRef.current) }
  }, [])

  const handleSubmit = async (data: {
    prompt: string
    theme: string
    slides?: number
    deckType?: string
    includeCharts?: boolean
    includeDiagrams?: boolean
    includeImages?: boolean
    formData?: Record<string, unknown>
    file?: File
  }) => {
    setLoading(true)
    setPageState('generating')
    setProgress(0)
    setLogs([])
    setCurrentAgent('intent')

    const tempJobId = `job_${Date.now()}`
    const newJob: GenerationJob = {
      jobId: tempJobId,
      status: 'pending',
      progress: 0,
      currentAgent: 'intent',
      createdAt: new Date(),
      prompt: data.prompt,
      theme: data.theme || 'mckinsey',
      deckType: data.deckType || 'strategy_deck',
    }
    addJob(newJob)
    setActiveJob(newJob)

    try {
      let response
      if (data.file) {
        response = await generateDeckWithFile(data.file, data.prompt, data.theme || 'mckinsey')
      } else {
        response = await generateDeck({
          prompt: data.prompt,
          theme: data.theme,
          slides: data.slides,
          deck_type: data.deckType,
          include_charts: data.includeCharts,
          include_diagrams: data.includeDiagrams,
          include_images: data.includeImages,
          form_data: data.formData,
        })
      }

      const realJobId = response.job_id || tempJobId
      updateJob(tempJobId, { jobId: realJobId })
      setActiveJob((prev) => prev ? { ...prev, jobId: realJobId } : null)
      pollStatus(realJobId)
    } catch {
      // API not reachable — use simulation
      simulateProgress(tempJobId)
    }
  }

  const handleGenerateAnother = () => {
    if (pollInterval) clearInterval(pollInterval)
    setPageState('input')
    setLoading(false)
    setProgress(0)
    setLogs([])
    setCurrentAgent('')
    setActiveJob(null)
  }

  return (
    <main className="min-h-screen bg-void-900 grid-bg">
      <Navbar />

      {/* Background orbs */}
      <div className="fixed orb w-[500px] h-[500px] bg-brand-purple/10 top-[-100px] right-[-150px] pointer-events-none" />
      <div className="fixed orb w-[400px] h-[400px] bg-brand-blue/8 bottom-[-100px] left-[-100px] pointer-events-none" />

      <div className="relative z-10 w-full pt-28 pb-20">
        {/* Page heading */}
        <AnimatePresence mode="wait">
          {pageState === 'input' && (
            <motion.div
              key="heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.45 }}
              className="text-center mb-10 max-w-4xl mx-auto px-6"
            >
              <h1 className="text-4xl md:text-5xl font-black mb-3">
                <span className="text-white">Generate Your </span>
                <span className="gradient-text">Deck</span>
              </h1>
              <p className="text-void-400 text-sm">
                Choose your input method, configure options, and let 12 AI agents build your presentation.
              </p>
            </motion.div>
          )}

          {pageState === 'generating' && (
            <motion.div
              key="gen-heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-center mb-10 max-w-4xl mx-auto px-6"
            >
              <h1 className="text-3xl md:text-4xl font-black mb-2">
                <span className="gradient-text">Agents at Work</span>
              </h1>
              <p className="text-void-400 text-sm">
                Your deck is being crafted by 12 specialized AI agents.
              </p>
            </motion.div>
          )}

          {pageState === 'complete' && (
            <motion.div
              key="complete-heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-8"
            />
          )}
        </AnimatePresence>

        {/* Mode selector (only shown on input state) */}
        <AnimatePresence>
          {pageState === 'input' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-4xl mx-auto mb-10 px-6"
            >
              <ModeSelector active={mode} onChange={setMode} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <AnimatePresence mode="wait">
          {pageState === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.4 }}
            >
              {mode === 'prompt' && (
                <PromptMode
                  initialPrompt={initialPrompt}
                  initialType={initialType}
                  onSubmit={handleSubmit}
                  loading={loading}
                />
              )}
              {mode === 'form' && (
                <FormMode onSubmit={handleSubmit} loading={loading} />
              )}
              {mode === 'upload' && (
                <UploadMode onSubmit={handleSubmit} loading={loading} />
              )}
            </motion.div>
          )}

          {pageState === 'generating' && (
            <motion.div
              key="generating"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="max-w-4xl mx-auto px-6"
            >
              <GenerationProgress
                progress={progress}
                currentAgent={currentAgent}
                logs={logs}
              />
            </motion.div>
          )}

          {pageState === 'complete' && activeJob && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="max-w-5xl mx-auto px-6"
            >
              <ResultCard job={activeJob} onGenerateAnother={handleGenerateAnother} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}

export default function GeneratePage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-void-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl font-black gradient-text animate-pulse mb-2">✦</div>
          <p className="text-void-400 text-sm">Loading...</p>
        </div>
      </main>
    }>
      <GeneratePageInner />
    </Suspense>
  )
}
