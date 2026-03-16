'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import Button from '@/components/ui/Button'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)

    // Dynamic import to avoid SSR issues if any
    import('@/lib/supabase').then(({ supabase }) => {
      supabase.auth.getSession().then(({ data }) => {
        setUser(data.session?.user || null)
      })
      const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(session?.user || null)
      })
    })

    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = async () => {
    const { supabase } = await import('@/lib/supabase')
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/generate', label: 'Generate' },
    { href: '/gallery', label: 'Gallery' },
  ]

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'backdrop-blur-xl bg-void-900/80 border-b border-white/5 shadow-glass'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-2xl font-black gradient-text tracking-tight group-hover:opacity-90 transition-opacity">
            ✦ Deck-star
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-void-300 hover:text-white text-sm font-medium transition-colors duration-200 hover:text-brand-violet"
            >
              {link.label}
            </Link>
          ))}
          
          {user ? (
            <button
              onClick={handleLogout}
              className="text-void-300 hover:text-white text-sm font-medium transition-colors duration-200 hover:text-red-400"
            >
              Logout
            </button>
          ) : (
            <Link
              href="/login"
              className="text-void-300 hover:text-white text-sm font-medium transition-colors duration-200 hover:text-brand-violet"
            >
              Login
            </Link>
          )}
        </div>

        {/* CTA */}
        <div className="hidden md:block">
          <Link href="/generate">
            <Button variant="gradient" size="sm">
              <span>Start Generating</span>
            </Button>
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-void-300 hover:text-white transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden backdrop-blur-xl bg-void-800/95 border-b border-white/5"
          >
            <div className="px-6 py-4 flex flex-col gap-4">
              {navLinks.map((link: any) => (
                <Link
                  key={link.label}
                  href={link.href}
                  className="text-void-200 hover:text-white py-2 text-sm font-medium border-b border-white/5 last:border-0 transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              
              {user ? (
                <button
                  onClick={() => { handleLogout(); setMobileOpen(false); }}
                  className="text-left text-void-200 hover:text-red-400 py-2 text-sm font-medium border-b border-white/5 last:border-0 transition-colors"
                >
                  Logout
                </button>
              ) : (
                <Link
                  href="/login"
                  className="text-void-200 hover:text-white py-2 text-sm font-medium border-b border-white/5 last:border-0 transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  Login
                </Link>
              )}
              <Link href="/generate" onClick={() => setMobileOpen(false)}>
                <Button variant="gradient" size="sm" fullWidth>
                  <span>Start Generating</span>
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
