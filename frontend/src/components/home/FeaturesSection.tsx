'use client'

import { motion } from 'framer-motion'
import { Brain, BarChart2, Palette, BarChart, Layers, Shield } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'

const FEATURES = [
  {
    icon: Brain,
    title: '12 Specialized Agents',
    description:
      'A full pipeline of AI agents — from intent detection to quality critique — each mastering a specific layer of deck creation.',
    color: 'from-brand-purple to-brand-violet',
    glow: 'rgba(124,58,237,0.3)',
  },
  {
    icon: BarChart2,
    title: 'Consulting Frameworks',
    description:
      'Automatically applies SCQA, Pyramid Principle, MECE logic and Minto-style storytelling to every presentation.',
    color: 'from-brand-blue to-brand-electric',
    glow: 'rgba(37,99,235,0.3)',
  },
  {
    icon: Palette,
    title: '10 Brand Themes',
    description:
      'McKinsey, BCG, Bain, EY, Deloitte and more — pixel-accurate design templates trusted by top-tier consultants.',
    color: 'from-pink-600 to-brand-violet',
    glow: 'rgba(168,85,247,0.3)',
  },
  {
    icon: BarChart,
    title: 'Smart Data Charts',
    description:
      '7 chart types — bar, line, waterfall, scatter, bubble, pie, and combo — auto-selected for your data.',
    color: 'from-cyan-600 to-brand-blue',
    glow: 'rgba(6,182,212,0.3)',
  },
  {
    icon: Layers,
    title: '3 Input Modes',
    description:
      'Describe via natural language prompt, fill a structured form, or upload a PDF/CSV/Excel and let AI do the rest.',
    color: 'from-emerald-600 to-teal-500',
    glow: 'rgba(16,185,129,0.3)',
  },
  {
    icon: Shield,
    title: 'Quality Critic Agent',
    description:
      'A dedicated critic agent reviews every slide, flags weak narratives, and auto-revises before final delivery.',
    color: 'from-amber-600 to-orange-500',
    glow: 'rgba(245,158,11,0.3)',
  },
]

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
}

const cardVariants = {
  hidden: { opacity: 0, y: 32 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] } },
}

export default function FeaturesSection() {
  return (
    <section className="py-24 px-6 relative overflow-hidden">
      {/* Background accent */}
      <div className="absolute inset-0 bg-gradient-to-b from-void-900 via-void-800/30 to-void-900 pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Section heading */}
        <div className="text-center mb-16">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-brand-violet text-sm font-semibold uppercase tracking-widest mb-3"
          >
            Why Deck-star
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="text-4xl md:text-5xl font-black text-white mb-4"
          >
            Intelligence Built For{' '}
            <span className="gradient-text">Consulting</span>
          </motion.h2>
          {/* Gradient accent line */}
          <motion.div
            initial={{ scaleX: 0 }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mx-auto h-1 w-24 rounded-full bg-gradient-to-r from-brand-purple to-brand-blue"
          />
        </div>

        {/* Feature grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {FEATURES.map((feature) => {
            const Icon = feature.icon
            return (
              <motion.div key={feature.title} variants={cardVariants}>
                <GlassCard
                  hover
                  className="h-full group"
                  style={{ ['--glow-color' as string]: feature.glow }}
                >
                  {/* Icon */}
                  <div
                    className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} mb-5 shadow-lg group-hover:scale-110 transition-transform duration-200`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>

                  <h3 className="text-white font-bold text-lg mb-3 group-hover:text-brand-violet transition-colors duration-200">
                    {feature.title}
                  </h3>
                  <p className="text-void-400 text-sm leading-relaxed">{feature.description}</p>
                </GlassCard>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}
