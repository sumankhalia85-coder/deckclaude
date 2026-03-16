'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check } from 'lucide-react'

// Purple → Indigo spectrum: lighter → darker as agents progress
const AGENTS = [
  { id: 'intent',    label: 'Intent',    role: 'The Analyst',      hex: '#C084FC',
    acts: ['Reading between the lines', 'Mapping narrative territory', 'Classifying deck intent', 'Profiling your audience'] },
  { id: 'blueprint', label: 'Blueprint', role: 'The Architect',    hex: '#A855F7',
    acts: ['Drawing the slide skeleton', 'Architecting the story arc', 'Laying structural foundations'] },
  { id: 'research',  label: 'Research',  role: 'The Scholar',      hex: '#9333EA',
    acts: ['Mining domain intelligence', 'Cross-referencing market data', 'Excavating statistical evidence'] },
  { id: 'insights',  label: 'Insights',  role: 'The Strategist',   hex: '#7C3AED',
    acts: ['Crafting the SCQA narrative', 'Distilling strategic insights', 'Writing executive-grade copy'] },
  { id: 'design',    label: 'Design',    role: 'The Choreographer',hex: '#6D28D9',
    acts: ['Choreographing visual flow', 'Composing visual hierarchy', 'Selecting layout archetypes'] },
  { id: 'charts',    label: 'Charts',    role: 'The Data Scientist',hex: '#4F46E5',
    acts: ['Plotting the data story', 'Rendering waterfall charts', 'Computing trend lines'] },
  { id: 'images',    label: 'Images',    role: 'The Curator',      hex: '#4338CA',
    acts: ['Scouting professional imagery', 'Curating visual evidence', 'Sourcing abstract visuals'] },
  { id: 'builder',   label: 'Builder',   role: 'The Engineer',     hex: '#3730A3',
    acts: ['Assembling slides in PowerPoint', 'Applying brand theme colours', 'Composing the final deck'] },
  { id: 'critic',    label: 'Critic',    role: 'The Editor',       hex: '#312E81',
    acts: ['Enforcing quality standards', 'Stress-testing the headlines', 'Scoring slide quality'] },
]

// Organic blob keyframes for continuous liquid morphing
const BLOBS = [
  '60% 40% 30% 70% / 60% 30% 70% 40%',
  '40% 60% 70% 30% / 50% 60% 30% 60%',
  '30% 70% 40% 60% / 40% 30% 60% 70%',
  '70% 30% 60% 40% / 30% 70% 40% 60%',
  '50% 50% 30% 70% / 60% 40% 50% 60%',
  '45% 55% 65% 35% / 35% 65% 45% 55%',
  '55% 45% 35% 65% / 65% 35% 55% 45%',
]

function rgba(hex: string, a: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${a})`
}

function lighten(hex: string): string {
  const r = Math.min(255, parseInt(hex.slice(1, 3), 16) + 55)
  const g = Math.min(255, parseInt(hex.slice(3, 5), 16) + 45)
  const b = Math.min(255, parseInt(hex.slice(5, 7), 16) + 35)
  return `rgb(${r},${g},${b})`
}

// ── Cycling activity text ─────────────────────────────────────────────────────
function ActivityTicker({ agent }: { agent: typeof AGENTS[0] }) {
  const [idx, setIdx] = useState(0)
  useEffect(() => {
    setIdx(0)
    const t = setInterval(() => setIdx(i => (i + 1) % agent.acts.length), 2400)
    return () => clearInterval(t)
  }, [agent.id, agent.acts.length])

  return (
    <div style={{ height: '1.25rem', overflow: 'hidden' }}>
      <AnimatePresence mode="wait">
        <motion.span
          key={`${agent.id}-${idx}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.4)', fontWeight: 400, letterSpacing: '0.01em' }}
        >
          {agent.acts[idx]}
        </motion.span>
      </AnimatePresence>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
interface GenerationProgressProps {
  progress: number
  currentAgent: string
  logs: string[]
}

