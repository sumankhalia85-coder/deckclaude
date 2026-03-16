import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export { API_BASE }

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export interface GenerateRequest {
  prompt: string
  theme?: string
  slides?: number
  deck_type?: string
  include_charts?: boolean
  include_diagrams?: boolean
  include_images?: boolean
  form_data?: Record<string, unknown>
}

export interface GenerateResponse {
  job_id: string
  status: string
  message: string
}

// Matches the backend JobStatus Pydantic model exactly
export interface JobStatus {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress_pct: number | null      // backend field name
  message: string | null           // backend uses message, not current_agent
  output_filename: string | null
  download_url: string | null      // relative path e.g. /download/file.pptx
  quality_score: number | null
  error: string | null
  created_at: number
  completed_at: number | null
  total_time: number | null
}

export const generateDeck = async (data: GenerateRequest): Promise<GenerateResponse> => {
  const res = await api.post('/generate', data)
  return res.data
}

export const generateDeckWithFile = async (file: File, prompt: string, theme: string): Promise<GenerateResponse> => {
  const form = new FormData()
  form.append('file', file)
  form.append('prompt', prompt)
  form.append('theme', theme)
  const res = await api.post('/generate/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const res = await api.get(`/status/${jobId}`)
  return res.data
}

// Always returns a full absolute URL safe to use with window.open / <a href>
export const getDownloadUrl = (relativeOrFilename: string): string => {
  if (relativeOrFilename.startsWith('http')) return relativeOrFilename
  if (relativeOrFilename.startsWith('/')) return `${API_BASE}${relativeOrFilename}`
  return `${API_BASE}/download/${relativeOrFilename}`
}

export const checkHealth = async (): Promise<boolean> => {
  try {
    await api.get('/health')
    return true
  } catch {
    return false
  }
}
