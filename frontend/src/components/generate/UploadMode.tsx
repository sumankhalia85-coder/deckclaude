'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, FileSpreadsheet, X, Sparkles } from 'lucide-react'
import { THEMES } from '@/lib/constants'
import Button from '@/components/ui/Button'
import GlassCard from '@/components/ui/GlassCard'

const ACCEPTED_TYPES: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'text/csv': ['.csv'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/json': ['.json'],
}

function getFileIcon(type: string) {
  if (type.includes('pdf')) return <FileText className="w-8 h-8 text-red-400" />
  if (type.includes('spreadsheet') || type.includes('excel') || type.includes('csv'))
    return <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
  return <FileText className="w-8 h-8 text-brand-violet" />
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

interface UploadModeProps {
  onSubmit: (data: { file: File; prompt: string; theme: string; slides: number }) => void
  loading?: boolean
}

export default function UploadMode({ onSubmit, loading = false }: UploadModeProps) {
  const [file, setFile] = useState<File | null>(null)
  const [prompt, setPrompt] = useState('')
  const [theme, setTheme] = useState('mckinsey')
  const [slides, setSlides] = useState(10)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  })

  const handleSubmit = () => {
    if (!file) return
    onSubmit({ file, prompt, theme, slides })
  }

  return (
    <div className="space-y-8">
      {/* Drop zone */}
      <GlassCard padding="none">
        {!file ? (
          <div
            {...getRootProps()}
            className={`p-12 flex flex-col items-center justify-center gap-4 cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 ${
              isDragActive
                ? 'border-brand-purple bg-brand-purple/10 shadow-glow-sm'
                : 'border-white/10 hover:border-brand-purple/40 hover:bg-white/3'
            }`}
          >
            <input {...getInputProps()} />
            <div
              className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                isDragActive ? 'bg-brand-purple/30' : 'bg-void-700/50'
              }`}
            >
              <Upload className={`w-8 h-8 transition-colors ${isDragActive ? 'text-brand-violet' : 'text-void-400'}`} />
            </div>
            <div className="text-center">
              <p className="text-void-200 font-semibold mb-1">
                {isDragActive ? 'Drop it here!' : 'Drop files here or click to browse'}
              </p>
              <p className="text-void-500 text-sm">Supports PDF, CSV, Excel (.xls/.xlsx), JSON</p>
              <p className="text-void-600 text-xs mt-1">Max 50 MB</p>
            </div>
          </div>
        ) : (
          <div className="p-6 flex items-center gap-4">
            <div className="w-16 h-16 rounded-xl bg-void-700/50 flex items-center justify-center flex-shrink-0">
              {getFileIcon(file.type)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-void-100 font-semibold truncate">{file.name}</p>
              <p className="text-void-400 text-sm">{formatSize(file.size)}</p>
              <p className="text-void-500 text-xs">{file.type || 'Unknown type'}</p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="w-8 h-8 rounded-full bg-void-700 hover:bg-red-500/20 hover:border-red-500/40 border border-white/10 flex items-center justify-center transition-colors flex-shrink-0"
            >
              <X className="w-4 h-4 text-void-400" />
            </button>
          </div>
        )}
      </GlassCard>

      {/* Prompt */}
      <GlassCard padding="md">
        <p className="text-void-300 text-sm font-semibold mb-3">What would you like to do with this data?</p>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. 'Summarize this financial report into an executive board presentation' or 'Turn this CSV data into a market analysis deck with charts'"
          rows={3}
          className="w-full bg-void-800/60 border border-white/10 rounded-xl px-4 py-3 text-void-100 placeholder-void-500 text-sm outline-none focus:border-brand-purple/60 transition-all duration-200 resize-none"
        />
      </GlassCard>

      {/* Slide count */}
      <GlassCard padding="md">
        <div className="flex justify-between items-center mb-3">
          <p className="text-void-300 text-sm font-semibold">Slide Count</p>
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
          <span>5 slides</span>
          <span>25 slides</span>
        </div>
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

      {/* Submit */}
      <Button
        variant="gradient"
        size="lg"
        fullWidth
        loading={loading}
        onClick={handleSubmit}
        disabled={!file}
      >
        <Sparkles className="w-5 h-5" />
        <span>Generate from File ✦</span>
      </Button>
    </div>
  )
}
