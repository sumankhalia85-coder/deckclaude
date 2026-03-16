'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Download, CheckCircle2 } from 'lucide-react'
import { AGENTS } from '@/lib/constants'

const STEPS = [
  {
    number: '01',
    icon: MessageSquare,
    title: 'Describe Your Deck',
    description:
      'Type a natural language prompt, fill out our structured form, or upload a PDF/CSV. We handle any input format.',
    color: 'from-brand-purple to-brand-violet',
  },
  {
    number: '02',
    icon: () => (
      <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
      </svg>
    ),
    title: '12 Agents Get to Work',
    description:
      'A pipeline of specialized AI agents fire in sequence — structuring, researching, designing, charting, and critiquing your deck.',
    color: 'from-brand-blue to-brand-electric',
  },
  {
    number: '03',
    icon: Download,
    title: 'Download Your Deck',
    description:
      'Receive a polished, consulting-grade .pptx file ready to present. Fully editable in PowerPoint or Google Slides.',
    color: 'from-emerald-600 to-teal-500',
  },
]

function AgentPipeline() {
  const [activeIndex, setActiveIndex] = useState(0)
  const [completed, setCompleted] = useState<number[]>([])

  const MOCK_LOGS: Record<any, string[]> = {
    intent: ['Detecting objective...', 'Classifying prompt: Strategy', 'Applied theme: BCG'],
    blueprint: ['Planning 12 slide headers...', 'Mapped slide layout to grid', 'Blueprint locked'],
    research: ['Extracting CAGR 15.4% metrics...', 'Reading datasets...', 'Insights parsed'],
    insights: ['Synthesizing core takeaways...', 'Refining narratives...', 'Storyline generated'],
    design: ['Choosing color balance...', 'Planning grid matrices...', 'Themes applied'],
    charts: ['Setting datasets array index...', 'Generating SVG vectors...', 'Bar charts locked'],
    images: ['Querying background abstract...', 'Downloading image files...', 'Images selected'],
    builder: ['Aggregating pptx stream...', 'Composing contents...', 'Rendering assets'],
    critic: ['Critiquing 12/12 content...', 'Grammar check green', 'Generation Complete.'],
  }

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => {
        const next = (prev + 1) % AGENTS.length
        if (next === 0) setCompleted([])
        else setCompleted((c) => [...c, prev].slice(-9))
        return next
      })
    }, 1800)
    return () => clearInterval(interval)
  }, [])

  const currentAgentId = AGENTS[activeIndex]?.id
  const currentLogs = MOCK_LOGS[currentAgentId] || []

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-4">
      {/* Node Grid Sidebar */}
      <div className="col-span-12 md:col-span-5 flex flex-wrap md:flex-col justify-between gap-3 relative md:border-r border-white/5 md:pr-4">
         {AGENTS.map((agent, i) => {
           const isCompleted = completed.includes(i)
           const isActive = activeIndex === i

           return (
             <div key={agent.id} className="flex items-center gap-3">
                <div className="relative">
                  {isActive && (
                    <div className="absolute inset-0 rounded-full animate-ping bg-brand-blue/30 scale-125" />
                  )}
                  <div
                    className={`w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                      isCompleted
                        ? 'bg-gradient-to-br from-brand-blue to-cyan-600 border-brand-blue shadow-glow-sm'
                        : isActive
                        ? 'bg-brand-blue/20 border-brand-blue shadow-glow-sm scale-105'
                        : 'bg-void-700/50 border-white/10'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    ) : (
                      <span className={`text-xs font-bold ${isActive ? 'text-brand-blue' : 'text-void-500'}`}>
                        {i + 1}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-start leading-tight">
                    <span className={`text-xs font-semibold ${isActive || isCompleted ? 'text-white' : 'text-void-400'}`}>
                       {agent.label}
                    </span>
                    <span className="text-[10px] text-void-500 hidden md:block">
                       {isActive ? 'Processing...' : isCompleted ? 'Completed' : 'Queued'}
                    </span>
                </div>
             </div>
           )
         })}
      </div>

      {/* Terminal View */}
      <div className="col-span-12 md:col-span-7 bg-void-950 border border-white/10 rounded-xl p-5 font-mono text-xs shadow-2xl h-[300px] flex flex-col justify-between">
         <div className="flex items-center gap-1.5 border-b border-white/5 pb-3">
             <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
             <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
             <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
             <span className="ml-2 text-void-400 text-[10px] font-sans">agent_stream_execution.sh</span>
         </div>

         <div className="flex-1 space-y-2 overflow-y-auto mt-4 text-brand-electric">
             <p className="text-void-500 opacity-60">Initializing workflow...</p>
             {completed.map((compIdx) => {
               const compAgent = AGENTS[compIdx]
               return (
                 <p key={compIdx} className="text-emerald-400">
                   <span className="text-void-600">[{compAgent.label}]</span> &gt;&gt; Done.
                 </p>
               )
             })}

             {/* Active Logs */}
             <motion.div 
               key={currentAgentId}
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               className="space-y-1"
             >
                <p className="text-brand-blue font-semibold">
                  <span className="text-void-500 font-normal">[{AGENTS[activeIndex]?.label}]</span> Running...
                </p>
                {currentLogs.map((log, lIdx) => (
                  <motion.p 
                    key={lIdx}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: lIdx * 0.3 }}
                    className="text-void-300 pl-4"
                  >
                     <span className="text-brand-blue">➜</span> {log}
                  </motion.p>
                ))}
             </motion.div>
         </div>

         <div className="text-[10px] text-void-500 border-t border-white/5 pt-2 mt-2">
            Status: Multi-agent generation executing...
         </div>
      </div>
    </div>
  )
}

export default function HowItWorksSection() {
  return (
    <section className="py-40 px-6 bg-void-800/20">
      <div className="max-w-6xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-16">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-brand-violet text-sm font-semibold uppercase tracking-widest mb-3"
          >
            How It Works
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="text-4xl md:text-5xl font-black text-white"
          >
            From Prompt to{' '}
            <span className="gradient-text">Presentation</span>
          </motion.h2>
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16 relative">
          {/* Connector lines (desktop) */}
          <div className="hidden md:block absolute top-16 left-[33%] right-[33%] h-0.5 bg-gradient-to-r from-brand-purple/40 to-brand-blue/40" />

          {STEPS.map((step, i) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.55, delay: i * 0.12 }}
                className="flex flex-col items-center text-center"
              >
                {/* Step number + icon */}
                <div className="relative mb-6">
                  <div
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center shadow-glow-sm`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-void-700 border border-white/10 flex items-center justify-center">
                    <span className="text-xs font-black gradient-text">{step.number}</span>
                  </div>
                </div>

                <h3 className="text-white font-bold text-xl mb-3">{step.title}</h3>
                <p className="text-void-400 text-sm leading-relaxed max-w-xs">{step.description}</p>
              </motion.div>
            )
          })}
        </div>

        {/* Agent pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="glass rounded-2xl p-6 border border-white/8"
        >
          <div className="text-center mb-4">
            <span className="text-void-300 text-sm font-medium">
              Live Agent Pipeline Simulation
            </span>
          </div>
          <AgentPipeline />
        </motion.div>
      </div>
    </section>
  )
}
