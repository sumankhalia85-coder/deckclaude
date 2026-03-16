'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorText, setErrorText] = useState('')

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorText('')

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error
      router.push('/generate')
    } catch (err: any) {
      setErrorText(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorText('')

    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/login`,
        },
      })

      if (error) throw error
      setErrorText('Check your email for the confirmation link!')
    } catch (err: any) {
      setErrorText(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-slate-900">
      {/* Background Image holding app Theme vibes */}
      <div className="absolute inset-0 bg-cover bg-center opacity-60" 
           style={{ backgroundImage: "url('https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80')" }} />
      <div className="absolute inset-0 bg-gradient-to-tr from-purple-900/40 via-transparent to-pink-900/20 backdrop-blur-sm" />

      <motion.div 
        className="w-full max-w-md bg-white p-8 rounded-2xl shadow-2xl relative z-10 border border-white/10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Logo Heading */}
        <div className="flex flex-col mb-8 text-center">
          <h2 className="text-2xl font-bold font-sans tracking-wide text-slate-800 flex items-center gap-2 justify-center">
            <Zap className="h-6 w-6 text-purple-600 fill-purple-200" /> DECKSTAR
          </h2>
        </div>

        <h3 className="text-2xl font-extrabold text-slate-900 mb-1 text-center">Get Started</h3>
        <p className="text-slate-500 mb-6 font-medium text-sm text-center">Sign in or sign up with email.</p>

        {errorText && (
          <div className={`mb-4 p-3 rounded-lg ${errorText.includes('confirm') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'} text-sm font-medium text-center`}>
            {errorText}
          </div>
        )}

        <form className="flex flex-col gap-4" onSubmit={handleSignIn}>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-600">Email Address</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com" 
              className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:border-purple-500 text-slate-800 font-medium text-sm transition-all"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-600">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••" 
              className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:border-purple-500 text-slate-800 font-medium text-sm transition-all"
            />
          </div>

          <div className="flex flex-col gap-2 mt-2">
            <button 
              type="submit" 
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl shadow-md hover:scale-[1.01] transition-all text-sm disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Sign in'}
            </button>
            <button 
              type="button" 
              onClick={handleSignUp}
              disabled={loading}
              className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-xl transition-all text-sm disabled:opacity-50"
            >
              Sign up
            </button>
          </div>
        </form>

        <p className="text-xs text-center text-slate-400 mt-6">
          Passwords must be at least 6 characters for Supabase.
        </p>
      </motion.div>
    </main>
  )
}