export default function GenerationProgress({ progress, currentAgent, logs }: GenerationProgressProps) {
  const [blobIdx, setBlobIdx] = useState(0)

  // Resolve active agent
  const matchedIdx = AGENTS.findIndex(
    a => currentAgent && (a.id === currentAgent || a.label.toLowerCase() === currentAgent.toLowerCase())
  )
  const progressIdx = Math.min(Math.floor((progress / 100) * AGENTS.length), AGENTS.length - 1)
  const activeIdx   = matchedIdx >= 0 ? matchedIdx : progressIdx
  const agent       = AGENTS[activeIdx]
  const doneCount   = activeIdx

  // Blob morphing loop
  useEffect(() => {
    const t = setInterval(() => setBlobIdx(i => (i + 1) % BLOBS.length), 720)
    return () => clearInterval(t)
  }, [])

  const trackProgress = progress > 0 ? progress : (activeIdx / (AGENTS.length - 1)) * 100

  return (
    <div
      style={{
        maxWidth: 660,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 44,
        position: 'relative',
      }}
    >
      {/* ── Full-page ambient glow ── */}
      <AnimatePresence>
        <motion.div
          key={agent.id + '-ambient'}
          style={{
            position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
            background: `radial-gradient(ellipse 55% 45% at 50% 30%, ${rgba(agent.hex, 0.09)}, transparent 70%)`,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.4 }}
        />
      </AnimatePresence>

      {/* ── Central liquid orb zone ── */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24 }}>

        {/* Orb + rings container */}
        <div style={{ position: 'relative', width: 220, height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

          {/* Outer slow pulse ring */}
          <motion.div
            style={{
              position: 'absolute', width: 220, height: 220, borderRadius: '50%',
              border: `1px solid ${rgba(agent.hex, 0.1)}`,
            }}
            animate={{ scale: [1, 1.5], opacity: [0.7, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeOut' }}
          />

          {/* Middle pulse ring */}
          <motion.div
            style={{
              position: 'absolute', width: 170, height: 170, borderRadius: '50%',
              border: `1px solid ${rgba(agent.hex, 0.18)}`,
            }}
            animate={{ scale: [1, 1.45], opacity: [0.9, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeOut', delay: 0.9 }}
          />

          {/* Inner pulse ring */}
          <motion.div
            style={{
              position: 'absolute', width: 130, height: 130, borderRadius: '50%',
              border: `1px solid ${rgba(agent.hex, 0.28)}`,
            }}
            animate={{ scale: [1, 1.5], opacity: [0.8, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeOut', delay: 1.8 }}
          />

          {/* Diffuse radial glow behind blob */}
          <AnimatePresence>
            <motion.div
              key={agent.id + '-glow'}
              style={{
                position: 'absolute', width: 150, height: 150, borderRadius: '50%',
                background: `radial-gradient(circle, ${rgba(agent.hex, 0.55)} 0%, ${rgba(agent.hex, 0)} 70%)`,
              }}
              animate={{ scale: [0.9, 1.08, 0.9] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              initial={{ opacity: 0 }}
              exit={{ opacity: 0 }}
            />
          </AnimatePresence>

          {/* ── The liquid morphing blob ── */}
          <AnimatePresence mode="wait">
            <motion.div
              key={agent.id + '-blob'}
              initial={{ scale: 0.75, opacity: 0 }}
              animate={{ scale: [1, 1.06, 1], opacity: 1 }}
              exit={{ scale: 0.85, opacity: 0 }}
              transition={{ scale: { duration: 2.8, repeat: Infinity, ease: 'easeInOut' }, opacity: { duration: 0.45 } }}
              style={{
                width: 124, height: 124,
                borderRadius: BLOBS[blobIdx],
                background: `radial-gradient(circle at 32% 28%, ${lighten(agent.hex)}, ${agent.hex} 65%, ${rgba(agent.hex, 0.85)} 100%)`,
                boxShadow: [
                  `0 0 50px ${rgba(agent.hex, 0.7)}`,
                  `0 0 100px ${rgba(agent.hex, 0.3)}`,
                  `inset 0 0 35px rgba(255,255,255,0.12)`,
                ].join(', '),
                transition: 'border-radius 0.68s cubic-bezier(0.45,0.05,0.55,0.95), background 0.8s ease',
                position: 'relative', overflow: 'hidden',
              }}
            >
              {/* Top-left shimmer */}
              <motion.div
                style={{
                  position: 'absolute', inset: 0, borderRadius: 'inherit',
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.26) 0%, transparent 48%)',
                }}
                animate={{ opacity: [0.55, 1, 0.55] }}
                transition={{ duration: 2.2, repeat: Infinity }}
              />
              {/* Inner breathing dot */}
              <motion.div
                style={{
                  position: 'absolute', width: 28, height: 28, borderRadius: '50%',
                  background: 'rgba(255,255,255,0.2)',
                  top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
                }}
                animate={{ scale: [1, 2.2], opacity: [0.5, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
              />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* ── Agent identity text ── */}
        <AnimatePresence mode="wait">
          <motion.div
            key={agent.id + '-text'}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.35 }}
            style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 5 }}
          >
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.2em',
              textTransform: 'uppercase', color: 'rgba(255,255,255,0.28)',
            }}>
              {agent.role}
            </span>
            <h3 style={{
              fontSize: 24, fontWeight: 800, margin: 0,
              color: agent.hex,
              letterSpacing: '0.02em',
              textShadow: `0 0 30px ${rgba(agent.hex, 0.4)}`,
            }}>
              {agent.label}
            </h3>
            <ActivityTicker agent={agent} />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ── Progress track + agent nodes ── */}
      <div style={{ width: '100%', zIndex: 1 }}>

        {/* Thin fill bar */}
        <div style={{
          height: 1, background: 'rgba(255,255,255,0.07)',
          borderRadius: 99, overflow: 'hidden', marginBottom: 22,
        }}>
          <motion.div
            style={{
              height: '100%', borderRadius: 99,
              background: `linear-gradient(90deg, #C084FC 0%, ${agent.hex} 100%)`,
            }}
            animate={{ width: `${Math.max(trackProgress, 4)}%` }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
          />
        </div>

        {/* Agent dot nodes */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 0 }}>
          {AGENTS.map((a, i) => {
            const state: 'idle' | 'active' | 'done' = i < activeIdx ? 'done' : i === activeIdx ? 'active' : 'idle'
            return (
              <div key={a.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1 }}>
                {/* Node */}
                <div style={{ position: 'relative', width: 10, height: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {state === 'active' && (
                    <motion.div
                      style={{
                        position: 'absolute', width: 18, height: 18, borderRadius: '50%',
                        background: rgba(a.hex, 0.35),
                      }}
                      animate={{ scale: [1, 1.9], opacity: [0.7, 0] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
                    />
                  )}
                  <div style={{
                    width: 9, height: 9, borderRadius: '50%',
                    background:
                      state === 'done'   ? a.hex :
                      state === 'active' ? a.hex :
                                           'rgba(255,255,255,0.09)',
                    boxShadow: state === 'active' ? `0 0 12px ${rgba(a.hex, 0.9)}` : 'none',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'background 0.5s ease, box-shadow 0.5s ease',
                  }}>
                    {state === 'done' && (
                      <Check style={{ width: 5, height: 5, color: 'white', strokeWidth: 3.5 }} />
                    )}
                  </div>
                </div>

                {/* Label */}
                <span style={{
                  fontSize: 8.5,
                  fontWeight: state === 'idle' ? 400 : 700,
                  letterSpacing: '0.07em',
                  textTransform: 'uppercase',
                  color:
                    state === 'active' ? a.hex :
                    state === 'done'   ? 'rgba(255,255,255,0.32)' :
                                         'rgba(255,255,255,0.1)',
                  transition: 'color 0.4s ease',
                  textAlign: 'center',
                }}>
                  {a.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Meta row ── */}
      <div style={{
        width: '100%', zIndex: 1,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'rgba(255,255,255,0.18)' }}>
          {doneCount} of {AGENTS.length} agents complete
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <motion.div
            style={{ width: 5, height: 5, borderRadius: '50%', background: agent.hex }}
            animate={{ opacity: [1, 0.15, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'rgba(255,255,255,0.18)' }}>live</span>
        </div>
      </div>

      {/* ── Minimal log ── */}
      {logs.length > 0 && (
        <div style={{ width: '100%', zIndex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {logs.slice(-4).map((log, i, arr) => {
            const isDone   = log.includes('✓')
            const isLatest = i === arr.length - 1
            const clean    = log.replace('✓ ', '').replace('→ ', '')
            return (
              <motion.div
                key={log + i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: isLatest ? 0.9 : isDone ? 0.5 : 0.25 }}
                transition={{ duration: 0.3 }}
                style={{ display: 'flex', gap: 10, fontFamily: 'monospace', fontSize: 11 }}
              >
                <span style={{ color: isDone ? '#4ADE80' : rgba(agent.hex, 0.6), flexShrink: 0 }}>
                  {isDone ? '✓' : '›'}
                </span>
                <span style={{ color: isDone ? 'rgba(74,222,128,0.7)' : isLatest ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.2)' }}>
                  {clean}
                </span>
                {isLatest && !isDone && (
                  <motion.span
                    style={{ color: rgba(agent.hex, 0.7) }}
                    animate={{ opacity: [1, 0, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    _
                  </motion.span>
                )}
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
