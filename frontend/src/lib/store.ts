import { create } from 'zustand'

interface GenerationJob {
  jobId: string
  status: 'pending' | 'processing' | 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  currentAgent: string
  outputPath?: string
  downloadUrl?: string
  error?: string
  createdAt: Date
  prompt: string
  theme: string
  deckType: string
}

interface AppStore {
  jobs: GenerationJob[]
  activeJobId: string | null
  addJob: (job: GenerationJob) => void
  updateJob: (jobId: string, updates: Partial<GenerationJob>) => void
  setActiveJob: (jobId: string | null) => void
  getJob: (jobId: string) => GenerationJob | undefined
}

export const useAppStore = create<AppStore>((set, get) => ({
  jobs: [],
  activeJobId: null,
  addJob: (job) => set((s) => ({ jobs: [job, ...s.jobs] })),
  updateJob: (jobId, updates) =>
    set((s) => ({ jobs: s.jobs.map((j) => (j.jobId === jobId ? { ...j, ...updates } : j)) })),
  setActiveJob: (jobId) => set({ activeJobId: jobId }),
  getJob: (jobId) => get().jobs.find((j) => j.jobId === jobId),
}))

export type { GenerationJob }
